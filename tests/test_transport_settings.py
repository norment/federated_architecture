import json
from pathlib import Path

from tre_wrappers.dx import DXSettings
from tre_wrappers.tsd import TSDSettings


def test_dx_settings_from_config_resolves_defaults_and_expands_vars(tmp_path, monkeypatch):
    config_path = tmp_path / "dx.yml"
    config_path.write_text(
        "\n".join(
            [
                "project: project-123",
                "folder: reports",
                "remote_prefix: ${PROJECT}/runs",
                'cleanup_remote_folder: "false"',
            ]
        )
    )

    monkeypatch.delenv("HELLO_REGRESSION_DX_PROJECT", raising=False)

    settings = DXSettings.from_config(
        config_path=config_path,
        env_prefix="HELLO_REGRESSION_DX_",
    )

    assert settings.project == "project-123"
    assert settings.folder == "/reports"
    assert settings.remote_prefix == "project-123/runs"
    assert settings.cleanup_remote_folder is False
    assert settings.remote_python == "python3"


def test_tsd_settings_from_config_derives_project_and_uses_manifest(tmp_path, monkeypatch):
    config_path = tmp_path / "tsd.yml"
    config_path.write_text(
        "\n".join(
            [
                "username: p33-user",
                "import_dir: /tsd/${PROJECT}/import",
                "export_dir: /tsd/${PROJECT}/export",
            ]
        )
    )

    cache_root = tmp_path / "cache"
    project_cache = cache_root / "p33"
    project_cache.mkdir(parents=True)
    (project_cache / "session_manifest.json").write_text(json.dumps({"username": "p33-user"}))

    monkeypatch.setenv("HELLO_REGRESSION_TSD_CACHE_DIR", str(cache_root))
    monkeypatch.delenv("HELLO_REGRESSION_TSD_PROJECT", raising=False)

    settings = TSDSettings.from_config(
        config_path=config_path,
        env_prefix="HELLO_REGRESSION_TSD_",
    )

    assert settings.project == "p33"
    assert settings.username == "p33-user"
    assert settings.import_dir == "/tsd/p33/import"
    assert settings.export_dir == "/tsd/p33/export"
    assert settings.cache_dir == project_cache
