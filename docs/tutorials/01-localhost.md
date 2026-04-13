# Tutorial 1: Single-Host Hello World

## Goal

Run the checked-in `hello_regression` example entirely on one machine.

The example synthesizes site-local data inside the client code, so no CSV or other input files need to be copied anywhere.

Mode: `sim`.

Tutorial 1 is the quick local validation path. The main goal is to prove that the example job itself works before you introduce startup kits, certificates, host-to-host connectivity, or copied client/admin kits.

The next tutorial switches to live provisioned processes in `prod`.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

Fastest first run:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
HELLO_REGRESSION_EXECUTOR=local \
python examples/hello_regression/job.py --env sim --clients site-a site-b
```

Run that from the repository root. The optional one-host `prod` preview below is only to inspect the server/client/admin mechanics.

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- one machine with at least four shell sessions
- `hostname -f` should return a usable hostname on the local machine
- activate `~/venvs/nvflare` in every shell used in this tutorial

## What Success Looks Like

If the run succeeds, `job.py` prints lines like:

```text
Wrote summary to .../hello_regression_summary.json
Job status: FINISHED_COMPLETED
```

The summary JSON contains the aggregated regression output for `site-a` and `site-b`.

## Why Start With `sim`

Tutorial 1 intentionally stays in `sim` mode.

That keeps the first run focused on:

- the checked-in example code
- the expected client list
- the final result bundle

It deliberately avoids the extra moving parts used in `prod`:

- provisioning startup kits
- certificate and hostname matching
- copying client/admin kits between hosts
- starting separate live server, client, and admin processes

Jumping from tutorial 1 in `sim` to tutorial 2 in `prod` is a reasonable progression, as long as the reader understands that tutorial 2 adds deployment mechanics rather than changing the `hello_regression` analysis itself.

## Optional: Preview What Changes In `prod`

If you want an intermediate bridge before tutorial 2, the main differences are:

- you provision startup kits from `project.yml` and `.env`
- you start a real server process, real client processes, and an admin shell
- you run `job.py --env prod` instead of `job.py --env sim`
- you submit the job with an admin startup kit instead of using the simulator directly

The same shared example files are still used:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

On one machine, that looks like this:

## Optional: One-Host `prod` Preview

This is not the main tutorial path. It is only here to show what tutorial 2 adds operationally.

### Copy The Checked-In Template

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

### Provision

From the repository root, activate your Python environment, then provision with the helper script:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
./scripts/provision_from_env.sh ~/nvflare_local_demo
```

### Start Components

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
export HELLO_REGRESSION_EXECUTOR=local
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
export HELLO_REGRESSION_EXECUTOR=local
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

To submit the job in this preview flow:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
python examples/hello_regression/job.py \
  --env prod \
  --clients site-a site-b \
  --startup_kit ~/nvflare_local_demo/workspace/${PROJECT_NAME}/prod_00/${ADMIN_NAME} \
  --username ${ADMIN_NAME}
```

If the infrastructure looks correct, move on to tutorial 2 and run the same `hello_regression` example against real server and client processes on the actual multi-host topology.
