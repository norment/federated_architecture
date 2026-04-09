# Hello Regression

Minimal federated analysis example with:

- no input data files to distribute
- deterministic per-site synthetic data generation
- custom client code
- custom server aggregation code

## Files

- `common.py`: deterministic data generation and regression math
- `site_runner.py`: site-local task that synthesizes one site's data and writes summary statistics as JSON
- `client.py`: NVFlare client script; calls `site_runner.py` through a subprocess
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

The subprocess call inside `client.py` is the wrapper boundary. For a real TRE wrapper, replace that local subprocess with TSD, DX, or another site API call.
