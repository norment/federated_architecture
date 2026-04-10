#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF' >&2
Usage:
  tutorial3_local.sh init <workdir> --p33-user <username> --p697-user <username> [--force]
  tutorial3_local.sh start-server <workdir>
  tutorial3_local.sh start-client-a <workdir>
  tutorial3_local.sh start-client-b <workdir>
  tutorial3_local.sh start-admin <workdir>
  tutorial3_local.sh submit <workdir> [job.py args...]

Examples:
  ./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo --p33-user p33-ofrei --p697-user p697-ofrei
  ./scripts/tutorial3_local.sh start-server ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh start-client-a ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh start-client-b ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh start-admin ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo --n_clients 2
EOF
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

command_name="$1"
workdir="$2"
shift 2

startup_dir() {
  local participant_name="$1"
  printf '%s\n' "${workdir}/workspace/${PROJECT_NAME}/prod_00/${participant_name}/startup"
}

participant_dir() {
  local participant_name="$1"
  printf '%s\n' "${workdir}/workspace/${PROJECT_NAME}/prod_00/${participant_name}"
}

detect_python() {
  if [[ -n "${VENV_PYTHON:-}" ]]; then
    printf '%s\n' "${VENV_PYTHON}"
    return
  fi
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    printf '%s\n' "${VIRTUAL_ENV}/bin/python"
    return
  fi
  if [[ -x "${HOME}/venvs/nvflare_tutorial3/bin/python" ]]; then
    printf '%s\n' "${HOME}/venvs/nvflare_tutorial3/bin/python"
    return
  fi
  printf '%s\n' "python3"
}

ensure_python_tools() {
  local python_bin
  python_bin="$(detect_python)"
  export PATH="$(dirname "${python_bin}"):${PATH}"
}

load_env() {
  local env_file
  env_file="${workdir}/.env"
  if [[ ! -f "${env_file}" ]]; then
    echo "Missing ${env_file}" >&2
    exit 1
  fi
  set -a
  # shellcheck disable=SC1090
  source "${env_file}"
  set +a
}

case "${command_name}" in
  init)
    ensure_python_tools

    p33_user=""
    p697_user=""
    force="false"
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --p33-user)
          p33_user="${2:-}"
          shift 2
          ;;
        --p697-user)
          p697_user="${2:-}"
          shift 2
          ;;
        --force)
          force="true"
          shift
          ;;
        *)
          echo "Unknown init option: $1" >&2
          usage
          ;;
      esac
    done

    if [[ -z "${p33_user}" || -z "${p697_user}" ]]; then
      echo "init requires --p33-user and --p697-user" >&2
      usage
    fi

    mkdir -p "${workdir}" "${workdir}/tsd-configs"

    if [[ "${force}" == "true" ]]; then
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/.env.template" "${workdir}/.env"
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/project.yml" "${workdir}/project.yml"
    else
      if [[ -e "${workdir}/.env" || -e "${workdir}/project.yml" ]]; then
        echo "Refusing to overwrite existing ${workdir}/.env or ${workdir}/project.yml without --force" >&2
        exit 1
      fi
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/.env.template" "${workdir}/.env"
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/project.yml" "${workdir}/project.yml"
    fi

    bash "${repo_root}/scripts/provision_from_env.sh" "${workdir}"

    python_bin="$(detect_python)"
    "${python_bin}" "${repo_root}/scripts/make_tsd_site_config.py" \
      --username "${p33_user}" \
      --output "${workdir}/tsd-configs/p33.yml" \
      --force
    "${python_bin}" "${repo_root}/scripts/make_tsd_site_config.py" \
      --username "${p697_user}" \
      --output "${workdir}/tsd-configs/p697.yml" \
      --force

    printf '%s\n' "Initialized tutorial 3 workspace at ${workdir}"
    printf '%s\n' "Generated ${workdir}/tsd-configs/p33.yml"
    printf '%s\n' "Generated ${workdir}/tsd-configs/p697.yml"
    ;;
  start-server)
    load_env
    cd "$(startup_dir "${SERVER_NAME}")"
    exec ./start.sh
    ;;
  start-client-a)
    load_env
    export HELLO_REGRESSION_EXECUTOR="${HELLO_REGRESSION_EXECUTOR:-tsd}"
    export HELLO_REGRESSION_TSD_CONFIG_DIR="${HELLO_REGRESSION_TSD_CONFIG_DIR:-${workdir}/tsd-configs}"
    cd "$(startup_dir "${WRAPPER_A_NAME}")"
    exec ./start.sh
    ;;
  start-client-b)
    load_env
    export HELLO_REGRESSION_EXECUTOR="${HELLO_REGRESSION_EXECUTOR:-tsd}"
    export HELLO_REGRESSION_TSD_CONFIG_DIR="${HELLO_REGRESSION_TSD_CONFIG_DIR:-${workdir}/tsd-configs}"
    cd "$(startup_dir "${WRAPPER_B_NAME}")"
    exec ./start.sh
    ;;
  start-admin)
    load_env
    cd "$(startup_dir "${ADMIN_NAME}")"
    exec ./fl_admin.sh
    ;;
  submit)
    load_env
    python_bin="$(detect_python)"
    cd "${repo_root}"
    exec "${python_bin}" examples/hello_regression/job.py \
      --env prod \
      --startup_kit "$(participant_dir "${ADMIN_NAME}")" \
      --username "${ADMIN_NAME}" \
      "$@"
    ;;
  *)
    usage
    ;;
esac
