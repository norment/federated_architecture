# Hello Regression

Minimal federated analysis example with:

- no input data files to distribute
- deterministic per-site synthetic data generation
- custom client code
- custom server aggregation code

## Files

- `common.py`: deterministic data generation and regression math
- `site_runner.py`: shared site-local task used by local, TSD, and DX executors
- `client.py`: NVFlare client script; dispatches to either the local subprocess runner, the TSD wrapper, or the DX wrapper
- `tsd_wrapper.py`: thin `hello_regression` adapter that describes which files to ship, which remote command to run, and how to parse the result
- `dx_wrapper.py`: thin `hello_regression` adapter for DNAnexus / UKB RAP
- `tsd_wrapper_config.yml.template`: template for non-secret per-site TSD wrapper settings such as username, paths, and Slurm account
- `dx_wrapper_config.yml.template`: template for non-secret per-site DX wrapper settings such as RAP project and instance type
- `../../scripts/make_tsd_site_config.py`: helper that creates a site-specific config from the template
- `../../scripts/make_dx_site_config.py`: helper that creates a site-specific DX config from the template
- `../../tre_wrappers/tsd.py`: reusable TSD transport used by example-specific adapters
- `../../tre_wrappers/dx.py`: reusable DX transport used by example-specific adapters
- `job.py`: launches the federated run and aggregates site-level sufficient statistics into one global regression

## Analysis

Each site generates its own synthetic dataset for:

`outcome ~ age + sex + exposure`

The client does not send rows back to the server. It sends only:

- `X'X`
- `X'y`
- `y'y`
- `n`

The server sums these across sites and solves the global linear regression.

## Why This Example Exists

This is the shared example used by all three tutorials:

- tutorial 1: `sim` on one machine
- tutorial 2: `prod` with native multi-site deployment
- tutorial 3: `poc` workspace with wrapper clients

The executor selection inside `client.py` is the wrapper boundary. Set `HELLO_REGRESSION_EXECUTOR` explicitly before starting each client process: use `local` for tutorials 1 and 2, `tsd` for TSD wrapper clients, and `dx` for RAP wrapper clients. Wrapper clients also require an explicit site config path: `HELLO_REGRESSION_TSD_CONFIG=/path/to/site.yml` or `HELLO_REGRESSION_DX_CONFIG=/path/to/site.yml`. The TSD path is split into a reusable transport in `tre_wrappers/tsd.py` and an example adapter in `tsd_wrapper.py`. The DX path follows the same pattern with `tre_wrappers/dx.py` and `dx_wrapper.py`. All three executors use the same `site_runner.py` and `common.py` logic for local-stat generation; `common.py` keeps that site-side path stdlib-only so RAP does not need `numpy` just to run the tutorial.

`job.py --env` means the NVFlare execution environment used to launch or submit the job:

- `sim`: run in the simulator with explicit `--clients`
- `prod`: submit to already running server/client/admin startup kits
- `poc`: let NVFlare manage a local POC workspace directly

The checked-in tutorials still use:

- tutorial 1: `job.py --env sim`
- tutorial 2: `job.py --env prod`
- tutorial 3: helper-managed `poc` workspace, then `job.py --env prod` against that live local workspace
