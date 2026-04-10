#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-") or "site"


def env_key(prefix: str, suffix: str) -> str:
    return f"{prefix}{suffix}"


def expand_vars(value: str, variables: dict[str, str]) -> str:
    pattern = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}|\$([A-Z_][A-Z0-9_]*)")

    def replace(match: re.Match[str]) -> str:
        key = match.group(1) or match.group(2)
        return variables.get(key, match.group(0))

    return pattern.sub(replace, value)


def _normalize_remote_folder(folder: str) -> str:
    folder = folder.strip() or "/"
    if not folder.startswith("/"):
        folder = f"/{folder}"
    return re.sub(r"/{2,}", "/", folder.rstrip("/")) or "/"


def _tail_text(text: str, max_lines: int = 80) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    if len(lines) <= max_lines:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


@dataclass
class DXSettings:
    project: str
    folder: str
    app_name: str
    instance_type: str
    priority: str
    remote_python: str
    remote_setup: str
    remote_prefix: str
    timeout_minutes: int
    cleanup_remote_folder: bool
    dx_bin_override: str | None = None

    @classmethod
    def from_config(
        cls,
        *,
        config_path: Path,
        env_prefix: str = "DX_",
    ) -> "DXSettings":
        config = load_yaml(config_path)
        if config and not isinstance(config, dict):
            raise RuntimeError(f"DX wrapper config must be a mapping: {config_path}")

        project = os.environ.get(env_key(env_prefix, "PROJECT")) or config.get("project")
        if not project:
            raise RuntimeError(f"Missing {env_key(env_prefix, 'PROJECT')} in environment or {config_path.name}")

        variables = {
            "PROJECT": str(project),
        }

        return cls(
            project=str(project),
            folder=_normalize_remote_folder(
                expand_vars(
                    os.environ.get(env_key(env_prefix, "FOLDER"))
                    or config.get("folder")
                    or "/federated_architecture",
                    variables,
                )
            ),
            app_name=str(
                os.environ.get(env_key(env_prefix, "APP_NAME"))
                or config.get("app_name")
                or "app-swiss-army-knife"
            ),
            instance_type=str(
                os.environ.get(env_key(env_prefix, "INSTANCE_TYPE")) or config.get("instance_type") or ""
            ).strip(),
            priority=str(
                os.environ.get(env_key(env_prefix, "PRIORITY")) or config.get("priority") or "normal"
            ).strip(),
            remote_python=expand_vars(
                os.environ.get(env_key(env_prefix, "REMOTE_PYTHON"))
                or config.get("remote_python")
                or "python3",
                variables,
            ).strip(),
            remote_setup=expand_vars(
                os.environ.get(env_key(env_prefix, "REMOTE_SETUP")) or config.get("remote_setup") or "",
                variables,
            ).strip(),
            remote_prefix=expand_vars(
                os.environ.get(env_key(env_prefix, "REMOTE_PREFIX"))
                or config.get("remote_prefix")
                or "hello_regression",
                variables,
            ).strip(),
            timeout_minutes=int(
                os.environ.get(env_key(env_prefix, "TIMEOUT_MINUTES")) or config.get("timeout_minutes") or "30"
            ),
            cleanup_remote_folder=str(
                os.environ.get(env_key(env_prefix, "CLEANUP_REMOTE_FOLDER"))
                or config.get("cleanup_remote_folder")
                or "true"
            ).strip().lower()
            in {"1", "true", "yes", "on"},
            dx_bin_override=os.environ.get(env_key(env_prefix, "DX_BIN")),
        )


@dataclass
class DXRunSpec:
    site_name: str
    job_name: str
    remote_subdir: str
    upload_files: list[Path]
    remote_command: str
    result_filename: str


@dataclass
class DXRunResult:
    job_id: str
    result_bytes: bytes
    job_info: dict[str, Any]
    remote_folder: str


class DXJobFailedError(RuntimeError):
    def __init__(
        self,
        job_id: str,
        state: str,
        job_info: dict[str, Any],
        stdout_tail: str,
        stderr_tail: str,
    ):
        message = [
            f"DX job {job_id} ended with state {state}",
            json.dumps(job_info, indent=2),
        ]
        if stdout_tail:
            message.append(f"STDOUT tail:\n{stdout_tail}")
        if stderr_tail:
            message.append(f"STDERR tail:\n{stderr_tail}")
        super().__init__("\n".join(message))
        self.job_id = job_id
        self.state = state
        self.job_info = job_info
        self.stdout_tail = stdout_tail
        self.stderr_tail = stderr_tail


def _dx_bin(settings: DXSettings) -> str:
    if settings.dx_bin_override:
        return settings.dx_bin_override
    sibling = Path(sys.executable).with_name("dx")
    if sibling.exists():
        return str(sibling)
    return shutil.which("dx") or "dx"


def _run_dx(
    settings: DXSettings,
    args: list[str],
    *,
    capture_output: bool = False,
    timeout_seconds: int | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [_dx_bin(settings), *args]
    print(f"DX wrapper: running {' '.join(shlex.quote(part) for part in cmd)}")
    return subprocess.run(
        cmd,
        text=True,
        capture_output=capture_output,
        check=False,
        timeout=timeout_seconds,
    )


def _full_remote_folder(settings: DXSettings, spec: DXRunSpec) -> str:
    return _normalize_remote_folder(f"{settings.folder}/{spec.remote_subdir}")


def _upload_file(settings: DXSettings, local_path: Path, remote_folder: str) -> str:
    result = _run_dx(
        settings,
        [
            "upload",
            str(local_path),
            "--path",
            f"{settings.project}:{remote_folder}/",
            "--parents",
            "--brief",
            "--wait",
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"dx upload failed for {local_path.name}: {result.stderr.strip()}")
    file_id = result.stdout.strip()
    if not file_id:
        raise RuntimeError(f"dx upload did not return a file id for {local_path.name}")
    return file_id


def _describe_job(settings: DXSettings, job_id: str) -> dict[str, Any]:
    result = _run_dx(settings, ["describe", job_id, "--json"], capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"dx describe failed for {job_id}: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected dx describe payload for {job_id}")
    return data


def _watch_job_stream(settings: DXSettings, job_id: str, stream_flag: str) -> str:
    result = _run_dx(
        settings,
        ["watch", job_id, stream_flag, "--no-timestamps", "--no-job-info"],
        capture_output=True,
    )
    if result.returncode != 0:
        return ""
    return _tail_text(result.stdout.strip())


def _wait_for_job(settings: DXSettings, job_id: str) -> dict[str, Any]:
    timeout_seconds = max(settings.timeout_minutes * 60, 60)
    try:
        result = _run_dx(settings, ["wait", job_id], capture_output=True, timeout_seconds=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"DX job {job_id} did not finish within {settings.timeout_minutes} minutes"
        ) from exc
    job_info = _describe_job(settings, job_id)
    if result.returncode != 0:
        state = str(job_info.get("state", "unknown"))
        raise DXJobFailedError(
            job_id=job_id,
            state=state,
            job_info=job_info,
            stdout_tail=_watch_job_stream(settings, job_id, "--get-stdout"),
            stderr_tail=_watch_job_stream(settings, job_id, "--get-stderr"),
        )
    return job_info


def _download_result(settings: DXSettings, remote_path: str) -> bytes:
    with tempfile.TemporaryDirectory(prefix="dx_wrapper_download_") as tmpdir:
        local_path = Path(tmpdir) / Path(remote_path).name
        result = _run_dx(
            settings,
            ["download", f"{settings.project}:{remote_path}", "--output", str(local_path), "--overwrite"],
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(f"dx download failed for {remote_path}: {result.stderr.strip()}")
        return local_path.read_bytes()


def _cleanup_remote_folder(settings: DXSettings, remote_folder: str) -> None:
    result = _run_dx(
        settings,
        ["rm", "-r", "-f", f"{settings.project}:{remote_folder}"],
        capture_output=True,
    )
    if result.returncode != 0:
        print(
            f"DX wrapper: warning: failed to clean up {settings.project}:{remote_folder}: {result.stderr.strip()}"
        )


def run_dx_job(settings: DXSettings, spec: DXRunSpec) -> DXRunResult:
    remote_folder = _full_remote_folder(settings, spec)
    input_ids = [_upload_file(settings, path, remote_folder) for path in spec.upload_files]

    command_lines = []
    if settings.remote_setup:
        command_lines.append(settings.remote_setup)
    command_lines.append(spec.remote_command.strip())
    remote_command = "set -euo pipefail\n" + "\n".join(command_lines)

    args = [
        "run",
        settings.app_name,
        "-icmd=" + remote_command,
        "--destination",
        f"{settings.project}:{remote_folder}",
        "--name",
        spec.job_name,
        "--priority",
        settings.priority,
        "-y",
        "--brief",
    ]
    if settings.instance_type:
        args.extend(["--instance-type", settings.instance_type])
    for file_id in input_ids:
        args.append(f"-iin={file_id}")

    submit_result = _run_dx(settings, args, capture_output=True)
    if submit_result.returncode != 0:
        raise RuntimeError(f"dx run failed: {submit_result.stderr.strip()}")

    job_id = submit_result.stdout.strip()
    if not job_id:
        raise RuntimeError("dx run did not return a job id")

    job_info = _wait_for_job(settings, job_id)
    remote_result_path = f"{remote_folder}/{spec.result_filename}"
    result_bytes = _download_result(settings, remote_result_path)

    if settings.cleanup_remote_folder:
        _cleanup_remote_folder(settings, remote_folder)

    return DXRunResult(
        job_id=job_id,
        result_bytes=result_bytes,
        job_info=job_info,
        remote_folder=remote_folder,
    )
