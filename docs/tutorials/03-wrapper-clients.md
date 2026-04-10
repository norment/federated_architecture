# Tutorial 3: Wrapper Clients For TRE Sites

## Goal

Use the same checked-in `hello_regression` example as tutorials 1 and 2, but run the NVFlare server and both wrapper clients on the same non-TRE host and let each client delegate site work through the TSD APIs.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/tsd_wrapper.py](../../examples/hello_regression/tsd_wrapper.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

The important point is that `client.py` does not compute the local statistics itself. For tutorial 3, each client process uses the TSD wrapper and delegates the site-local work through TSD file API plus TSD HPC API.

## Topology

- one non-TRE host runs the NVFlare server
- that same host also runs one NVFlare wrapper client per wrapped site
- each wrapper client calls its TRE-specific API
- the TRE runs the local analysis internally
- the wrapper client downloads summary statistics and sends them back to the NVFlare server

This tutorial focuses on two local wrapper clients:

- `p33` -> TSD project `p33`
- `p697` -> TSD project `p697`

The same pattern also works with only one TSD site. In that case, run just one wrapper client and submit with `--n_clients 1`.

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- complete [tutorial 3 prerequisites](03-local-wrapper-prerequisites.md)
- create `~/venvs/nvflare_tutorial3` on the non-TRE host that will run both the server and the wrapper clients
- make sure that host can reach `api.tsd.usit.no`
- have TSD access ready for both `p33-ofrei` and `p697-ofrei` or the equivalent users you will test with

Unlike tutorial 2, tutorial 3 does not require a public FL endpoint. The NVFlare server, wrapper clients, and admin shell all run on the same local host, and only the wrapper logic talks to remote site APIs.

## Happy Path

From the repository root:

```bash
source ~/venvs/nvflare_tutorial3/bin/activate

./scripts/prime_tsd_session.sh --username p33-ofrei
./scripts/prime_tsd_session.sh --username p697-ofrei

./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo \
  --p33-user p33-ofrei \
  --p697-user p697-ofrei
```

That one `init` command:

- copies the checked-in tutorial assets
- provisions the local NVFlare workspace
- creates `~/nvflare_wrapper_demo/tsd-configs/p33.yml`
- creates `~/nvflare_wrapper_demo/tsd-configs/p697.yml`

Then open four terminals on the same host:

Server:

```bash
source ~/venvs/nvflare_tutorial3/bin/activate
./scripts/tutorial3_local.sh start-server ~/nvflare_wrapper_demo
```

Wrapper client A (`p33`):

```bash
source ~/venvs/nvflare_tutorial3/bin/activate
./scripts/tutorial3_local.sh start-client-a ~/nvflare_wrapper_demo
```

Wrapper client B (`p697`):

```bash
source ~/venvs/nvflare_tutorial3/bin/activate
./scripts/tutorial3_local.sh start-client-b ~/nvflare_wrapper_demo
```

Admin console:

```bash
source ~/venvs/nvflare_tutorial3/bin/activate
./scripts/tutorial3_local.sh start-admin ~/nvflare_wrapper_demo
```

Submit the job:

```bash
source ~/venvs/nvflare_tutorial3/bin/activate
./scripts/tutorial3_local.sh submit ~/nvflare_wrapper_demo --n_clients 2
```

The downloaded result bundle ends up under:

```bash
~/nvflare_wrapper_demo/workspace/wrapper_two_sites/prod_00/admin@demo.org/transfer/<job-id>/
```

The main output for this example is:

```bash
~/nvflare_wrapper_demo/workspace/wrapper_two_sites/prod_00/admin@demo.org/transfer/<job-id>/workspace/server_results/hello_regression_summary.json
```

## Fixed Tutorial Defaults

This tutorial uses checked-in defaults:

- server name: `localhost`
- FL port: `8002`
- admin port: `8003`
- wrapper client names: `p33` and `p697`

You normally do not need to edit either `.env` or `project.yml`.

The checked-in files used by `init` are:

- [docs/tutorials/assets/03-wrapper-clients/.env.template](assets/03-wrapper-clients/.env.template)
- [docs/tutorials/assets/03-wrapper-clients/project.yml](assets/03-wrapper-clients/project.yml)
- [scripts/tutorial3_local.sh](../../scripts/tutorial3_local.sh)

If you want to test only one TSD site, you can still run only `p33`, start only client A, and submit with `--n_clients 1`.

## Notes

- `init` derives `project`, `slurm_account`, and standard TSD paths from the usernames you pass.
- `start-client-a` and `start-client-b` export `HELLO_REGRESSION_EXECUTOR=tsd` automatically.
- tutorial 3 setup assumptions: [tutorial 3 prerequisites](03-local-wrapper-prerequisites.md)
- TSD flow: [TSD](../sites/tsd.md)
