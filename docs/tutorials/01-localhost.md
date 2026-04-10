# Tutorial 1: Single-Host Hello World

## Goal

Run the checked-in `hello_regression` example entirely on one machine.

The example synthesizes site-local data inside the client code, so no CSV or other input files need to be copied anywhere.

Suggested mode: `sim`.

Tutorial 1 is the quick local validation path. If you want to exercise real NVFlare server and client processes, move to tutorial 2 and use `--env prod`.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

Fastest first run:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
python examples/hello_regression/job.py --env sim --n_clients 2
```

Run that from the repository root. The manual provisioning below is only to inspect the server/client/admin mechanics.

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- one machine with at least four shell sessions
- `hostname -f` should return a usable hostname on the local machine
- activate `~/venvs/nvflare` in every shell used in this tutorial

## Copy The Checked-In Template

```bash
mkdir -p ~/nvflare_local_demo
cp docs/tutorials/assets/01-localhost/.env.template ~/nvflare_local_demo/.env
cp docs/tutorials/assets/01-localhost/project.yml ~/nvflare_local_demo/project.yml
cd ~/nvflare_local_demo
```

Edit `.env` and set at least:

- `SERVER_NAME`
- `FL_PORT` and `ADMIN_PORT` only if `8002` or `8003` are already in use on this machine
- participant names only if you want different labels than `site-a`, `site-b`, and `admin@demo.org`

The checked-in files are:

- [docs/tutorials/assets/01-localhost/.env.template](assets/01-localhost/.env.template)
- [docs/tutorials/assets/01-localhost/project.yml](assets/01-localhost/project.yml)
- [scripts/provision_from_env.sh](../../scripts/provision_from_env.sh)

The checked-in `project.yml` is a template. Use the helper script below rather than passing it directly to `nvflare provision`.

## Provision

From the repository root, activate your Python environment, then provision with the helper script:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
./scripts/provision_from_env.sh ~/nvflare_local_demo
```

## Start Components

Server shell:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd ~/nvflare_local_demo
set -a
source .env
set +a
cd workspace/${PROJECT_NAME}/prod_00/${SERVER_NAME}/startup
./start.sh
```

Client `site-a` shell:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd ~/nvflare_local_demo
set -a
source .env
set +a
cd workspace/${PROJECT_NAME}/prod_00/${CLIENT_A_NAME}/startup
./start.sh
```

Client `site-b` shell:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd ~/nvflare_local_demo
set -a
source .env
set +a
cd workspace/${PROJECT_NAME}/prod_00/${CLIENT_B_NAME}/startup
./start.sh
```

Admin shell:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd ~/nvflare_local_demo
set -a
source .env
set +a
cd workspace/${PROJECT_NAME}/prod_00/${ADMIN_NAME}/startup
./fl_admin.sh
```

Inside the admin console:

```text
check_status server
check_status client
```

If the infrastructure looks correct, move on to tutorial 2 and run the same `hello_regression` example against real server and client processes.
