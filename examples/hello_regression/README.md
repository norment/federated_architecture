# Hello Regression

Minimal federated analysis example with:

- no input data files to distribute
- deterministic per-site synthetic data generation
- custom client code
- custom server aggregation code

## Files

- `common.py`: deterministic data generation and regression math
- `site_runner.py`: site-local task that synthesizes one site's data and writes summary statistics as JSON
- `client.py`: NVFlare client script; dispatches to either the local subprocess runner or the TSD wrapper
- `tsd_wrapper.py`: thin `hello_regression` adapter that describes which files to ship, which remote command to run, and how to parse the result
- `tsd_wrapper_config.yml.template`: template for non-secret per-site TSD wrapper settings such as username, paths, and Slurm account
- `../../scripts/make_tsd_site_config.py`: helper that creates a site-specific config from the template
- `../../tre_wrappers/tsd.py`: reusable TSD transport used by example-specific adapters
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

- tutorial 1: simulation on one machine
- tutorial 2: native multi-site deployment
- tutorial 3: wrapper pattern

The executor selection inside `client.py` is the wrapper boundary. The default executor is still the local subprocess path. The TSD path is now split into a reusable transport in `tre_wrappers/tsd.py` and an example adapter in `tsd_wrapper.py`. For real TSD runs, each wrapper client uses a site-specific config copied from `tsd_wrapper_config.yml.template`. If you place files like `tsd-configs/<site-name>.yml` near the wrapper workspace, the adapter auto-discovers them.
