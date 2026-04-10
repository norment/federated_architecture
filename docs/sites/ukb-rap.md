# UK Biobank RAP / DNAnexus

## Pattern

Use a wrapper client.

Keep the NVFlare socket outside RAP. In tutorial 3, the intended pattern is to run the wrapper on the same non-TRE host as the NVFlare server.

The wrapper should call `dx`, wait for job completion, collect agreed outputs, and send only those outputs back into the federated run.

## Existing Tracked Notes

- [ukb/dx_fema_usage.md](../../ukb/dx_fema_usage.md)
- [ukb/dx_swiss_army_knife.md](../../ukb/dx_swiss_army_knife.md)

## Wrapper Lifecycle

1. Receive task from NVFlare server.
2. Trigger RAP execution through `dx`.
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
- destination for outputs
- which outputs are allowed to leave RAP

## First Validation Run

Before wiring RAP into NVFlare:

1. run the target `dx` command manually
2. confirm the expected output lands in the intended project location
3. confirm the wrapper can retrieve that output without manual intervention

## Related Docs

- [Wrapper clients for TRE sites](../tutorials/03-wrapper-clients.md)
