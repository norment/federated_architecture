import re
import shutil
import time
from pathlib import Path

import pytest

from .helpers import (
    REPO_ROOT,
    base_env,
    find_free_port,
    load_json,
    require_command,
    run_command,
    start_process,
    stop_processes,
    wait_for_glob,
    wait_for_port,
)


pytestmark = pytest.mark.integration


def _require_local_nvflare_tools(env: dict[str, str]) -> None:
    try:
        require_command("nvflare", env=env)
        require_command("envsubst", env=env)
    except RuntimeError as exc:
        pytest.skip(str(exc))


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_tutorial1_sim_mode_runs_live_nvflare_job():
    env = base_env()
    try:
        require_command("nvflare", env=env)
    except RuntimeError as exc:
        pytest.skip(str(exc))

    env["HELLO_REGRESSION_EXECUTOR"] = "local"
    result = run_command(
            [
                env["VENV_PYTHON"],
                "examples/hello_regression/job.py",
                "--env",
                "sim",
                "--clients",
                "site-a",
                "site-b",
            ],
        env=env,
        cwd=REPO_ROOT,
        timeout=180,
    )

    match = re.search(r"Wrote summary to (.+hello_regression_summary\.json)", result.stdout)
    assert match, result.stdout
    summary_path = Path(match.group(1).strip())
    summary = load_json(summary_path)
    assert sorted(summary["site_names"]) == ["site-a", "site-b"]
    assert summary["total_samples"] == 56
    assert "Job status:" in result.stdout


def test_tutorial2_native_clients_run_in_local_poc_harness(tmp_path: Path):
    env = base_env()
    _require_local_nvflare_tools(env)

    project_name = "integration_native_two_sites"
    fl_port = find_free_port()
    admin_port = find_free_port()
    workdir = tmp_path / "tutorial2"
    log_dir = tmp_path / "logs"
    startup_root = workdir / "poc" / project_name / "prod_00"
    workdir.mkdir(parents=True, exist_ok=True)

    shutil.copy(
        REPO_ROOT / "docs/tutorials/assets/02-dedicated-server-native-clients/project.yml",
        workdir / "project.yml",
    )
    _write_text(
        workdir / ".env",
        "\n".join(
            [
                f"PROJECT_NAME={project_name}",
                "SERVER_NAME=localhost",
                f"LOCAL_FL_PORT={fl_port}",
                f"PUBLIC_FL_PORT={fl_port}",
                f"ADMIN_PORT={admin_port}",
                "ADMIN_HOST=localhost",
                "ORG_NAME=demo",
                "CLIENT_A_NAME=site-a",
                "CLIENT_B_NAME=site-b",
                "ADMIN_NAME=admin@demo.org",
                "",
            ]
        ),
    )

    run_command(
        [
            "bash",
            "-lc",
            "set -a; source .env; set +a; envsubst < project.yml > project.rendered.yml",
        ],
        env=env,
        cwd=workdir,
        timeout=60,
    )
    run_command(
        ["nvflare", "poc", "prepare", "-i", str(workdir / "project.rendered.yml")],
        env={
            **env,
            "HOME": str(workdir / ".home"),
            "NVFLARE_POC_WORKSPACE": str(workdir / "poc"),
        },
        cwd=REPO_ROOT,
        timeout=180,
    )

    processes = []
    try:
        processes.append(
            start_process(
                ["bash", "-lc", "./start.sh"],
                name="tutorial2-server",
                env=env,
                cwd=startup_root / "localhost" / "startup",
                log_dir=log_dir,
            )
        )
        wait_for_port("127.0.0.1", fl_port, timeout=30)

        client_env = {**env, "HELLO_REGRESSION_EXECUTOR": "local"}
        for client_name in ("site-a", "site-b"):
            processes.append(
                start_process(
                    ["bash", "-lc", "./start.sh"],
                    name=f"tutorial2-{client_name}",
                    env=client_env,
                    cwd=startup_root / client_name / "startup",
                    log_dir=log_dir,
                )
            )

        time.sleep(5)
        result = run_command(
                [
                    env["VENV_PYTHON"],
                    "examples/hello_regression/job.py",
                    "--env",
                    "prod",
                    "--clients",
                    "site-a",
                    "site-b",
                    "--startup_kit",
                    str(startup_root / "admin@demo.org"),
                    "--username",
                "admin@demo.org",
            ],
            env=env,
            cwd=REPO_ROOT,
            timeout=240,
        )

        summary_path = wait_for_glob(
            startup_root / "admin@demo.org" / "transfer",
            "*/workspace/server_results/hello_regression_summary.json",
            timeout=60,
        )
        summary = load_json(summary_path)
        assert sorted(summary["site_names"]) == ["site-a", "site-b"]
        assert summary["total_samples"] == 56
        assert "Job status:" in result.stdout
    finally:
        stop_processes(processes)


def test_tutorial3_poc_mode_runs_live_local_workspace_with_mocked_wrappers(tmp_path: Path):
    env = base_env()
    _require_local_nvflare_tools(env)

    project_name = "integration_wrapper_three_sites"
    fl_port = find_free_port()
    admin_port = find_free_port()
    workdir = tmp_path / "tutorial3"
    log_dir = tmp_path / "logs"
    startup_root = workdir / "poc" / project_name / "prod_00"
    workdir.mkdir(parents=True, exist_ok=True)

    shutil.copy(
        REPO_ROOT / "docs/tutorials/assets/03-wrapper-clients/project.yml",
        workdir / "project.yml",
    )
    _write_text(
        workdir / ".env",
        "\n".join(
            [
                f"PROJECT_NAME={project_name}",
                "SERVER_NAME=localhost",
                f"FL_PORT={fl_port}",
                f"ADMIN_PORT={admin_port}",
                "ORG_NAME=demo",
                "WRAPPER_A_NAME=p33",
                "WRAPPER_B_NAME=p697",
                "WRAPPER_C_NAME=ukb-rap",
                "ADMIN_NAME=admin@demo.org",
                "",
            ]
        ),
    )

    render_result = run_command(
        [
            "bash",
            "-lc",
            "set -a; source .env; set +a; envsubst < project.yml > project.rendered.yml",
        ],
        env=env,
        cwd=workdir,
        timeout=60,
    )
    assert render_result.returncode == 0

    run_command(
        ["nvflare", "poc", "prepare", "-i", str(workdir / "project.rendered.yml")],
        env={
            **env,
            "HOME": str(workdir / ".home"),
            "NVFLARE_POC_WORKSPACE": str(workdir / "poc"),
        },
        cwd=REPO_ROOT,
        timeout=180,
    )

    run_command(
        [
            env["VENV_PYTHON"],
            "scripts/make_tsd_site_config.py",
            "--username",
            "p33-test",
            "--output",
            str(workdir / "tsd-configs/p33.yml"),
            "--force",
        ],
        env=env,
        cwd=REPO_ROOT,
    )
    run_command(
        [
            env["VENV_PYTHON"],
            "scripts/make_tsd_site_config.py",
            "--username",
            "p697-test",
            "--output",
            str(workdir / "tsd-configs/p697.yml"),
            "--force",
        ],
        env=env,
        cwd=REPO_ROOT,
    )
    run_command(
        [
            env["VENV_PYTHON"],
            "scripts/make_dx_site_config.py",
            "--project",
            "project-mock",
            "--output",
            str(workdir / "dx-configs/ukb-rap.yml"),
            "--force",
        ],
        env=env,
        cwd=REPO_ROOT,
    )

    processes = []
    mock_env = {
        **env,
        "HELLO_REGRESSION_TSD_MOCK_MODE": "local",
        "HELLO_REGRESSION_DX_MOCK_MODE": "local",
    }
    try:
        processes.append(
            start_process(
                ["bash", str(REPO_ROOT / "scripts/tutorial3_local.sh"), "start-server", str(workdir)],
                name="tutorial3-server",
                env=mock_env,
                cwd=REPO_ROOT,
                log_dir=log_dir,
            )
        )
        wait_for_port("127.0.0.1", fl_port, timeout=30)

        for command_name in ("start-client-a", "start-client-b", "start-client-c"):
            processes.append(
                start_process(
                    ["bash", str(REPO_ROOT / "scripts/tutorial3_local.sh"), command_name, str(workdir)],
                    name=f"tutorial3-{command_name}",
                    env=mock_env,
                    cwd=REPO_ROOT,
                    log_dir=log_dir,
                )
            )

        time.sleep(5)
        result = run_command(
            [
                "bash",
                str(REPO_ROOT / "scripts/tutorial3_local.sh"),
                "submit",
                str(workdir),
            ],
            env=mock_env,
            cwd=REPO_ROOT,
            timeout=240,
        )

        summary_path = wait_for_glob(
            startup_root / "admin@demo.org" / "transfer",
            "*/workspace/server_results/hello_regression_summary.json",
            timeout=60,
        )
        summary = load_json(summary_path)
        assert sorted(summary["site_names"]) == ["p33", "p697", "ukb-rap"]
        assert summary["total_samples"] > 0
        assert "Job status:" in result.stdout
    finally:
        stop_processes(processes)
