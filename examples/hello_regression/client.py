#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import nvflare.client as flare


def _get_executor() -> str:
    return os.environ.get("HELLO_REGRESSION_EXECUTOR", "local").strip().lower()


def _run_local_site_task(site_name: str) -> dict:
    custom_dir = Path(__file__).resolve().parent
    runner_path = custom_dir / "site_runner.py"

    if not runner_path.exists():
        raise FileNotFoundError(f"site runner not found: {runner_path}")

    with tempfile.TemporaryDirectory(prefix=f"{site_name}_hello_regression_") as tmp_dir:
        output_path = Path(tmp_dir) / "local_stats.json"
        cmd = [
            sys.executable,
            str(runner_path),
            "--site-name",
            site_name,
            "--output",
            str(output_path),
        ]

        # This subprocess call is the wrapper boundary.
        # For a real TRE wrapper, replace the local runner with a site API call.
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(
                f"site runner failed for {site_name} with code {result.returncode}: {result.stderr.strip()}"
            )

        return json.loads(output_path.read_text())


def run_site_task(site_name: str) -> dict:
    executor = _get_executor()
    if executor == "local":
        return _run_local_site_task(site_name)
    if executor == "tsd":
        from tsd_wrapper import run_tsd_site_task

        return run_tsd_site_task(site_name)
    raise RuntimeError(
        f"Unsupported HELLO_REGRESSION_EXECUTOR={executor!r}. Expected 'local' or 'tsd'."
    )


def main():
    flare.init()
    site_name = flare.get_site_name()
    executor = _get_executor()
    print(f"hello_regression client started on {site_name} with executor={executor}")

    while flare.is_running():
        input_model = flare.receive()
        if input_model is None:
            print(f"{site_name}: received no task payload; exiting")
            break

        current_round = getattr(input_model, "current_round", 0)
        print(f"{site_name}: handling round {current_round}")

        try:
            local_stats = run_site_task(site_name)
            output_model = flare.FLModel(
                params={"SUCCESS": True},
                meta={"site_name": site_name, "local_stats": local_stats},
            )
        except Exception as exc:
            output_model = flare.FLModel(
                params={"SUCCESS": False},
                meta={"site_name": site_name, "error_message": str(exc)},
            )

        flare.send(output_model)


if __name__ == "__main__":
    main()
