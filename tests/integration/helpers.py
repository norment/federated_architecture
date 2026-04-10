import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def base_env() -> dict[str, str]:
    env = os.environ.copy()
    python_bin_dir = str(Path(sys.executable).parent)
    env["PATH"] = python_bin_dir + os.pathsep + env.get("PATH", "")
    env["VENV_PYTHON"] = sys.executable
    env["VIRTUAL_ENV"] = str(Path(sys.executable).parent.parent)
    env["PYTHONUNBUFFERED"] = "1"
    return env


def require_command(name: str, *, env: dict[str, str]) -> None:
    if shutil.which(name, path=env.get("PATH")) is None:
        raise RuntimeError(f"required command not found in PATH: {name}")


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_command(
    cmd: list[str],
    *,
    env: dict[str, str],
    cwd: Path | None = None,
    timeout: int = 180,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"command failed with exit code {result.returncode}: {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


@dataclass
class ManagedProcess:
    name: str
    popen: subprocess.Popen[str]
    log_path: Path
    log_handle: object


def start_process(
    cmd: list[str],
    *,
    name: str,
    env: dict[str, str],
    cwd: Path,
    log_dir: Path,
) -> ManagedProcess:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{name}.log"
    log_handle = log_path.open("w", encoding="utf-8")
    popen = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid,
    )
    return ManagedProcess(name=name, popen=popen, log_path=log_path, log_handle=log_handle)


def stop_processes(processes: list[ManagedProcess]) -> None:
    for proc in reversed(processes):
        if proc.popen.poll() is None:
            try:
                os.killpg(proc.popen.pid, signal.SIGTERM)
                proc.popen.wait(timeout=10)
            except Exception:
                try:
                    os.killpg(proc.popen.pid, signal.SIGKILL)
                except Exception:
                    pass
        proc.log_handle.close()


def wait_for_port(host: str, port: int, *, timeout: int = 30) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.5)
    raise TimeoutError(f"timed out waiting for {host}:{port}")


def wait_for_glob(root: Path, pattern: str, *, timeout: int = 60) -> Path:
    deadline = time.time() + timeout
    while time.time() < deadline:
        matches = sorted(root.glob(pattern))
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise RuntimeError(f"expected one match for {pattern} under {root}, found {len(matches)}")
        time.sleep(1)
    raise TimeoutError(f"timed out waiting for {pattern} under {root}")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
