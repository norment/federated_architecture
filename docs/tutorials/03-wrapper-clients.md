# Tutorial 3: Wrapper Clients For TRE Sites

Use this when a TRE cannot run an NVFlare-native client that connects directly to the server, but the TRE exposes an API or job interface that you can drive from outside.

## Topology

- NVFlare server on a reachable host
- NVFlare wrapper client on a reachable host
- wrapper client calls the TRE-specific API
- TRE runs the local analysis internally
- wrapper client collects the agreed outputs and sends them back to the NVFlare server

## Prerequisites

- complete [Prerequisites](../prerequisites.md)
- create the NVFlare venv on the server host
- create the NVFlare venv on the wrapper-client host
- make sure the wrapper host can reach the NVFlare server
- activate the NVFlare venv in every shell that runs the server or wrapper client
- install the TRE-specific dependencies described in [TSD](../sites/tsd.md) or [UK Biobank RAP / DNAnexus](../sites/ukb-rap.md)

## The Wrapper Contract

From NVFlare's point of view, the wrapper still looks like a normal client:

1. receive task from server
2. trigger site-local analysis through the TRE API
3. wait for completion
4. download or collect result files
5. send agreed outputs back to the server

This is often the right pattern for secure platforms because the direct NVFlare socket stays outside the TRE boundary.

## TSD Pattern

For TSD, the useful sequence is:

1. upload pipeline bundle
2. upload generated job script
3. submit job through the TSD HPC API
4. wait for job completion
5. download results

This repo includes tracked notes in [TSD site guide](../sites/tsd.md). The reviewed reference flow was adapted from the TSD HPC API example.

## UKB RAP / DX Pattern

For UKB RAP / DNAnexus, the useful sequence is:

1. prepare container or analysis package
2. launch analysis with `dx run` or Swiss Army Knife
3. wait for job completion
4. upload or collect output
5. return agreed outputs to the NVFlare server

Tracked notes are in [UKB RAP site guide](../sites/ukb-rap.md) and the existing [ukb](../../ukb) folder.

## What To Keep Site-Specific

- auth and 2FA
- upload and download paths
- scheduler or API parameters
- permitted output files
- retry logic for transient API failures

## What To Keep Common Across Sites

- job lifecycle inside the wrapper client
- serialization of outputs back to NVFlare
- logging and error handling
- result validation

## Recommended Next Step

Keep the wrapper docs short and implementation-specific:

- one short page per TRE
- one small wrapper launcher per TRE
- same high-level lifecycle everywhere
