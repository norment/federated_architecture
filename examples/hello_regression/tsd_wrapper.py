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
    from tre_wrappers.tsd import TSDRunSpec, TSDSettings, run_tsd_job, slugify
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tre_wrappers.tsd import TSDRunSpec, TSDSettings, run_tsd_job, slugify


def _run_token(site_name: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{slugify(site_name)}-{timestamp}-{uuid.uuid4().hex[:8]}"


def _wrapper_config_path(site_name: str, custom_dir: Path) -> Path:
    configured = os.environ.get("HELLO_REGRESSION_TSD_CONFIG")
    if configured:
        return Path(configured).expanduser()

    config_dir = os.environ.get("HELLO_REGRESSION_TSD_CONFIG_DIR")
    if config_dir:
        config_dir_path = Path(config_dir).expanduser()
        for filename in (f"{site_name}.yml", f"{slugify(site_name)}.yml"):
            candidate = config_dir_path / filename
            if candidate.exists():
                return candidate

    filenames = [f"{site_name}.yml"]
    slugged = f"{slugify(site_name)}.yml"
    if slugged not in filenames:
        filenames.append(slugged)

    search_roots = []
    for root in (Path.cwd().resolve(), custom_dir.resolve()):
        if root not in search_roots:
            search_roots.append(root)
    for root in search_roots:
        for parent in (root, *root.parents):
            for filename in filenames:
                candidate = parent / "tsd-configs" / filename
                if candidate.exists():
                    return candidate

    default_path = custom_dir / "tsd_wrapper_config.yml"
    if default_path.exists():
        return default_path

    template_path = custom_dir / "tsd_wrapper_config.yml.template"
    if template_path.exists():
        raise RuntimeError(
            "Missing TSD wrapper config. Put a site-specific file like "
            f"tsd-configs/{slugify(site_name)}.yml on the host, set HELLO_REGRESSION_TSD_CONFIG_DIR, "
            "or set HELLO_REGRESSION_TSD_CONFIG=/path/to/site-config.yml before starting the client."
        )

    raise FileNotFoundError("TSD wrapper config not found")


def run_tsd_site_task(site_name: str) -> dict:
    custom_dir = Path(__file__).resolve().parent
    common_path = custom_dir / "common.py"
    runner_path = custom_dir / "site_runner.py"
    config_path = _wrapper_config_path(site_name, custom_dir)

    if not common_path.exists() or not runner_path.exists():
        raise FileNotFoundError("common.py or site_runner.py not found next to client.py")

    settings = TSDSettings.from_config(
        config_path=config_path,
        env_prefix="HELLO_REGRESSION_TSD_",
    )
    run_token = _run_token(site_name)
    remote_subdir = f"{settings.remote_prefix}/{run_token}"
    result_filename = f"{run_token}-local-stats.json"

    remote_command = "\n".join(
        [
            'cd "$REMOTE_IMPORT_DIR"',
            (
                f"{settings.remote_python} site_runner.py "
                f"--site-name {shlex.quote(site_name)} "
                f'--output "$REMOTE_WORK_DIR"/{shlex.quote(result_filename)}'
            ),
            (
                f'cp "$REMOTE_WORK_DIR"/{shlex.quote(result_filename)} '
                f'"$REMOTE_EXPORT_DIR"/{shlex.quote(result_filename)}'
            ),
        ]
    )

    result = run_tsd_job(
        settings=settings,
        spec=TSDRunSpec(
            site_name=site_name,
            job_name=f"hello_regression_{slugify(site_name)}",
            remote_subdir=remote_subdir,
            upload_files=[common_path, runner_path],
            remote_command=remote_command,
            result_filename=result_filename,
            remote_work_subdir=f"hello_regression/{remote_subdir}",
        ),
    )
    return json.loads(result.result_bytes.decode("utf-8"))
