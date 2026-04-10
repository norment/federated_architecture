# Tutorial 3: Wrapper Clients For TRE Sites

## Goal

Use the same checked-in `hello_regression` example as tutorials 1 and 2, but run the NVFlare server and the wrapper clients on the same non-TRE host and treat the client-side subprocess boundary as the TRE wrapper boundary.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

The important point is that `client.py` does not compute the local statistics itself. It shells out to `site_runner.py`. For a real wrapper, replace that subprocess call with a concrete TRE API call such as TSD HPC API or `dx`.

## Topology

- one non-TRE host runs the NVFlare server
- that same host also runs one NVFlare wrapper client per wrapped site
- each wrapper client calls its TRE-specific API
- the TRE runs the local analysis internally
- the wrapper client downloads summary statistics and sends them back to the NVFlare server

This tutorial focuses only on the wrapper pattern. Combining NVFlare-native sites from tutorial 2 with wrapper clients from tutorial 3 is possible, but not shown here.

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- create `~/venvs/nvflare` on the non-TRE host that will run both the server and the wrapper clients
- make sure that host can reach the target TRE API endpoints
- install the TRE-specific dependencies described in [TSD](../sites/tsd.md) or [UK Biobank RAP / DNAnexus](../sites/ukb-rap.md)
- have the required credentials ready before you start

For the concrete examples in this tutorial:

- TSD wrapper:
  - `tacl`
  - TSD credentials
  - OTP access
  - the wrapper host must be whitelisted for the TSD project
  - a TSD project admin should request that whitelisting by contacting `tsd-drift@usit.uio.no`
- UKB RAP / DX wrapper:
  - `dx`
  - RAP permissions
  - credentials for the RAP project or workspace used by the wrapper

## Copy The Checked-In Template

From the repository root on the non-TRE host that will run both server and wrapper clients:

```bash
mkdir -p ~/nvflare_wrapper_demo
cp docs/tutorials/assets/03-wrapper-clients/.env.template ~/nvflare_wrapper_demo/.env
cp docs/tutorials/assets/03-wrapper-clients/project.yml ~/nvflare_wrapper_demo/project.yml
cd ~/nvflare_wrapper_demo
```

Edit `.env` and set at least:

- `SERVER_NAME`
- `FL_PORT` and `ADMIN_PORT` only if another service already uses `8002` or `8003` on the server host
- `WRAPPER_A_NAME` and `WRAPPER_B_NAME` if you want wrapper client names that match your real sites

The checked-in files are:

- [docs/tutorials/assets/03-wrapper-clients/.env.template](assets/03-wrapper-clients/.env.template)
- [docs/tutorials/assets/03-wrapper-clients/project.yml](assets/03-wrapper-clients/project.yml)
- [scripts/provision_from_env.sh](../../scripts/provision_from_env.sh)

The checked-in `project.yml` is a template. Use the helper script below rather than passing it directly to `nvflare provision`.

## Provision

From the repository root, activate your Python environment, then provision with the helper script:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
./scripts/provision_from_env.sh ~/nvflare_wrapper_demo
```

## Local Development Run

Before wiring in a real TRE API, run the shared example locally on that same host:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
python examples/hello_regression/job.py --env sim --n_clients 2
```

Run that from the repository root. It proves the server aggregation and the subprocess-based client boundary work before you add TSD HPC API or `dx`.

## Start Server And Wrapper Clients On The Same Host

Server:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd ~/nvflare_wrapper_demo
set -a
source .env
set +a
cd workspace/${PROJECT_NAME}/prod_00/${SERVER_NAME}/startup
./start.sh
```

Each wrapper client on the same host:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd /path/to/local/wrapper-client-kit/startup
./start.sh
```

Admin console:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
cd /path/to/copied/admin-kit/startup
./fl_admin.sh
```

From the repository root on the same host:

```bash
source ~/venvs/nvflare/bin/activate  # or activate your equivalent Python env
python examples/hello_regression/job.py \
  --env prod \
  --n_clients 2 \
  --startup_kit /path/to/copied/admin-kit \
  --username <admin-name-from-.env>
```

## Wrapper Contract

Keep the same server-side aggregation in [examples/hello_regression/job.py](../../examples/hello_regression/job.py). In the client, replace the local subprocess with:

1. upload code or parameters into the TRE
2. submit the TRE-side job
3. wait for completion
4. download the JSON summary statistics
5. send those summary statistics back to NVFlare

Concrete examples:

- TSD wrapper: upload input bundle, submit through TSD HPC API, wait, download the JSON summary
- UKB RAP wrapper: run the prepared `dx` command, wait, download the JSON summary

The return payload should stay the same as the local example:

- `site_name`
- `n`
- `x_tx`
- `x_ty`
- `y_ty`

## Site-Specific References

- TSD flow: [TSD](../sites/tsd.md)
- UKB RAP / DX flow: [UK Biobank RAP / DNAnexus](../sites/ukb-rap.md)

## What Stays Shared Across Sites

- regression math in `examples/hello_regression/common.py`
- server aggregation in `examples/hello_regression/job.py`
- JSON payload format returned by the client

## What Changes Per TRE

- authentication
- upload and download paths
- job submission command
- polling method
- output retrieval
- credential refresh or token refresh behavior

The wrapper client and admin startup kits come from `~/nvflare_wrapper_demo/workspace/${PROJECT_NAME}/prod_00/` on the same non-TRE host after provisioning.

If you keep the default template values, the admin name is `admin@demo.org`.
