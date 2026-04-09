# Tutorial 2: Dedicated Server + Native Clients

## Goal

Run the same checked-in `hello_regression` example as tutorial 1, but against a real NVFlare server and real NVFlare clients.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

The client synthesizes site-local data from the site name. No data files need to be copied to the clients.

## Topology

- one dedicated server host
- one client per participating site
- one admin startup kit
- one provisioning run shared across all participants

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- create `~/venvs/nvflare` on the server host
- create `~/venvs/nvflare` on every client host
- choose one machine that has the admin startup kit
- confirm each client host can open an outbound connection to the server FL port
- confirm the admin host can reach the server admin port

## Minimal Provisioning Pattern

On the server host:

```bash
export SERVER_NAME="$(hostname -f)"
export FL_PORT=29002
export ADMIN_PORT=29003
mkdir -p ~/nvflare_two_sites
cd ~/nvflare_two_sites
```

Create `project.yml`:

```yaml
api_version: 3
name: native_two_sites
participants:
  - name: ${SERVER_NAME}
    type: server
    org: demo
    fed_learn_port: ${FL_PORT}
    admin_port: ${ADMIN_PORT}
  - name: site-a
    type: client
    org: demo
  - name: site-b
    type: client
    org: demo
  - name: admin@demo.org
    type: admin
    org: demo
    role: project_admin
builders:
  - path: nvflare.lighter.impl.workspace.WorkspaceBuilder
    args: { template_file: master_template.yml }
  - path: nvflare.lighter.impl.template.TemplateBuilder
  - path: nvflare.lighter.impl.static_file.StaticFileBuilder
    args:
      overseer_agent:
        path: nvflare.ha.dummy_overseer_agent.DummyOverseerAgent
        overseer_exists: false
        args:
          sp_end_point: ${SERVER_NAME}:${FL_PORT}:${ADMIN_PORT}
  - path: nvflare.lighter.impl.cert.CertBuilder
  - path: nvflare.lighter.impl.signature.SignatureBuilder
```

Provision:

```bash
source ~/venvs/nvflare/bin/activate
nvflare provision -p project.yml
```

## Start Server And Clients

Server:

```bash
source ~/venvs/nvflare/bin/activate
cd ~/nvflare_two_sites/workspace/native_two_sites/prod_00/${SERVER_NAME}/startup
./start.sh
```

Each client:

```bash
source ~/venvs/nvflare/bin/activate
cd /path/to/<site-name>/startup
./start.sh
```

Optional admin status check:

```bash
source ~/venvs/nvflare/bin/activate
cd /path/to/admin@demo.org/startup
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
source ~/venvs/nvflare/bin/activate
python examples/hello_regression/job.py \
  --env prod \
  --n_clients 2 \
  --startup_kit /path/to/admin@demo.org \
  --username admin@demo.org
```

That submits the same custom client and custom server code used in tutorial 1, but against real server and client processes.

## Common Issues

- connection immediately opens then closes: hostname or certificate mismatch
- client cannot connect: blocked outbound FL port
- one site uses older kits: mixed provisioning runs
- `hello_regression` prod run fails before submission: `--startup_kit` points to the wrong directory

## Next Step

If a site cannot make the outbound NVFlare connection, keep the same `hello_regression` server-side code and move to tutorial 3.
