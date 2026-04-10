#!/usr/bin/env python3
from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from typing import Any

import requests
import yaml


PROD_HOST = "api.tsd.usit.no"


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


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


def tacl_dir() -> Path:
    if os.sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "tacl"
    return Path.home() / ".config" / "tacl"


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-") or "site"


def env_key(prefix: str, suffix: str) -> str:
    return f"{prefix}{suffix}"


def derive_project_from_username(username: str | None) -> str | None:
    if not username:
        return None
    username = username.strip()
    if not username or "-" not in username:
        return None
    project, _ = username.split("-", 1)
    return project or None


def expand_vars(value: str, variables: dict[str, str]) -> str:
    pattern = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2)
        return variables.get(key, match.group(0))

    return pattern.sub(replace, value)


def api_base(project: str) -> str:
    return f"https://{PROD_HOST}/v1/{project}"


def hpc_auth_url(project: str) -> str:
    return f"{api_base(project)}/auth/tsd/token"


@dataclass
class TSDSettings:
    project: str
    username: str
    import_dir: str
    export_dir: str
    work_dir: str
    slurm_account: str
    remote_python: str
    remote_setup: str
    remote_prefix: str
    poll_interval_seconds: int
    timeout_minutes: int
    min_valid_seconds: int
    cache_root: Path
    tacl_bin_override: str | None = None

    @classmethod
    def from_config(
        cls,
        *,
        config_path: Path,
        env_prefix: str = "TSD_",
    ) -> "TSDSettings":
        config = load_yaml(config_path)
        if config and not isinstance(config, dict):
            raise RuntimeError(f"TSD wrapper config must be a mapping: {config_path}")

        configured_username = os.environ.get(env_key(env_prefix, "USERNAME")) or config.get("username")
        project = (
            os.environ.get(env_key(env_prefix, "PROJECT"))
            or config.get("project")
            or derive_project_from_username(configured_username)
        )
        if not project:
            raise RuntimeError(
                f"Missing {env_key(env_prefix, 'PROJECT')} and unable to derive project from username in {config_path.name}"
            )

        cache_root = Path(
            os.environ.get(env_key(env_prefix, "CACHE_DIR"), "~/.cache/federated_architecture/tsd")
        ).expanduser()
        manifest = load_yaml(cache_root / project / "session_manifest.json")

        username = configured_username or manifest.get("username")
        if not username:
            raise RuntimeError(
                f"Missing {env_key(env_prefix, 'USERNAME')} and no username found in primed manifest"
            )

        variables = {
            "PROJECT": project,
            "USERNAME": username,
        }

        import_dir = expand_vars(
            os.environ.get(env_key(env_prefix, "IMPORT_DIR"))
            or config.get("import_dir")
            or "/tsd/${PROJECT}/data/durable/file-import/${PROJECT}-member-group",
            variables,
        )
        export_dir = expand_vars(
            os.environ.get(env_key(env_prefix, "EXPORT_DIR"))
            or config.get("export_dir")
            or "/tsd/${PROJECT}/data/durable/file-export",
            variables,
        )
        work_dir = expand_vars(
            os.environ.get(env_key(env_prefix, "WORK_DIR"))
            or config.get("work_dir")
            or "/tsd/${PROJECT}/home/${USERNAME}",
            variables,
        )
        slurm_account = expand_vars(
            os.environ.get(env_key(env_prefix, "SLURM_ACCOUNT"))
            or config.get("slurm_account")
            or "${PROJECT}_tsd",
            variables,
        )

        return cls(
            project=project,
            username=username,
            import_dir=import_dir,
            export_dir=export_dir,
            work_dir=work_dir,
            slurm_account=slurm_account,
            remote_python=expand_vars(
                os.environ.get(env_key(env_prefix, "REMOTE_PYTHON"))
                or config.get("remote_python")
                or "python3",
                variables,
            ),
            remote_setup=expand_vars(
                os.environ.get(env_key(env_prefix, "REMOTE_SETUP"))
                or config.get("remote_setup")
                or "",
                variables,
            ).strip(),
            remote_prefix=expand_vars(
                os.environ.get(env_key(env_prefix, "REMOTE_PREFIX"))
                or config.get("remote_prefix")
                or "tsd_job",
                variables,
            ),
            poll_interval_seconds=int(
                os.environ.get(env_key(env_prefix, "POLL_INTERVAL_SECONDS"))
                or config.get("poll_interval_seconds", "10")
            ),
            timeout_minutes=int(
                os.environ.get(env_key(env_prefix, "TIMEOUT_MINUTES")) or config.get("timeout_minutes", "30")
            ),
            min_valid_seconds=int(
                os.environ.get(env_key(env_prefix, "MIN_VALID_SECONDS")) or config.get("min_valid_seconds", "300")
            ),
            cache_root=cache_root,
            tacl_bin_override=os.environ.get(env_key(env_prefix, "TACL_BIN")),
        )

    @property
    def cache_dir(self) -> Path:
        return self.cache_root / self.project

    @property
    def hpc_token_path(self) -> Path:
        manifest = load_yaml(self.cache_dir / "session_manifest.json")
        configured = manifest.get("token_files", {}).get("hpc")
        if configured:
            return Path(configured).expanduser()
        return self.cache_dir / "hpc.token"

    @property
    def tacl_config_path(self) -> Path:
        return tacl_dir() / "config"


@dataclass
class TSDRunSpec:
    site_name: str
    job_name: str
    remote_subdir: str
    upload_files: list[Path]
    remote_command: str
    result_filename: str
    remote_work_subdir: str | None = None
    remote_export_subdir: str | None = None


@dataclass
class TSDRunResult:
    job_id: str
    result_bytes: bytes
    job_info: dict[str, Any]


class TSDJobFailedError(RuntimeError):
    def __init__(self, job_id: str, state: str, job_info: dict[str, Any]):
        super().__init__(f"TSD job {job_id} ended with state {state}: {json.dumps(job_info, indent=2)}")
        self.job_id = job_id
        self.state = state
        self.job_info = job_info


def _mock_mode_enabled() -> bool:
    return os.environ.get("HELLO_REGRESSION_TSD_MOCK_MODE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "local",
    }


def _run_tsd_job_mock(*, settings: TSDSettings, spec: TSDRunSpec) -> TSDRunResult:
    print(f"TSD wrapper: mock mode local execution for {spec.site_name}")

    with tempfile.TemporaryDirectory(prefix=f"{slugify(spec.site_name)}_tsd_mock_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        remote_import_dir = tmp_path / "remote_import"
        remote_export_dir = tmp_path / "remote_export"
        remote_work_dir = tmp_path / "remote_work"
        remote_import_dir.mkdir(parents=True, exist_ok=True)
        remote_export_dir.mkdir(parents=True, exist_ok=True)
        remote_work_dir.mkdir(parents=True, exist_ok=True)

        for file_path in spec.upload_files:
            shutil.copy2(file_path, remote_import_dir / file_path.name)

        command_lines = []
        if settings.remote_setup:
            command_lines.append(settings.remote_setup)
        command_lines.append(spec.remote_command.strip())
        result = subprocess.run(
            ["bash", "-lc", "set -euo pipefail\n" + "\n".join(command_lines)],
            cwd=str(remote_import_dir),
            text=True,
            capture_output=True,
            check=False,
            env={
                **os.environ,
                "REMOTE_IMPORT_DIR": str(remote_import_dir),
                "REMOTE_EXPORT_DIR": str(remote_export_dir),
                "REMOTE_WORK_DIR": str(remote_work_dir),
            },
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"TSD mock job failed for {spec.site_name} with code {result.returncode}\n"
                f"STDOUT:\n{result.stdout.strip()}\n"
                f"STDERR:\n{result.stderr.strip()}"
            )

        result_path = remote_export_dir / spec.result_filename
        if not result_path.exists():
            raise FileNotFoundError(f"TSD mock result not found: {result_path}")

        return TSDRunResult(
            job_id=f"mock-tsd-{slugify(spec.site_name)}",
            result_bytes=result_path.read_bytes(),
            job_info={"job_state": "COMPLETED", "mock_mode": True},
        )


def _tacl_cmd(settings: TSDSettings, args: list[str]) -> list[str]:
    if settings.tacl_bin_override:
        tacl_bin = settings.tacl_bin_override
    else:
        sibling = Path(sys.executable).with_name("tacl")
        tacl_bin = str(sibling) if sibling.exists() else (shutil.which("tacl") or "tacl")
    return [tacl_bin, *args]


def _run_tacl(settings: TSDSettings, args: list[str], cwd: str | None = None) -> None:
    cmd = _tacl_cmd(settings, args)
    print(f"TSD wrapper: running {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"tacl failed with exit code {result.returncode}: {' '.join(cmd)}")


def _load_api_key(settings: TSDSettings) -> str:
    config = load_yaml(settings.tacl_config_path)
    api_key = config.get("prod", {}).get(settings.project)
    if not api_key:
        raise RuntimeError(
            f"No tacl registration found for prod:{settings.project}. "
            f"Run `tacl --register {settings.project}` first."
        )
    return api_key


def _load_hpc_token(settings: TSDSettings) -> str | None:
    path = settings.hpc_token_path
    if not path.exists():
        return None
    token = path.read_text(encoding="utf-8").strip()
    return token if token_valid(token, settings.min_valid_seconds) else None


def _save_hpc_token(settings: TSDSettings, token: str) -> None:
    path = settings.hpc_token_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token, encoding="utf-8")
    path.chmod(0o600)


def _fetch_hpc_token(settings: TSDSettings) -> str:
    api_key = _load_api_key(settings)
    password = getpass(f"TSD password for {settings.username} > ")
    otp = input("One-time code > ").strip()
    response = requests.post(
        hpc_auth_url(settings.project),
        params={"type": "hpc"},
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={"user_name": settings.username, "password": password, "otp": otp},
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to obtain HPC token ({response.status_code}): {response.text}")
    token = response.json().get("token")
    if not token:
        raise RuntimeError(f"HPC token missing from response: {response.text}")
    _save_hpc_token(settings, token)
    return token


def _get_hpc_token(settings: TSDSettings) -> str:
    return _load_hpc_token(settings) or _fetch_hpc_token(settings)


def _submit_job(settings: TSDSettings, token: str, remote_job_script: str, job_name: str) -> str:
    response = requests.post(
        f"{api_base(settings.project)}/hpc/job/submit",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "script": f"#!/bin/bash\nbash -l {remote_job_script}",
            "job": {
                "name": job_name,
                "account": settings.slurm_account,
                "current_working_directory": settings.work_dir,
                "environment": [
                    f"HOME=/tsd/{settings.project}/home/{settings.username}",
                    f"USER={settings.username}",
                    f"LOGNAME={settings.username}",
                    "PATH=/bin/:/usr/bin/:/usr/local/bin/:/sbin/",
                ],
                "nodes": "1",
                "tasks": 1,
                "memory_per_cpu": {"set": True, "number": 4096},
                "time_limit": {"set": True, "number": settings.timeout_minutes},
            },
        },
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"TSD job submission failed ({response.status_code}): {response.text}")
    job_id = str(response.json().get("job_id", ""))
    if not job_id:
        raise RuntimeError(f"No job_id in TSD response: {response.text}")
    return job_id


def _get_job_status(settings: TSDSettings, token: str, job_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{api_base(settings.project)}/hpc/job/{job_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=60,
    )
    if response.status_code != 200:
        raise RuntimeError(f"TSD job status query failed ({response.status_code}): {response.text}")
    jobs = response.json().get("jobs", [])
    if not jobs:
        raise RuntimeError(f"No TSD job found with id {job_id}")
    return jobs[0]


def _wait_for_job(settings: TSDSettings, token: str, job_id: str) -> dict[str, Any]:
    deadline = time.time() + (settings.timeout_minutes * 60)
    while True:
        job_info = _get_job_status(settings, token, job_id)
        state = job_info.get("job_state")
        print(f"TSD wrapper: job {job_id} state={state}")
        if state == "COMPLETED":
            return job_info
        if state in {"FAILED", "CANCELLED", "TIMEOUT"}:
            raise TSDJobFailedError(job_id, state, job_info)
        if time.time() > deadline:
            raise TimeoutError(f"TSD job {job_id} did not complete within {settings.timeout_minutes} minutes")
        time.sleep(settings.poll_interval_seconds)


def _log_filenames(spec: TSDRunSpec) -> tuple[str, str]:
    stem = spec.result_filename[:-5] if spec.result_filename.endswith(".json") else spec.result_filename
    return f"{stem}.stdout.log", f"{stem}.stderr.log"


def _build_job_script(settings: TSDSettings, spec: TSDRunSpec) -> str:
    remote_import_dir = f"{settings.import_dir}/{spec.remote_subdir}"
    export_subdir = spec.remote_export_subdir or spec.remote_subdir
    remote_export_dir = f"{settings.export_dir}/{export_subdir}"
    work_subdir = spec.remote_work_subdir or spec.remote_subdir
    remote_work_dir = f"{settings.work_dir}/{work_subdir}"
    stdout_log_name, stderr_log_name = _log_filenames(spec)
    setup_block = f"{settings.remote_setup}\n" if settings.remote_setup else ""
    command_block = textwrap.indent(spec.remote_command.strip(), "  ")
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        set -euo pipefail

        REMOTE_IMPORT_DIR="{remote_import_dir}"
        REMOTE_EXPORT_DIR="{remote_export_dir}"
        REMOTE_WORK_DIR="{remote_work_dir}"
        WRAPPER_STDOUT_LOG="${{REMOTE_EXPORT_DIR}}/{stdout_log_name}"
        WRAPPER_STDERR_LOG="${{REMOTE_EXPORT_DIR}}/{stderr_log_name}"

        mkdir -p "${{REMOTE_EXPORT_DIR}}" "${{REMOTE_WORK_DIR}}"
        exec > >(tee -a "${{WRAPPER_STDOUT_LOG}}") 2> >(tee -a "${{WRAPPER_STDERR_LOG}}" >&2)
        {setup_block}{command_block}
        rm -rf "${{REMOTE_IMPORT_DIR}}" "${{REMOTE_WORK_DIR}}"
        """
    )


def _read_downloaded_file(download_dir: Path, filename: str) -> bytes:
    result_path = download_dir / filename
    if not result_path.exists():
        matches = sorted(download_dir.rglob(filename))
        if len(matches) == 1:
            result_path = matches[0]
        elif len(matches) > 1:
            raise FileNotFoundError(
                f"Downloaded file {filename} found in multiple locations: "
                f"{', '.join(str(path) for path in matches)}"
            )
        else:
            raise FileNotFoundError(f"Expected downloaded file not found under: {download_dir}")
    return result_path.read_bytes()


def _download_optional_export_file(
    settings: TSDSettings,
    remote_subdir: str,
    filename: str,
    download_dir: Path,
) -> bytes | None:
    cmd = _tacl_cmd(
        settings,
        [settings.project, "--download", filename, "--remote-path", f"/{remote_subdir}"],
    )
    result = subprocess.run(cmd, cwd=str(download_dir), text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return None
    try:
        return _read_downloaded_file(download_dir, filename)
    except FileNotFoundError:
        return None


def _log_excerpt(data: bytes | None, label: str) -> str | None:
    if not data:
        return None
    text = data.decode("utf-8", errors="replace").strip()
    if not text:
        return None
    lines = text.splitlines()
    if len(lines) > 40:
        text = "\n".join(lines[-40:])
    return f"{label}:\n{text}"


def run_tsd_job(*, settings: TSDSettings, spec: TSDRunSpec) -> TSDRunResult:
    if not spec.upload_files:
        raise ValueError("upload_files must not be empty")
    if _mock_mode_enabled():
        return _run_tsd_job_mock(settings=settings, spec=spec)

    with tempfile.TemporaryDirectory(prefix=f"{slugify(spec.site_name)}_tsd_wrapper_") as tmp_dir:
        tmp_path = Path(tmp_dir)
        job_script_path = tmp_path / "run.sh"
        job_script_path.write_text(_build_job_script(settings, spec), encoding="utf-8")
        job_script_path.chmod(0o755)

        upload_args_base = [settings.project]
        for file_path in [*spec.upload_files, job_script_path]:
            _run_tacl(settings, upload_args_base + ["--upload", str(file_path), "--remote-path", spec.remote_subdir])

        token = _get_hpc_token(settings)
        remote_job_script = f"{settings.import_dir}/{spec.remote_subdir}/{job_script_path.name}"
        job_id = _submit_job(settings, token, remote_job_script, spec.job_name)
        print(f"TSD wrapper: submitted job {job_id} for {spec.site_name}")

        download_dir = tmp_path / "download"
        download_dir.mkdir(parents=True, exist_ok=True)
        remote_download_subdir = spec.remote_export_subdir or spec.remote_subdir
        try:
            job_info = _wait_for_job(settings, token, job_id)
        except TSDJobFailedError as exc:
            stdout_log_name, stderr_log_name = _log_filenames(spec)
            stdout_log = _download_optional_export_file(
                settings, remote_download_subdir, stdout_log_name, download_dir
            )
            stderr_log = _download_optional_export_file(
                settings, remote_download_subdir, stderr_log_name, download_dir
            )
            details = [str(exc)]
            standard_output = exc.job_info.get("standard_output")
            standard_error = exc.job_info.get("standard_error")
            if standard_output or standard_error:
                details.append(
                    "slurm log paths:"
                    f"\nstdout={standard_output}"
                    f"\nstderr={standard_error}"
                )
            stdout_excerpt = _log_excerpt(stdout_log, "wrapper stdout tail")
            stderr_excerpt = _log_excerpt(stderr_log, "wrapper stderr tail")
            if stdout_excerpt:
                details.append(stdout_excerpt)
            if stderr_excerpt:
                details.append(stderr_excerpt)
            raise RuntimeError("\n\n".join(details)) from exc

        _run_tacl(
            settings,
            [settings.project, "--download", spec.result_filename, "--remote-path", f"/{remote_download_subdir}"],
            cwd=str(download_dir),
        )
        return TSDRunResult(
            job_id=job_id,
            result_bytes=_read_downloaded_file(download_dir, spec.result_filename),
            job_info=job_info,
        )
