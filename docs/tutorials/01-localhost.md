# Tutorial 1: Single-Host Hello World

## Goal

Run the checked-in `hello_regression` example entirely on one machine.

The example synthesizes site-local data inside the client code, so no CSV or other input files need to be copied anywhere.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

Fastest first run:

```bash
source ~/venvs/nvflare/bin/activate
python examples/hello_regression/job.py --env sim --n_clients 2
```

Run that from the repository root. The manual provisioning below is only to inspect the server/client/admin mechanics.

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- one machine with at least four shell sessions
- `hostname -f` should return a usable hostname on the local machine
- activate `~/venvs/nvflare` in every shell used in this tutorial

## Create A Minimal Project

```bash
export SERVER_NAME="$(hostname -f)"
export FL_PORT=29002
export ADMIN_PORT=29003
mkdir -p ~/nvflare_local_demo
cd ~/nvflare_local_demo
```

Create `project.yml`:

```yaml
api_version: 3
name: local_demo
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
nvflare provision -p project.yml
```

## Start Components

Server shell:

```bash
source ~/venvs/nvflare/bin/activate
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/${SERVER_NAME}/startup
./start.sh
```

Client `site-a` shell:

```bash
source ~/venvs/nvflare/bin/activate
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/site-a/startup
./start.sh
```

Client `site-b` shell:

```bash
source ~/venvs/nvflare/bin/activate
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/site-b/startup
./start.sh
```

Admin shell:

```bash
source ~/venvs/nvflare/bin/activate
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/admin\@demo.org/startup
./fl_admin.sh
```

Inside the admin console:

```text
check_status server
check_status client
```

If the infrastructure looks correct, move on to tutorial 2 and run the same `hello_regression` example against real server and client processes.
