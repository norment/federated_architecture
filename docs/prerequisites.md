# Prerequisites

These are the baseline requirements before you attempt any tutorial in this repo.

## Common Requirements

- a Linux shell with `bash`
- Python 3
- network access appropriate for your chosen setup
- enough shell sessions to keep server, clients, and admin running at the same time

## Python Environment

You need a Python environment with at least:

- `nvflare`
- `numpy`

How you get that environment depends on the platform:

- local workstation: `python -m venv`
- HPC: `module load ...` plus a virtual environment, or a Conda or Miniconda environment
- managed research platform: whatever site-approved Python environment mechanism is available

The important part is not the tool. The important part is that the shell where you run NVFlare commands has a working Python with `nvflare` and `numpy` installed.

The tutorials that use checked-in `.env.template` files also use [`scripts/provision_from_env.sh`](../scripts/provision_from_env.sh), which expects `envsubst` to be available.

For tutorial 3, use the same environment and add the lightweight wrapper dependencies:

- `tsd-api-client`
- `dxpy`

## One Example: local venv

Create one venv on each machine that will run NVFlare:

```bash
python3 -m venv ~/venvs/nvflare
source ~/venvs/nvflare/bin/activate
python -m pip install --upgrade pip
pip install nvflare numpy tsd-api-client dxpy
nvflare --version
```

If `python3 -m venv` is not available on your platform, use another site-approved Python environment method instead of assuming `sudo`.

## Which Hosts Need Python + NVFlare?

### Native NVFlare deployment

You need Python + NVFlare on:

- the server host
- every client host
- the machine where you run provisioning, `fl_admin.sh`, or `examples/hello_regression/job.py`

If the admin shell runs on the same machine as the server, that is not an extra host.

Tutorial 2 also needs a publicly reachable FL endpoint for the server. See [tutorial 2 server endpoint options](tutorials/02-server-endpoint-options.md).

## Port Roles

For the tutorials in this repo:

- clients need reachability to the FL server port
- the admin shell needs reachability to the admin port
- clients do not need reachability to the admin port
- these tutorials do not use a separate overseer port

Examples in this repo use:

- FL port: `8002`
- admin port: `8003`

If the server host already has another NVFlare deployment bound to those ports, choose another free port pair and replace them consistently in `project.yml` and in the connectivity checks below.

Port reachability is a network and firewall question, not a low-port versus high-port question. A port such as `29002` can be reachable from outside the host if that port is listening and the network path allows it.

## Check Client-To-Server Connectivity

Run these from the client host toward the server host, using the FL server port from your `project.yml`.

Example variables:

```bash
export SERVER_HOST=your.server.host
export FL_PORT=8002
```

Test raw TCP reachability with `curl`:

```bash
curl -v telnet://$SERVER_HOST:$FL_PORT
```

Test the TLS handshake on the FL port:

```bash
curl -vk https://$SERVER_HOST:$FL_PORT
```

For an NVFlare FL port, a successful handshake can still end with an empty or non-HTTP reply. That is fine. The useful signal is that the client can open the connection and reach the TLS endpoint.

If `nc` is available, you can also use:

```bash
nc -vz $SERVER_HOST $FL_PORT
```

Only the FL port needs to be reachable from client to server.

- do not test the admin port from the client unless the client host will also run `fl_admin.sh`
- do not assume a separate overseer port is needed for these tutorials

If you later add HA or an Overseer-based setup, that is a separate advanced configuration. See [advanced NVFlare notes](advanced-nvflare.md).

### Wrapper deployment

You need Python + NVFlare on:

- the server host
- the host that runs the wrapper clients
- the machine where you run provisioning, `fl_admin.sh`, or `examples/hello_regression/job.py`

In tutorial 3, the simplest pattern is to run the NVFlare server and the wrapper clients on the same non-TRE host.

You do not need NVFlare inside the TRE. The wrapper stays outside the TRE and talks to the TRE through its own API.

Tutorial 3 in this repo assumes a local-only NVFlare topology on one host. It does not require a public FL endpoint for the server. See [wrapper clients for TRE sites](tutorials/03-wrapper-clients.md), [TSD](sites/tsd.md), and [UK Biobank RAP / DNAnexus](sites/ukb-rap.md).

## How Many Shells Do You Need?

### Tutorial 1

Run on one machine with four shells:

- server
- client A
- client B
- admin console

### Tutorial 2

Run on multiple machines:

- one shell on server host
- one shell per client host
- one shell for admin console

### Tutorial 3

Run on at least:

- one shell for the NVFlare server
- one shell per wrapper client
- one shell for the admin console

You may also need site-specific tools such as `tacl` or `dx`.

## Site-Specific Dependencies

### Native NVFlare Tutorials

Tutorials 1 and 2 use the checked-in `examples/hello_regression` code and require:

- `nvflare`
- `numpy`
- standard shell tools

### Wrapper Tutorials

Tutorial 3 depends on the target TRE:

- TSD:
  - `tacl`
  - TSD project registration
  - credentials for the TSD project
  - OTP access
  - the external host that runs the wrapper must be whitelisted for the TSD project
  - for whitelisting, a TSD project admin should contact `tsd-drift@usit.uio.no`
- UKB RAP / DNAnexus:
  - `dx` tooling
  - RAP permissions
  - credentials for the RAP project or workspace used by the wrapper

See:

- [Wrapper clients for TRE sites](tutorials/03-wrapper-clients.md)
- [TSD](sites/tsd.md)
- [UK Biobank RAP / DNAnexus](sites/ukb-rap.md)

## Before You Start A Real Multi-Site Run

- confirm which host will run the server
- confirm which sites are native and which need wrappers
- confirm required ports and outbound connectivity
- confirm who starts each client
- confirm who has account and 2FA access at each site

## Handle Startup Kits As Sensitive Files

The generated NVFlare startup kits are not site login credentials, but they do contain NVFlare certificates and private keys for the participants.

Treat them as deployment secrets:

- copy them only to the intended hosts
- do not email them or put them in shared chat
- do not commit them to git
- remove them from temporary locations when the run is finished
