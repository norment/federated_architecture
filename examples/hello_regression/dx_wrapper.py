#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
import uuid

try:
    from tre_wrappers.dx import DXRunSpec, DXSettings, run_dx_job, slugify
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tre_wrappers.dx import DXRunSpec, DXSettings, run_dx_job, slugify


def _run_token(site_name: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{slugify(site_name)}-{timestamp}-{uuid.uuid4().hex[:8]}"


def run_dx_site_task(site_name: str) -> dict:
    custom_dir = Path(__file__).resolve().parent
    common_path = custom_dir / "common.py"
    runner_path = custom_dir / "site_runner.py"
    configured = os.environ.get("HELLO_REGRESSION_DX_CONFIG", "").strip()
    if not configured:
        raise RuntimeError(
            "HELLO_REGRESSION_DX_CONFIG is required for the DX wrapper. "
            "Set it to the site-specific YAML config path before starting the client process."
        )
    config_path = Path(configured).expanduser()

    if not common_path.exists() or not runner_path.exists():
        raise FileNotFoundError("common.py or site_runner.py not found next to client.py")
    if not config_path.exists():
        raise FileNotFoundError(f"DX wrapper config not found: {config_path}")

    settings = DXSettings.from_config(
        config_path=config_path,
        env_prefix="HELLO_REGRESSION_DX_",
    )
    run_token = _run_token(site_name)
    remote_subdir = f"{settings.remote_prefix}/{run_token}"
    result_filename = f"{run_token}-local-stats.json"

    remote_command = (
        f"{settings.remote_python} site_runner.py "
        f"--site-name {shlex.quote(site_name)} "
        f"--output {shlex.quote(result_filename)}"
    )

    result = run_dx_job(
        settings=settings,
        spec=DXRunSpec(
            site_name=site_name,
            job_name=f"hello_regression_{slugify(site_name)}",
            remote_subdir=remote_subdir,
            upload_files=[common_path, runner_path],
            remote_command=remote_command,
            result_filename=result_filename,
        ),
    )
    return json.loads(result.result_bytes.decode("utf-8"))
