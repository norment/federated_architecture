# Tutorial 1: Single-Host Hello World

Use this first. It proves that your local NVFlare install, provisioning flow, startup kits, and admin workflow all work before you involve real sites.

## Goal

Run one server, two clients, and one admin on a single machine.

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- one machine with at least four shell sessions
- `hostname -f` should return a usable hostname on the local machine
- activate the NVFlare venv in every shell used in this tutorial

## Create A Minimal Project

Choose a hostname that resolves on your machine:

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

```bash
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/${SERVER_NAME}/startup
./start.sh
```

In another shell:

```bash
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/site-a/startup
./start.sh
```

In a third shell:

```bash
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/site-b/startup
./start.sh
```

In a fourth shell:

```bash
cd ~/nvflare_local_demo/workspace/local_demo/prod_00/admin\@demo.org/startup
./fl_admin.sh
```

Inside the admin console:

```text
check_status server
check_status client
```

## Submit A Tiny Job

Outside the admin console:

```bash
nvflare job create -w sag_cross_np -j ~/nvflare_local_demo/my_first_job
```

Back in the admin console:

```text
submit_job /home/$USER/nvflare_local_demo/my_first_job
list_jobs
download_job <job_id>
```

## Stop Everything

Inside the admin console:

```text
shutdown client site-a
shutdown client site-b
shutdown server
bye
```

If this works, move on to a real server plus remote clients.
