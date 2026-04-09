# Tutorial 2: Dedicated Server + Native Clients

Use this when each participating site can run an NVFlare client that opens an outbound connection to the server.

This is the pattern to use for setups such as:

- server on NREC
- client on Snellius
- client on another reachable workstation or TRE host
- HuntCloud if firewall exceptions allow the outbound connection

## Topology

- one dedicated server host
- one client per participating site
- one admin console
- one provisioning run shared across all participants

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- create the NVFlare venv on the server host
- create the NVFlare venv on every client host
- choose one host for the admin console
- confirm each client host can open an outbound connection to the server FL port
- confirm the admin host can reach the server admin port
- activate the NVFlare venv in every shell used below

## Key Rules

- Use the server FQDN or stable IP in `project.yml`
- Pick explicit ports for FL traffic and admin traffic
- All participants must use kits from the same provisioning run
- Clients must be able to reach the server outbound on the chosen FL port

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
nvflare provision -p project.yml
```

Copy each client kit to its site, then start:

- server: `./start.sh`
- each client: `./start.sh`
- admin console: `./fl_admin.sh`

## Native-Site Checklist

- outbound connection from client host to `${SERVER_NAME}:${FL_PORT}`
- admin access to `${SERVER_NAME}:${ADMIN_PORT}`
- correct hostname in certificate and `project.yml`
- same `prod_00` kit set everywhere

## Common Issues

- connection immediately opens then closes: usually hostname or cert mismatch
- client cannot connect: usually blocked outbound port
- one site uses older kits: usually mixed provisioning runs

## When To Stop Using This Pattern

If a site will not allow the outbound NVFlare connection from inside the TRE, switch to the wrapper pattern instead of fighting the platform.
