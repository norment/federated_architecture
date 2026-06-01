#!/usr/bin/env python3
from __future__ import annotations

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


def run_tsd_regenie_task(site_name: str, dataset_id: int) -> str:
    """Submit a regenie job to TSD HPC via the TSD wrapper and return the result file content.

    Reads settings from the YAML config pointed to by REGENIE_TSD_CONFIG.
    The config path may be overridden per-setting via REGENIE_TSD_* environment variables
    (see TSDSettings.from_config).

    Args:
        site_name:  The NVFlare site name (e.g. "tsd").
        dataset_id: Integer passed as the first argument to the REGENIE runner script
                    (1 = snellius, 2 = tsd).

    Returns:
        The text content of the regenie step-2 output file downloaded from TSD.
    """
    custom_dir = Path(__file__).resolve().parent
    script_candidates = [
        custom_dir / "client_regenie_nodocker.sh",
        custom_dir / "hunt_client_regenie_nodocker.sh",
    ]
    regenie_script = next((path for path in script_candidates if path.exists()), None)

    configured = os.environ.get("REGENIE_TSD_CONFIG", "").strip()
    if not configured:
        raise RuntimeError(
            "REGENIE_TSD_CONFIG is required for the TSD wrapper. "
            "Set it to the site-specific YAML config path before starting the client process."
        )
    config_path = Path(configured).expanduser()

    if regenie_script is None:
        raise FileNotFoundError(
            "Regenie script not found. Expected one of: "
            f"{', '.join(str(path) for path in script_candidates)}"
        )
    if not config_path.exists():
        raise FileNotFoundError(f"TSD wrapper config not found: {config_path}")

    settings = TSDSettings.from_config(
        config_path=config_path,
        env_prefix="REGENIE_TSD_",
    )

    run_token = _run_token(site_name)
    remote_subdir = f"{settings.remote_prefix}/{run_token}"
    result_filename = f"{run_token}-regenie_step2_AD.regenie"

    # The TSD library (_build_job_script) generates a Slurm bash script with this layout:
    #
    #   #!/usr/bin/env bash          ← script header
    #   set -euo pipefail
    #   REMOTE_IMPORT_DIR=...        ← directory variables
    #   ...
    #   [remote_setup]               ← from config: source .../flare-env/bin/activate
    #   [remote_command below]       ← regenie execution
    #
    # Slurm specs (account, nodes, memory, time_limit) go as JSON fields in
    # the TSD HPC REST API call — not as #SBATCH lines in the script.
    #
    # remote_command steps:
    #   1. cd to the import directory so that the uploaded REGENIE runner is found
    #   2. Run regenie (both steps), reading inputs from $REMOTE_WORK_DIR/data
    #      and writing outputs to $REMOTE_WORK_DIR/out
    #   3. Copy the step-2 result to $REMOTE_EXPORT_DIR so the wrapper can download it
    remote_command = "\n".join(
        [
            'cd "$REMOTE_IMPORT_DIR"',
            f'bash {shlex.quote(regenie_script.name)} {dataset_id} "$REMOTE_WORK_DIR"',
            (
                f'cp "$REMOTE_WORK_DIR/out/regenie_step2_AD.regenie" '
                f'"$REMOTE_EXPORT_DIR"/{shlex.quote(result_filename)}'
            ),
        ]
    )

    result = run_tsd_job(
        settings=settings,
        spec=TSDRunSpec(
            site_name=site_name,
            job_name=f"regenie_{slugify(site_name)}",
            remote_subdir=remote_subdir,
            upload_files=[regenie_script],
            remote_command=remote_command,
            result_filename=result_filename,
            remote_work_subdir=f"regenie_on_tsd/{remote_subdir}",
        ),
    )
    return result.result_bytes.decode("utf-8")
