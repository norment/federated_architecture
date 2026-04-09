# Prerequisites

These are the baseline requirements before you attempt any tutorial in this repo.

## Common Requirements

- a Linux shell with `bash`
- Python 3 with `venv`
- network access appropriate for your chosen setup
- enough shell sessions to keep server, clients, and admin running at the same time

## Create An NVFlare Virtual Environment

Create one venv on each machine that will run NVFlare:

```bash
python3 -m venv ~/venvs/nvflare
source ~/venvs/nvflare/bin/activate
python -m pip install --upgrade pip
pip install nvflare
nvflare --version
```

If `python3 -m venv` fails, install the system package that provides `venv` first.

Examples:

- Ubuntu or Debian: `sudo apt install python3-venv`
- RHEL-compatible systems: install the Python 3 venv package used by your distribution

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
- one shell for the wrapper client
- one shell for the admin console

You may also need site-specific tools such as `tacl` or `dx`.

## Site-Specific Dependencies

### Native NVFlare Tutorials

Tutorials 1 and 2 only require NVFlare plus standard shell tools.

### Wrapper Tutorials

Tutorial 3 depends on the target TRE:

- TSD: `tacl`, TSD project registration, VPN or whitelisted IP, OTP access
- UKB RAP / DNAnexus: `dx` tooling and RAP permissions

See:

- [TSD](sites/tsd.md)
- [UK Biobank RAP / DNAnexus](sites/ukb-rap.md)

## Before You Start A Real Multi-Site Run

- confirm which host will run the server
- confirm which sites are native and which need wrappers
- confirm required ports and outbound connectivity
- confirm who starts each client
- confirm who has account and 2FA access at each site
