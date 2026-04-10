#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <workdir-with-.env-and-project.yml>" >&2
  exit 1
fi

workdir="$1"
env_file="${workdir}/.env"
project_template="${workdir}/project.yml"
rendered_project="${workdir}/project.rendered.yml"

if [[ ! -f "${env_file}" ]]; then
  echo "Missing ${env_file}" >&2
  exit 1
fi

if [[ ! -f "${project_template}" ]]; then
  echo "Missing ${project_template}" >&2
  exit 1
fi

if ! command -v envsubst >/dev/null 2>&1; then
  echo "envsubst is required but was not found in PATH" >&2
  exit 1
fi

if ! command -v nvflare >/dev/null 2>&1; then
  echo "nvflare is required but was not found in PATH" >&2
  exit 1
fi

(
  cd "${workdir}"
  set -a
  source .env
  set +a
  envsubst < project.yml > project.rendered.yml
  nvflare provision -p project.rendered.yml
)
