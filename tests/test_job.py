import json
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

import pytest
from nvflare.apis.fl_constant import FLContextKey
from nvflare.app_common.abstract.fl_model import ParamsType
from nvflare.client import FLModel

import common
import job


class FakeWorkspace:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir

    def get_run_dir(self, _job_id):
        return str(self.run_dir)


class FakeFLContext:
    def __init__(self, run_dir: Path):
        self.workspace = FakeWorkspace(run_dir)

    def get_job_id(self):
        return "job-123"

    def get_prop(self, key):
        if key == FLContextKey.WORKSPACE_OBJECT:
            return self.workspace
        raise KeyError(key)


class FakeJob:
    def __init__(self):
        self.to_clients_calls = []
        self.add_file_calls = []

    def to_clients(self, name):
        self.to_clients_calls.append(name)

    def add_file_to_clients(self, path, dest_dir=None):
        self.add_file_calls.append((path, dest_dir))


class FakeRecipe:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.job = FakeJob()

    def execute(self, env):
        FakeRecipe.last_env = env
        return SimpleNamespace(get_status=lambda: "ok", get_result=lambda: "/tmp/fake-result")


def test_regression_aggregator_writes_summary(tmp_path):
    aggregator = job.RegressionAggregator()
    aggregator.fl_ctx = FakeFLContext(tmp_path / "run")

    for site_name in ("site-a", "site-b"):
        stats = common.compute_local_statistics(site_name)
        aggregator.accept_model(
            FLModel(
                params={"SUCCESS": True},
                params_type=ParamsType.FULL,
                meta={"site_name": site_name, "local_stats": stats},
            )
        )

    result = aggregator.aggregate_model()

    summary_path = tmp_path / "run" / "server_results" / "hello_regression_summary.json"
    assert summary_path.exists()
    summary = json.loads(summary_path.read_text())
    assert summary["site_names"] == ["site-a", "site-b"]
    assert result.meta["total_samples"] == 56
    assert result.params["numpy_key"] == pytest.approx(summary["estimated_beta"])


def test_regression_aggregator_ignores_failed_and_empty_models(capsys):
    aggregator = job.RegressionAggregator()

    aggregator.accept_model(
        FLModel(params={"SUCCESS": False}, meta={"site_name": "site-a", "error_message": "bad site"})
    )
    aggregator.accept_model(FLModel(params={"SUCCESS": True}, meta={"site_name": "site-b"}))

    captured = capsys.readouterr()
    assert "ERROR: site site-a failed: bad site" in captured.out
    assert "WARNING: no local_stats received from site-b" in captured.out
    assert aggregator.local_stats == []


def test_main_uses_simenv_with_explicit_clients(monkeypatch):
    created = {}

    def fake_simenv(**kwargs):
        created["simenv"] = kwargs
        return ("simenv", kwargs)

    monkeypatch.setattr(job, "parse_args", lambda: Namespace(
        env="sim",
        clients=["site-a", "site-b"],
        num_rounds=1,
        startup_kit=None,
        username="admin@demo.org",
    ))
    monkeypatch.setattr(job, "NumpyFedAvgRecipe", FakeRecipe)
    monkeypatch.setattr(job, "SimEnv", fake_simenv)

    job.main()

    assert created["simenv"] == {"clients": ["site-a", "site-b"]}


def test_main_uses_pocenv_with_explicit_clients(monkeypatch):
    created = {}

    def fake_pocenv(**kwargs):
        created["pocenv"] = kwargs
        return ("pocenv", kwargs)

    monkeypatch.setattr(job, "parse_args", lambda: Namespace(
        env="poc",
        clients=["site-a", "site-b"],
        num_rounds=1,
        startup_kit=None,
        username="admin@demo.org",
    ))
    monkeypatch.setattr(job, "NumpyFedAvgRecipe", FakeRecipe)
    monkeypatch.setattr(job, "PocEnv", fake_pocenv)

    job.main()

    assert created["pocenv"] == {"clients": ["site-a", "site-b"], "username": "admin@demo.org"}


def test_main_requires_clients(monkeypatch):
    monkeypatch.setattr(job, "parse_args", lambda: Namespace(
        env="sim",
        clients=None,
        num_rounds=1,
        startup_kit=None,
        username="admin@demo.org",
    ))

    with pytest.raises(ValueError, match="`--clients` is required"):
        job.main()


def test_main_requires_startup_kit_for_prod(monkeypatch):
    monkeypatch.setattr(job, "parse_args", lambda: Namespace(
        env="prod",
        clients=["site-a"],
        num_rounds=1,
        startup_kit=None,
        username="",
    ))

    with pytest.raises(ValueError, match="--startup_kit is required for --env prod"):
        job.main()
