#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_WORKSTATION_INSTANCE_TYPE = "mem1_ssd1_v2_x8"
DEFAULT_WORKSTATION_SESSION_LENGTH = "1h"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prime DX login and RAP project context for tutorial 3.",
    )
    parser.add_argument(
        "--project",
        required=True,
        help="DX project ID or name to select, for example project-REDACTED1234567890EXAMPLE",
    )
    parser.add_argument(
        "--folder",
        default="/",
        help="Folder to switch to after selecting the project",
    )
    parser.add_argument(
        "--cache-dir",
        default="~/.cache/federated_architecture/dx",
        help="Hidden directory where a small priming manifest is written",
    )
    parser.add_argument(
        "--login-timeout",
        default="",
        help="Optional dx login token timeout, for example 4h",
    )
    parser.add_argument(
        "--start-workstation",
        action="store_true",
        help="Optionally launch Cloud Workstation for manual debugging",
    )
    parser.add_argument(
        "--workstation-instance-type",
        default=DEFAULT_WORKSTATION_INSTANCE_TYPE,
        help="Cloud Workstation instance type",
    )
    parser.add_argument(
        "--workstation-max-session-length",
        default=DEFAULT_WORKSTATION_SESSION_LENGTH,
        help="Cloud Workstation max_session_length input",
    )
    parser.add_argument(
        "--allow-ssh",
        action="store_true",
        help="If starting a workstation, allow SSH access to the job",
    )
    return parser.parse_args()


def run_dx(args: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["dx", *args],
        check=False,
        text=True,
        capture_output=capture_output,
    )


def ensure_secret_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def safe_project_slug(value: str) -> str:
    allowed = []
    for char in value:
        if char.isalnum() or char in {"-", "_", "."}:
            allowed.append(char)
        else:
            allowed.append("_")
    return "".join(allowed)


def ensure_dx_login(login_timeout: str) -> str:
    result = run_dx(["whoami"], capture_output=True)
    if result.returncode == 0:
        user = result.stdout.strip()
        if not user:
            raise RuntimeError("dx whoami returned success without a username")
        return user

    cmd = ["login", "--save"]
    if login_timeout:
        cmd.extend(["--timeout", login_timeout])
    login_result = run_dx(cmd)
    if login_result.returncode != 0:
        raise RuntimeError("dx login failed")

    result = run_dx(["whoami"], capture_output=True)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("dx login completed but dx whoami still failed")
    return result.stdout.strip()


def select_project(project: str, folder: str) -> str:
    result = run_dx(["select", project])
    if result.returncode != 0:
        raise RuntimeError(f"dx select failed for {project}")
    if folder and folder != "/":
        cd_result = run_dx(["cd", folder])
        if cd_result.returncode != 0:
            raise RuntimeError(f"dx cd failed for {folder}")
    pwd_result = run_dx(["pwd"], capture_output=True)
    if pwd_result.returncode != 0:
        raise RuntimeError("dx pwd failed after selecting project")
    return pwd_result.stdout.strip()


def describe_project(project: str) -> dict[str, Any]:
    result = run_dx(["describe", project, "--json"], capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"dx describe failed for {project}: {stderr}")
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected dx describe payload for {project}")
    return data


def probe_project_root() -> list[str]:
    result = run_dx(["ls", "/"], capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"dx ls / failed: {stderr}")
    entries = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return entries[:20]


def maybe_start_workstation(args: argparse.Namespace) -> str | None:
    if not args.start_workstation:
        return None

    cmd = [
        "run",
        "app-cloud_workstation",
        f"-imax_session_length={args.workstation_max_session_length}",
        "--instance-type",
        args.workstation_instance_type,
        "-y",
        "--brief",
    ]
    if args.allow_ssh:
        cmd.append("--allow-ssh")

    result = run_dx(cmd, capture_output=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(f"Cloud Workstation launch failed: {stderr}")
    job_id = result.stdout.strip()
    if not job_id:
        raise RuntimeError("Cloud Workstation launch did not return a job id")
    return job_id


def main() -> int:
    args = parse_args()
    cache_root = Path(args.cache_dir).expanduser() / safe_project_slug(args.project)
    ensure_secret_dir(cache_root)

    print(f"[1/4] Ensuring DX login")
    username = ensure_dx_login(args.login_timeout)

    print(f"[2/4] Selecting DX project {args.project}")
    pwd_value = select_project(args.project, args.folder)

    print(f"[3/4] Verifying DX project access")
    project_info = describe_project(args.project)
    root_entries = probe_project_root()

    workstation_job_id = None
    if args.start_workstation:
        print(f"[4/4] Starting Cloud Workstation")
        workstation_job_id = maybe_start_workstation(args)
    else:
        print(f"[4/4] Skipping Cloud Workstation launch")

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dx_user": username,
        "project_id": project_info.get("id"),
        "project_name": project_info.get("name"),
        "project_level": project_info.get("level"),
        "folder": args.folder,
        "pwd": pwd_value,
        "api_server": "https://api.dnanexus.com",
        "root_entries_preview": root_entries,
        "workstation": {
            "started": args.start_workstation,
            "job_id": workstation_job_id,
            "instance_type": args.workstation_instance_type if args.start_workstation else None,
            "max_session_length": (
                args.workstation_max_session_length if args.start_workstation else None
            ),
        },
    }

    manifest_path = cache_root / "session_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    manifest_path.chmod(0o600)

    print("")
    print("DX priming complete.")
    print(f"Project: {project_info.get('name')} ({project_info.get('id')})")
    print(f"User: {username}")
    print(f"Context: {pwd_value}")
    print(f"Manifest: {manifest_path}")
    if args.start_workstation:
        print(
            "Cloud Workstation: "
            f"{workstation_job_id} "
            f"(instance_type={args.workstation_instance_type}, "
            f"max_session_length={args.workstation_max_session_length})"
        )
    else:
        print("Cloud Workstation: not started")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
