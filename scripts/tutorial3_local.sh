#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF' >&2
Usage:
  tutorial3_local.sh init <workdir> [--p33-user <username>] [--p697-user <username>] [--dx-project <project-id>] [--force]
  tutorial3_local.sh start-server <workdir>
  tutorial3_local.sh start-client-a <workdir>
  tutorial3_local.sh start-client-b <workdir>
  tutorial3_local.sh start-client-c <workdir>
  tutorial3_local.sh start-admin <workdir>
  tutorial3_local.sh submit <workdir> [job.py args...]

Examples:
  ./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo --p33-user p33-username --p697-user p697-username --dx-project project-REDACTED1234567890EXAMPLE
  ./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo_dx --dx-project project-REDACTED1234567890EXAMPLE
  ./scripts/tutorial3_local.sh start-server ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh start-client-a ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh start-client-b ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh start-client-c ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh start-admin ~/nvflare_wrapper_demo
  ./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo
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
  printf '%s\n' "${workdir}/poc/${PROJECT_NAME}/prod_00/${participant_name}/startup"
}

participant_dir() {
  local participant_name="$1"
  printf '%s\n' "${workdir}/poc/${PROJECT_NAME}/prod_00/${participant_name}"
}

configured_clients() {
  local clients=()
  if [[ -f "${workdir}/tsd-configs/${WRAPPER_A_NAME}.yml" ]]; then
    clients+=("${WRAPPER_A_NAME}")
  fi
  if [[ -f "${workdir}/tsd-configs/${WRAPPER_B_NAME}.yml" ]]; then
    clients+=("${WRAPPER_B_NAME}")
  fi
  if [[ -f "${workdir}/dx-configs/${WRAPPER_C_NAME}.yml" ]]; then
    clients+=("${WRAPPER_C_NAME}")
  fi
  printf '%s\n' "${clients[@]}"
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
  if [[ -x "${HOME}/venvs/nvflare/bin/python" ]]; then
    printf '%s\n' "${HOME}/venvs/nvflare/bin/python"
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

render_project() {
  local rendered_project
  rendered_project="${workdir}/project.rendered.yml"
  (
    cd "${workdir}"
    set -a
    source .env
    set +a
    envsubst < project.yml > project.rendered.yml
  )
  printf '%s\n' "${rendered_project}"
}

case "${command_name}" in
  init)
    ensure_python_tools

    p33_user=""
    p697_user=""
    dx_project=""
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
        --dx-project)
          dx_project="${2:-}"
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

    if [[ -z "${p33_user}" && -z "${p697_user}" && -z "${dx_project}" ]]; then
      echo "init requires at least one site option: --p33-user, --p697-user, or --dx-project" >&2
      usage
    fi

    mkdir -p "${workdir}" "${workdir}/tsd-configs" "${workdir}/dx-configs" "${workdir}/.home"

    if [[ "${force}" == "true" ]]; then
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/.env.template" "${workdir}/.env"
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/project.yml" "${workdir}/project.yml"
      rm -rf "${workdir}/poc" "${workdir}/project.rendered.yml"
    else
      if [[ -e "${workdir}/.env" || -e "${workdir}/project.yml" || -e "${workdir}/poc" ]]; then
        echo "Refusing to overwrite existing ${workdir}/.env, ${workdir}/project.yml, or ${workdir}/poc without --force" >&2
        exit 1
      fi
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/.env.template" "${workdir}/.env"
      cp "${repo_root}/docs/tutorials/assets/03-wrapper-clients/project.yml" "${workdir}/project.yml"
    fi

    rendered_project="$(render_project)"
    HOME="${workdir}/.home" NVFLARE_POC_WORKSPACE="${workdir}/poc" nvflare poc prepare -i "${rendered_project}"

    python_bin="$(detect_python)"
    if [[ -n "${p33_user}" ]]; then
      "${python_bin}" "${repo_root}/scripts/make_tsd_site_config.py" \
        --username "${p33_user}" \
        --output "${workdir}/tsd-configs/p33.yml" \
        --force
      printf '%s\n' "Generated ${workdir}/tsd-configs/p33.yml"
    fi
    if [[ -n "${p697_user}" ]]; then
      "${python_bin}" "${repo_root}/scripts/make_tsd_site_config.py" \
        --username "${p697_user}" \
        --output "${workdir}/tsd-configs/p697.yml" \
        --force
      printf '%s\n' "Generated ${workdir}/tsd-configs/p697.yml"
    fi
    if [[ -n "${dx_project}" ]]; then
      "${python_bin}" "${repo_root}/scripts/make_dx_site_config.py" \
        --project "${dx_project}" \
        --output "${workdir}/dx-configs/ukb-rap.yml" \
        --force
      printf '%s\n' "Generated ${workdir}/dx-configs/ukb-rap.yml"
    fi
    printf '%s\n' "Initialized tutorial 3 workspace at ${workdir}"
    ;;
  start-server)
    load_env
    cd "$(startup_dir "${SERVER_NAME}")"
    exec ./start.sh
    ;;
  start-client-a)
    load_env
    export HELLO_REGRESSION_EXECUTOR="tsd"
    export HELLO_REGRESSION_TSD_CONFIG="${workdir}/tsd-configs/${WRAPPER_A_NAME}.yml"
    cd "$(startup_dir "${WRAPPER_A_NAME}")"
    exec ./start.sh
    ;;
  start-client-b)
    load_env
    export HELLO_REGRESSION_EXECUTOR="tsd"
    export HELLO_REGRESSION_TSD_CONFIG="${workdir}/tsd-configs/${WRAPPER_B_NAME}.yml"
    cd "$(startup_dir "${WRAPPER_B_NAME}")"
    exec ./start.sh
    ;;
  start-client-c)
    load_env
    export HELLO_REGRESSION_EXECUTOR="dx"
    export HELLO_REGRESSION_DX_CONFIG="${workdir}/dx-configs/${WRAPPER_C_NAME}.yml"
    cd "$(startup_dir "${WRAPPER_C_NAME}")"
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
    mapfile -t detected_clients < <(configured_clients)
    if [[ ${#detected_clients[@]} -eq 0 ]]; then
      echo "No configured wrapper clients found under ${workdir}/tsd-configs or ${workdir}/dx-configs" >&2
      exit 1
    fi
    cd "${repo_root}"
    job_cmd=(
      "${python_bin}" examples/hello_regression/job.py
      --env prod
      --clients "${detected_clients[@]}"
      --startup_kit "$(participant_dir "${ADMIN_NAME}")"
      --username ""
    )
    job_cmd+=("$@")
    exec "${job_cmd[@]}"
    ;;
  *)
    usage
    ;;
esac
