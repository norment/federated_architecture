# Tutorial 2: Public FL Endpoint + Native Clients

## Goal

Run the same checked-in `hello_regression` example as tutorial 1, but against a real NVFlare server and real NVFlare clients.

Suggested mode: `prod`.

For tutorial 2, the requirement is a publicly reachable FL endpoint. The server process can run on:

- a dedicated public machine
- or your local machine behind stable TCP forwarding such as `ngrok tcp 8002`

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

The client synthesizes site-local data from the site name. No data files need to be copied to the clients.

This is the tutorial where running `examples/hello_regression/job.py --env prod ...` makes the most sense, because the point is to exercise the real provisioned server, client, and admin startup kits.

## Topology

- one public FL endpoint for the server
- one machine that runs the server process
- one client per participating site
- one admin startup kit
- one provisioning run shared across all participants

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- choose one public FL endpoint option from [tutorial 2 server endpoint options](02-server-endpoint-options.md)
- create `~/venvs/nvflare` on the machine that will run the server process
- create `~/venvs/nvflare` on every client host
- choose one machine that has the admin startup kit
- confirm each client host can open an outbound connection to the public FL endpoint
- confirm the admin host can reach the server admin port if admin will not run locally on the server machine

## Copy The Checked-In Template

From the repository root on the machine that will run the server process:

```bash
mkdir -p ~/nvflare_two_sites
cp docs/tutorials/assets/02-dedicated-server-native-clients/.env.template ~/nvflare_two_sites/.env
cp docs/tutorials/assets/02-dedicated-server-native-clients/project.yml ~/nvflare_two_sites/project.yml
cd ~/nvflare_two_sites
```

Edit `.env` and set at least:

- `SERVER_NAME` to the public hostname or IP that clients will actually dial
- `LOCAL_FL_PORT` to the port the server process listens on locally, usually `8002`
- `PUBLIC_FL_PORT` to the public FL port that clients will actually dial
- `ADMIN_PORT` only if another service already uses `8003` on the server machine
- `ADMIN_HOST`, usually `localhost`
- client and admin names only if you want different labels

The checked-in files are:

- [docs/tutorials/assets/02-dedicated-server-native-clients/.env.template](assets/02-dedicated-server-native-clients/.env.template)
- [docs/tutorials/assets/02-dedicated-server-native-clients/project.yml](assets/02-dedicated-server-native-clients/project.yml)
- [scripts/provision_from_env.sh](../../scripts/provision_from_env.sh)
- [tutorial 2 server endpoint options](02-server-endpoint-options.md)

The checked-in `project.yml` is a template. Use the helper script below rather than passing it directly to `nvflare provision`.

## Provision

From the repository root, activate your Python environment, then provision with the helper script:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
./scripts/provision_from_env.sh ~/nvflare_two_sites
```

## Start Server And Clients

Server process host:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd ~/nvflare_two_sites
set -a
source .env
set +a
cd workspace/${PROJECT_NAME}/prod_00/${SERVER_NAME}/startup
./start.sh
```

Each client:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd /path/to/copied/client-kit/startup
./start.sh
```

Optional admin status check:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd /path/to/copied/admin-kit/startup
./fl_admin.sh
```

Inside the admin console:

```text
check_status server
check_status client
```

## Run The Shared Example

From the repository root on a machine that has the admin startup kit:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
python examples/hello_regression/job.py \
  --env prod \
  --n_clients 2 \
  --startup_kit /path/to/copied/admin-kit \
  --username <admin-name-from-.env>
```

That submits the same custom client and custom server code used in tutorial 1, but against real server and client processes.

The client and admin startup kits come from `~/nvflare_two_sites/workspace/${PROJECT_NAME}/prod_00/` on the server host after provisioning.

If you keep the default template values, the admin name is `admin@demo.org`.

You do not put SSH passwords, site account credentials, or 2FA material into `.env` or `project.yml`. Those are used only when you log in to hosts and copy the startup kits.

The startup kits themselves contain NVFlare certificates and private keys, so handle them as sensitive deployment files.

## Common Issues

- connection immediately opens then closes: hostname or certificate mismatch
- client cannot connect: public FL endpoint is not actually reachable from that client site
- using local machine plus port forwarding: `PUBLIC_FL_PORT` still points to the local server port instead of the public forwarded port
- multiple NVFlare servers on one host: assign a different free local admin port or local FL port as needed before forwarding
- one site uses older kits: mixed provisioning runs
- `hello_regression` prod run fails before submission: `--startup_kit` points to the wrong directory

## Next Step

If a site cannot make the outbound NVFlare connection, keep the same `hello_regression` server-side code and move to tutorial 3.
