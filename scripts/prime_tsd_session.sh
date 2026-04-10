#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "${VENV_PYTHON:-}" ]]; then
  venv_python="${VENV_PYTHON}"
elif [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
  venv_python="${VIRTUAL_ENV}/bin/python"
else
  venv_python="${HOME}/venvs/nvflare_tutorial3/bin/python"
fi

if [[ ! -x "${venv_python}" ]]; then
  echo "Missing Python interpreter: ${venv_python}" >&2
  echo "Create and activate the tutorial 3 environment first, for example:" >&2
  echo "  python3 -m venv ~/venvs/nvflare_tutorial3" >&2
  echo "  source ~/venvs/nvflare_tutorial3/bin/activate" >&2
  echo "  python -m pip install --upgrade pip" >&2
  echo "  pip install nvflare numpy tsd-api-client" >&2
  echo "Or set VENV_PYTHON=/full/path/to/python before running this script." >&2
  exit 1
fi

exec "${venv_python}" "${repo_root}/scripts/prime_tsd_session.py" "$@"
