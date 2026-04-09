# Tutorial 3: Wrapper Clients For TRE Sites

## Goal

Use the same checked-in `hello_regression` example as tutorials 1 and 2, but treat the client-side subprocess boundary as the TRE wrapper boundary.

## Shared Example

This tutorial uses:

- [examples/hello_regression/client.py](../../examples/hello_regression/client.py)
- [examples/hello_regression/site_runner.py](../../examples/hello_regression/site_runner.py)
- [examples/hello_regression/job.py](../../examples/hello_regression/job.py)

The important point is that `client.py` does not compute the local statistics itself. It shells out to `site_runner.py`. For a real TRE wrapper, replace that subprocess call with TSD, DX, or another site API call.

## Topology

- NVFlare server on a reachable host
- NVFlare wrapper client on a reachable host
- wrapper client calls the TRE-specific API
- TRE runs the local analysis internally
- wrapper client downloads summary statistics and sends them back to the NVFlare server

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- create `~/venvs/nvflare` on the server host
- create `~/venvs/nvflare` on the wrapper-client host
- make sure the wrapper host can reach the NVFlare server
- install the TRE-specific dependencies described in [TSD](../sites/tsd.md) or [UK Biobank RAP / DNAnexus](../sites/ukb-rap.md)

## Local Development Run

Before wiring in a real TRE API, run the shared example locally:

```bash
source ~/venvs/nvflare/bin/activate
python examples/hello_regression/job.py --env sim --n_clients 2
```

Run that from the repository root. It proves the server aggregation and the subprocess-based client boundary work.

## Wrapper Contract

Keep the same server-side aggregation in [examples/hello_regression/job.py](../../examples/hello_regression/job.py). In the client, replace the local subprocess with:

1. upload code or parameters into the TRE
2. submit the TRE-side job
3. wait for completion
4. download the JSON summary statistics
5. send those summary statistics back to NVFlare

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
