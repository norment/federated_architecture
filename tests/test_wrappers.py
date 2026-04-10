from pathlib import Path
from types import SimpleNamespace

import pytest

import dx_wrapper
import tsd_wrapper


def _fake_stats(site_name: str) -> bytes:
    return (
        "{"
        f"\"site_name\": \"{site_name}\", "
        "\"n\": 1, "
        "\"p\": 1, "
        "\"x_tx\": [[1.0]], "
        "\"x_ty\": [1.0], "
        "\"y_ty\": 1.0, "
        "\"feature_names\": [\"intercept\"], "
        "\"true_beta\": [0.0], "
        "\"site_config\": {}"
        "}"
    ).encode("utf-8")


def test_tsd_wrapper_requires_explicit_config(monkeypatch):
    monkeypatch.delenv("HELLO_REGRESSION_TSD_CONFIG", raising=False)

    with pytest.raises(RuntimeError, match="HELLO_REGRESSION_TSD_CONFIG is required"):
        tsd_wrapper.run_tsd_site_task("p33")


def test_dx_wrapper_requires_explicit_config(monkeypatch):
    monkeypatch.delenv("HELLO_REGRESSION_DX_CONFIG", raising=False)

    with pytest.raises(RuntimeError, match="HELLO_REGRESSION_DX_CONFIG is required"):
        dx_wrapper.run_dx_site_task("ukb-rap")


def test_tsd_wrapper_uses_explicit_config_path(monkeypatch, tmp_path):
    config_path = tmp_path / "p33.yml"
    config_path.write_text("project: p33\nusername: p33-user\n")
    monkeypatch.setenv("HELLO_REGRESSION_TSD_CONFIG", str(config_path))

    captured = {}

    def fake_from_config(*, config_path, env_prefix):
        captured["config_path"] = config_path
        captured["env_prefix"] = env_prefix
        return SimpleNamespace(remote_prefix="tsd_job", remote_python="python3")

    def fake_run_tsd_job(*, settings, spec):
        captured["settings"] = settings
        captured["spec"] = spec
        return SimpleNamespace(result_bytes=_fake_stats(spec.site_name))

    monkeypatch.setattr(tsd_wrapper.TSDSettings, "from_config", staticmethod(fake_from_config))
    monkeypatch.setattr(tsd_wrapper, "run_tsd_job", fake_run_tsd_job)

    result = tsd_wrapper.run_tsd_site_task("p33")

    assert result["site_name"] == "p33"
    assert captured["config_path"] == config_path
    assert captured["env_prefix"] == "HELLO_REGRESSION_TSD_"
    assert captured["spec"].site_name == "p33"
    assert "site_runner.py" in captured["spec"].remote_command


def test_dx_wrapper_uses_explicit_config_path(monkeypatch, tmp_path):
    config_path = tmp_path / "ukb-rap.yml"
    config_path.write_text("project: project-123\n")
    monkeypatch.setenv("HELLO_REGRESSION_DX_CONFIG", str(config_path))

    captured = {}

    def fake_from_config(*, config_path, env_prefix):
        captured["config_path"] = config_path
        captured["env_prefix"] = env_prefix
        return SimpleNamespace(remote_prefix="hello_regression", remote_python="python3")

    def fake_run_dx_job(*, settings, spec):
        captured["settings"] = settings
        captured["spec"] = spec
        return SimpleNamespace(result_bytes=_fake_stats(spec.site_name))

    monkeypatch.setattr(dx_wrapper.DXSettings, "from_config", staticmethod(fake_from_config))
    monkeypatch.setattr(dx_wrapper, "run_dx_job", fake_run_dx_job)

    result = dx_wrapper.run_dx_site_task("ukb-rap")

    assert result["site_name"] == "ukb-rap"
    assert captured["config_path"] == config_path
    assert captured["env_prefix"] == "HELLO_REGRESSION_DX_"
    assert captured["spec"].site_name == "ukb-rap"
    assert captured["spec"].result_filename.endswith("-local-stats.json")
