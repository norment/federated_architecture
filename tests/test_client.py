from types import SimpleNamespace

import pytest
from nvflare.client import FLModel

import client


class FakeFlare:
    def __init__(self, site_name: str):
        self.site_name = site_name
        self.sent = []
        self._running_calls = 0
        self.FLModel = FLModel

    def init(self):
        return None

    def get_site_name(self):
        return self.site_name

    def is_running(self):
        self._running_calls += 1
        return self._running_calls == 1

    def receive(self):
        return SimpleNamespace(current_round=0)

    def send(self, model):
        self.sent.append(model)


def test_get_executor_requires_explicit_env(monkeypatch):
    monkeypatch.delenv("HELLO_REGRESSION_EXECUTOR", raising=False)

    with pytest.raises(RuntimeError, match="HELLO_REGRESSION_EXECUTOR is required"):
        client._get_executor()


def test_run_site_task_local_executes_shared_site_runner():
    stats = client.run_site_task("site-a", "local")

    assert stats["site_name"] == "site-a"
    assert stats["n"] == 24
    assert stats["feature_names"] == ["intercept", "age", "sex", "exposure"]


def test_main_sends_successful_model_for_local_executor(monkeypatch):
    fake_flare = FakeFlare("site-a")
    monkeypatch.setenv("HELLO_REGRESSION_EXECUTOR", "local")
    monkeypatch.setattr(client, "flare", fake_flare)

    client.main()

    assert len(fake_flare.sent) == 1
    model = fake_flare.sent[0]
    assert model.params["SUCCESS"] is True
    assert model.meta["site_name"] == "site-a"
    assert model.meta["local_stats"]["n"] == 24


def test_main_sends_error_model_when_site_task_fails(monkeypatch):
    fake_flare = FakeFlare("site-a")
    monkeypatch.setenv("HELLO_REGRESSION_EXECUTOR", "local")
    monkeypatch.setattr(client, "flare", fake_flare)
    monkeypatch.setattr(client, "run_site_task", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    client.main()

    assert len(fake_flare.sent) == 1
    model = fake_flare.sent[0]
    assert model.params["SUCCESS"] is False
    assert model.meta["site_name"] == "site-a"
    assert "boom" in model.meta["error_message"]
