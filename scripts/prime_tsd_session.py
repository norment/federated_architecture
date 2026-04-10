#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from typing import Any

import requests
import yaml


PROD_HOST = "api.tsd.usit.no"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prime TSD File API and HPC API sessions for a federated session.",
    )
    parser.add_argument("--project", default="", help="Optional TSD project, for example p33")
    parser.add_argument("--username", required=True, help="TSD username, for example p33-yourname")
    parser.add_argument(
        "--cache-dir",
        default="~/.cache/federated_architecture/tsd",
        help="Hidden directory where primed token files and manifest are stored",
    )
    parser.add_argument(
        "--upload-remote-path",
        default="federated_architecture_smoke",
        help="Remote import subdirectory for the smoke-test upload",
    )
    parser.add_argument(
        "--download-file",
        default="",
        help="Optional known export filename to download after listing the export area",
    )
    parser.add_argument(
        "--download-remote-path",
        default="",
        help="Optional remote export subdirectory for download-list or --download-file",
    )
    parser.add_argument(
        "--hpc-probe-endpoint",
        default="jobs",
        choices=["jobs", "jobs/state"],
        help="HPC read endpoint used to verify the HPC token",
    )
    parser.add_argument(
        "--force-hpc-refresh",
        action="store_true",
        help="Ignore any cached HPC token and fetch a fresh one",
    )
    parser.add_argument(
        "--min-valid-seconds",
        type=int,
        default=300,
        help="Treat tokens expiring within this window as expired",
    )
    return parser.parse_args()


def derive_project_from_username(username: str) -> str | None:
    username = username.strip()
    if not username or "-" not in username:
        return None
    project, _ = username.split("-", 1)
    return project or None


def tacl_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "tacl"
    return Path.home() / ".config" / "tacl"


def ensure_secret_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_secret(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)
    path.chmod(0o600)


def jwt_payload(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return None


def token_valid(token: str | None, min_valid_seconds: int) -> bool:
    payload = jwt_payload(token)
    if not payload or "exp" not in payload:
        return False
    return datetime.now(timezone.utc).timestamp() < payload["exp"] - min_valid_seconds


def token_summary(token: str | None) -> dict[str, Any]:
    payload = jwt_payload(token)
    if not payload:
        return {"present": False}

    exp_ts = payload.get("exp")
    exp_iso = None
    remaining_seconds = None
    if exp_ts:
        exp_dt = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
        exp_iso = exp_dt.isoformat()
        remaining_seconds = int(exp_dt.timestamp() - datetime.now(timezone.utc).timestamp())

    return {
        "present": True,
        "name": payload.get("name"),
        "user": payload.get("user") or payload.get("user_name"),
        "groups": payload.get("groups", []),
        "expires_at": exp_iso,
        "remaining_seconds": remaining_seconds,
    }


def run_tacl(args: list[str]) -> None:
    cmd = ["tacl", *args]
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"tacl failed with exit code {result.returncode}: {' '.join(cmd)}")


def api_base(project: str) -> str:
    return f"https://{PROD_HOST}/v1/{project}"


def hpc_auth_url(project: str) -> str:
    return f"{api_base(project)}/auth/tsd/token"


def load_api_key(project: str) -> str:
    config = load_yaml(tacl_dir() / "config")
    api_key = config.get("prod", {}).get(project)
    if not api_key:
        raise RuntimeError(
            f"No tacl registration found for prod:{project}. Run `tacl --register {project}` first."
        )
    return api_key


def load_tacl_access_token(project: str, token_type: str) -> str | None:
    session = load_yaml(tacl_dir() / "session")
    token = session.get("prod", {}).get(project, {}).get(token_type)
    return token if isinstance(token, str) else None


def fetch_hpc_token(
    *,
    project: str,
    username: str,
    api_key: str,
) -> str:
    password = getpass(f"TSD password for {username} > ")
    otp = input("One-time code > ").strip()
    url = hpc_auth_url(project)
    response = requests.post(
        url,
        params={"type": "hpc"},
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"user_name": username, "password": password, "otp": otp},
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to obtain HPC token ({response.status_code}): {response.text}")

    token = response.json().get("token")
    if not token:
        raise RuntimeError(f"HPC token missing from response: {response.text}")
    return token


def probe_hpc_api(*, project: str, token: str, endpoint: str) -> dict[str, Any]:
    url = f"{api_base(project)}/hpc/{endpoint}"
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    if response.status_code != 200:
        summary = token_summary(token)
        raise RuntimeError(
            "HPC probe failed "
            f"({response.status_code}) at {url}\n"
            f"token_summary={json.dumps(summary, indent=2)}\n"
            f"response_headers={dict(response.headers)}\n"
            f"response_body={response.text}"
        )
    data = response.json()
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected HPC probe payload at {url}: {type(data).__name__}")
    data["_probe_url"] = url
    data["_probe_status_code"] = response.status_code
    return data


def download_list_args(project: str, remote_path: str) -> list[str]:
    args = [project, "--download-list"]
    if remote_path:
        args.append(remote_path)
    return args


def main() -> int:
    args = parse_args()
    project = args.project or derive_project_from_username(args.username)
    if not project:
        raise RuntimeError(
            "Unable to determine TSD project. Pass --project explicitly or use a username like p33-yourname."
        )
    if args.project and derive_project_from_username(args.username) not in {None, project}:
        raise RuntimeError(
            f"--project {args.project!r} does not match username {args.username!r}. "
            "Use a matching project or omit --project."
        )

    cache_root = Path(args.cache_dir).expanduser() / project
    ensure_secret_dir(cache_root)

    api_key = load_api_key(project)

    print(f"[1/3] Priming File API import session for {project}")
    with tempfile.TemporaryDirectory(prefix=f"{project}_tsd_smoke_") as tmpdir:
        smoke_file = Path(tmpdir) / "upload_test.txt"
        smoke_file.write_text(
            f"TSD smoke test for {project} at {datetime.now(timezone.utc).isoformat()}\n",
            encoding="utf-8",
        )
        upload_args = [project, "--upload", str(smoke_file)]
        if args.upload_remote_path:
            upload_args.extend(["--remote-path", args.upload_remote_path])
        run_tacl(upload_args)

    print(f"[2/3] Priming File API export session for {project}")
    run_tacl(download_list_args(project, args.download_remote_path))
    if args.download_file:
        download_args = [project, "--download", args.download_file]
        if args.download_remote_path:
            download_args.extend(["--remote-path", args.download_remote_path])
        run_tacl(download_args)

    import_token = load_tacl_access_token(project, "import")
    export_token = load_tacl_access_token(project, "export")
    if not import_token:
        raise RuntimeError("Import token not found in tacl session store after upload")
    if not export_token:
        raise RuntimeError("Export token not found in tacl session store after download-list")

    hpc_token_path = cache_root / "hpc.token"
    cached_hpc_token = hpc_token_path.read_text(encoding="utf-8").strip() if hpc_token_path.exists() else None
    need_hpc_refresh = args.force_hpc_refresh or not token_valid(cached_hpc_token, args.min_valid_seconds)

    print(f"[3/3] Priming HPC session for {project}")
    if need_hpc_refresh:
        hpc_token = fetch_hpc_token(
            project=project,
            username=args.username,
            api_key=api_key,
        )
        write_secret(hpc_token_path, hpc_token)
    else:
        hpc_token = cached_hpc_token

    hpc_probe = probe_hpc_api(
        project=project,
        token=hpc_token,
        endpoint=args.hpc_probe_endpoint,
    )
    probe_url = hpc_probe.get("_probe_url")
    probe_status_code = hpc_probe.get("_probe_status_code")
    probe_jobs = hpc_probe.get("jobs")
    if isinstance(probe_jobs, list):
        probe_summary = f"returned {len(probe_jobs)} jobs"
    else:
        probe_summary = f"top-level keys: {', '.join(sorted(k for k in hpc_probe.keys() if not k.startswith('_')))}"

    write_secret(cache_root / "import.token", import_token)
    write_secret(cache_root / "export.token", export_token)

    manifest = {
        "project": project,
        "username": args.username,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "token_files": {
            "import": str(cache_root / "import.token"),
            "export": str(cache_root / "export.token"),
            "hpc": str(hpc_token_path),
        },
        "tacl_state": {
            "config_path": str(tacl_dir() / "config"),
            "session_path": str(tacl_dir() / "session"),
        },
        "import_token": token_summary(import_token),
        "export_token": token_summary(export_token),
        "hpc_token": token_summary(hpc_token),
        "hpc_probe_url": probe_url,
        "hpc_probe_status_code": probe_status_code,
        "hpc_probe_endpoint": args.hpc_probe_endpoint,
        "hpc_probe_ok": True,
        "hpc_probe_keys": sorted(hpc_probe.keys()) if isinstance(hpc_probe, dict) else [],
        "hpc_probe_job_count": len(probe_jobs) if isinstance(probe_jobs, list) else None,
    }
    write_secret(cache_root / "session_manifest.json", json.dumps(manifest, indent=2) + "\n")

    print()
    print("TSD priming complete.")
    print(f"Secret cache directory: {cache_root}")
    print(f"Manifest: {cache_root / 'session_manifest.json'}")
    for name in ("import_token", "export_token", "hpc_token"):
        summary = manifest[name]
        print(f"{name}: expires_at={summary.get('expires_at')} remaining_seconds={summary.get('remaining_seconds')}")
    print(f"HPC probe ok: GET {probe_url} -> {probe_status_code}, {probe_summary}")
    print("The printed expiry timestamps come from the JWT exp claim.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
