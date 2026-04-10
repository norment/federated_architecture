# UK Biobank RAP / DNAnexus

## Pattern

Use a wrapper client.

Keep the NVFlare socket outside RAP. In tutorial 3, the intended pattern is to run the wrapper on the same non-TRE host as the NVFlare server.

The wrapper should call `dx run`, wait for job completion, collect agreed outputs, and send only those outputs back into the federated run.

Select the RAP project explicitly. Unlike TSD, the project cannot be inferred from the username.

## Existing Tracked Notes

- [ukb/dx_fema_usage.md](../../ukb/dx_fema_usage.md)
- [ukb/dx_swiss_army_knife.md](../../ukb/dx_swiss_army_knife.md)

## Prerequisites

- `dx` installed and on `PATH`
- the local host can reach `api.dnanexus.com`
- your saved DX login can access the RAP project used by the wrapper
- for the current tutorial-3 example, one local wrapper client is reserved for RAP

Use the shared Python environment from [Prerequisites](../prerequisites.md#python-environment).

## Wrapper Lifecycle

1. Receive task from NVFlare server.
2. Trigger RAP batch execution through `dx run`.
3. Monitor the RAP job.
4. Collect result files when complete.
5. Return agreed outputs to the federated run.

The same host can run:

- the NVFlare server
- the RAP wrapper client
- a second wrapper client for another TRE such as TSD

## Required Per-Use-Case Settings

- container or app used in RAP
- input files and expected output files
- exact `dx run` command template
- RAP project ID or name to select
- destination for outputs
- which outputs are allowed to leave RAP

## Priming

For tutorial 3, priming RAP should mean:

1. make sure `dx login` is valid on the local host
2. switch to the intended RAP project with `dx select`
3. verify that `dx ls /` works in that project

Use the helper like this:

```bash
source ~/venvs/nvflare/bin/activate

./scripts/prime_dx_session.sh --project project-REDACTED1234567890EXAMPLE
```

This verifies DX login, switches the local DX context to the requested project, checks that the project root is readable, and writes a small manifest under `~/.cache/federated_architecture/dx/`.

Launching Cloud Workstation is optional and is best treated as a manual debug aid rather than the normal wrapper execution model.

If you want an interactive RAP workstation for manual debugging, the same helper supports:

```bash
./scripts/prime_dx_session.sh \
  --project project-REDACTED1234567890EXAMPLE \
  --start-workstation
```

The official Cloud Workstation defaults documented by DNAnexus are:

- instance type `mem1_ssd1_v2_x8`
- maximum session length `1h`

For `hello_regression`, the current tutorial-3 implementation uses `app-swiss-army-knife` as a batch runner and the same shared `site_runner.py` and `common.py` logic used by the local and TSD paths. The site-local part of `common.py` is stdlib-only, so RAP does not need `numpy` just to run the tutorial.

## First Validation Run

Before wiring RAP into NVFlare:

1. run the target `dx` command manually
2. confirm the expected output lands in the intended project location
3. confirm the wrapper can retrieve that output without manual intervention

## Related Docs

- [Wrapper clients for TRE sites](../tutorials/03-wrapper-clients.md)
- [TSD](tsd.md)
