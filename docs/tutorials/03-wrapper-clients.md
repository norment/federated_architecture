# Tutorial 3: Wrapper Clients For TRE Sites

## Goal

Use the same checked-in `hello_regression` example as tutorials 1 and 2, but run the NVFlare server and all wrapper clients on the same non-TRE host and let each client delegate site work through its site API.

Suggested mode: `sim` for wrapper development and validation.

Tutorial 3 is mainly about exercising the wrapper logic itself. Start with `--env sim` when you want to validate the TSD or DX integration. Use the local `prod` setup in this tutorial only when you specifically want to inspect the full local server/client/admin NVFlare topology around those wrappers.

The implementation supports running any subset of the configured wrapper clients, but this tutorial walks through the full three-site setup.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/tsd_wrapper.py](../../examples/hello_regression/tsd_wrapper.py)
- [examples/hello_regression/dx_wrapper.py](../../examples/hello_regression/dx_wrapper.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

The important point is that `client.py` does not compute the local statistics itself. For tutorial 3, each client process uses a site-specific wrapper and delegates the site-local work through that site's API.

## Topology

- one non-TRE host runs the NVFlare server
- that same host also runs one NVFlare wrapper client per wrapped site
- each wrapper client calls its TRE-specific API
- the TRE runs the local analysis internally
- the wrapper client downloads summary statistics and sends them back to the NVFlare server

This tutorial walks through three local wrapper clients:

- `p33` -> TSD project `p33`
- `p697` -> TSD project `p697`
- `ukb-rap` -> UKB RAP / DNAnexus project configured in `dx-configs/ukb-rap.yml`

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- create `~/venvs/nvflare` on the non-TRE host that will run both the server and the wrapper clients
- make sure that host can reach `api.tsd.usit.no`
- have TSD access ready for both `p33-ofrei` and `p697-ofrei` or the equivalent users you will test with
- have DX access ready for the RAP project you will test with

Unlike tutorial 2, tutorial 3 does not require a public FL endpoint. The NVFlare server, wrapper clients, and admin shell all run on the same local host, and only the wrapper logic talks to remote site APIs.

Use these setup sections directly:

- [TSD prerequisites](../sites/tsd.md#prerequisites)
- [TSD priming](../sites/tsd.md#priming)
- [UKB RAP / DNAnexus prerequisites](../sites/ukb-rap.md#prerequisites)
- [UKB RAP / DNAnexus priming](../sites/ukb-rap.md#priming)

## Happy Path

Recommended first check for tutorial 3 is a `sim` run that still exercises the wrapper code path. The helper script now generates `sim-site-map.json`, so `submit` can route simulated clients to the right wrapper backend and site config.

For example, after priming and initializing the workspace, run:

```bash
source ~/venvs/nvflare/bin/activate
./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo --n_clients 3
```

That default `submit` path uses `--env sim`.

If you want to inspect the full local NVFlare topology with real server, client, and admin processes, use the same helper with `--env prod` and start the local processes in separate terminals as shown below.

From the repository root:

```bash
source ~/venvs/nvflare/bin/activate

./scripts/prime_tsd_session.sh --username p33-ofrei
./scripts/prime_tsd_session.sh --username p697-ofrei
./scripts/prime_dx_session.sh --project project-REDACTED1234567890EXAMPLE

./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo \
  --p33-user p33-ofrei \
  --p697-user p697-ofrei \
  --dx-project project-REDACTED1234567890EXAMPLE
```

That one `init` command:

- copies the checked-in tutorial assets
- provisions the local NVFlare workspace
- creates `~/nvflare_wrapper_demo/tsd-configs/p33.yml`
- creates `~/nvflare_wrapper_demo/tsd-configs/p697.yml`
- creates `~/nvflare_wrapper_demo/dx-configs/ukb-rap.yml`

Optional `prod` walkthrough for the same three-site setup:

Open five terminals on the same host:

Server:

```bash
source ~/venvs/nvflare/bin/activate
./scripts/tutorial3_local.sh start-server ~/nvflare_wrapper_demo
```

Wrapper client A (`p33`):

```bash
source ~/venvs/nvflare/bin/activate
./scripts/tutorial3_local.sh start-client-a ~/nvflare_wrapper_demo
```

Wrapper client B (`p697`):

```bash
source ~/venvs/nvflare/bin/activate
./scripts/tutorial3_local.sh start-client-b ~/nvflare_wrapper_demo
```

Wrapper client C (`ukb-rap`):

```bash
source ~/venvs/nvflare/bin/activate
./scripts/tutorial3_local.sh start-client-c ~/nvflare_wrapper_demo
```

Admin console:

```bash
source ~/venvs/nvflare/bin/activate
./scripts/tutorial3_local.sh start-admin ~/nvflare_wrapper_demo
```

Submit the job:

```bash
source ~/venvs/nvflare/bin/activate
./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo --env prod --n_clients 3
```

The downloaded result bundle ends up under:

```bash
~/nvflare_wrapper_demo/workspace/wrapper_three_sites/prod_00/admin@demo.org/transfer/<job-id>/
```

The main output for this example is:

```bash
~/nvflare_wrapper_demo/workspace/wrapper_three_sites/prod_00/admin@demo.org/transfer/<job-id>/workspace/server_results/hello_regression_summary.json
```

## Fixed Tutorial Defaults

This tutorial uses checked-in defaults:

- server name: `localhost`
- FL port: `8002`
- admin port: `8003`
- wrapper client names: `p33`, `p697`, and `ukb-rap`

You normally do not need to edit either `.env` or `project.yml`.

The checked-in files used by `init` are:

- [docs/tutorials/assets/03-wrapper-clients/.env.template](assets/03-wrapper-clients/.env.template)
- [docs/tutorials/assets/03-wrapper-clients/project.yml](assets/03-wrapper-clients/project.yml)
- [scripts/tutorial3_local.sh](../../scripts/tutorial3_local.sh)

## Notes

- `init` derives `project`, `slurm_account`, and standard TSD paths from the usernames you pass.
- `init` also writes `sim-site-map.json`, which maps `site-1`, `site-2`, and `site-3` to the configured wrapper backends for tutorial-3 `sim` runs.
- `start-client-a` and `start-client-b` export `HELLO_REGRESSION_EXECUTOR=tsd` automatically.
- `init` writes the DX project you pass into `dx-configs/ukb-rap.yml`.
- `start-client-c` exports `HELLO_REGRESSION_EXECUTOR=dx` automatically.
- TSD flow: [TSD](../sites/tsd.md)
- UKB RAP / DNAnexus flow: [UK Biobank RAP / DNAnexus](../sites/ukb-rap.md)

## Reduced Setups

The same implementation also supports running a reduced subset of wrapper clients.

General rule:

- start only the client processes you want to use
- pass only the site options you want to `tutorial3_local.sh init`
- submit with `--n_clients` set to the number of active wrapper clients

Examples:

- DX only:

```bash
./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo_dx \
  --dx-project project-REDACTED1234567890EXAMPLE

./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo_dx --n_clients 1
```

- One TSD site only:

```bash
./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo_p33 \
  --p33-user p33-yourusername

./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo_p33 --n_clients 1
```

- Two TSD sites only:

```bash
./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo_tsd \
  --p33-user p33-yourusername \
  --p697-user p697-yourusername

./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo_tsd --n_clients 2
```
