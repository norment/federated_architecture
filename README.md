# federated_architecture

Hello-world and deployment notes for running analyst-started federated analyses with NVFlare across TRE and HPC sites.

## What This Repo Is

This repo is meant to help researchers get from "I want to run a federated analysis across a few sites" to a working first deployment with gradually increasing complexity:

1. Single host hello world
2. Dedicated server with NVFlare-native clients
3. TRE wrapper clients that call site-specific APIs

## What This Repo Is Not

This repo is not aiming at a permanent 24/7 federated service where users submit jobs into always-on server and client processes.

The expected operating model is:

- one analyst or coordinating site starts the NVFlare server
- each participating site starts its own client
- the job is run for that analysis session
- the full setup is shut down when the analysis is done

## NVFlare In One Minute

- NVFlare uses a client/server architecture
- the server listens on a reachable host and port
- clients connect outbound to the server
- clients do not need inbound connections from outside
- an admin submits a job after server and clients are online

This outbound client-to-server connection is the main design constraint for TRE deployment.

## Choose A Deployment Pattern

| Pattern | Use when | Typical sites | Doc |
| --- | --- | --- | --- |
| NVFlare-native | The site can open the required outbound connection from the client host to the server | NREC-hosted clients, Snellius, HuntCloud with firewall exception | [Dedicated server + native clients](docs/tutorials/02-dedicated-server-native-clients.md) |
| Wrapper client | The TRE does not allow a native NVFlare client to connect out, but it exposes an API or controlled job interface | TSD HPC API, UKB RAP DX | [Wrapper clients for TRE sites](docs/tutorials/03-wrapper-clients.md) |

## Start Here

- [Prerequisites](docs/prerequisites.md)
- [NVFlare basics for TRE researchers](docs/nvflare-basics.md)
- [Shared runnable example: hello_regression](examples/hello_regression/README.md)
- [Tutorial 1: Single-host hello world](docs/tutorials/01-localhost.md)
- [Tutorial 2: Dedicated server + native clients](docs/tutorials/02-dedicated-server-native-clients.md)
- [Tutorial 3: Wrapper clients for TRE sites](docs/tutorials/03-wrapper-clients.md)

## Site Notes

- [Snellius + NREC](docs/sites/snellius-nrec.md)
- [HuntCloud](docs/sites/huntcloud.md)
- [TSD](docs/sites/tsd.md)
- [UK Biobank RAP / DNAnexus](docs/sites/ukb-rap.md)
- Existing UKB command notes: [ukb/dx_fema_usage.md](ukb/dx_fema_usage.md), [ukb/dx_swiss_army_knife.md](ukb/dx_swiss_army_knife.md)

## Repo Layout

- `docs/` tracked documentation and deployment notes copied/adapted from reviewed examples
- `examples/` checked-in runnable examples used by the tutorials
- `ukb/` tracked UKB RAP / DX command notes
- `external/` review-only material that is not expected to be committed

## Relevant Google Docs And Spreadsheets

These links are intentionally kept here because they are part of the working project context.

- [Federated analysis notes](https://docs.google.com/document/d/1GXTNEM4xV8B8EXIqsBx1SABcf-_82UnD5OT2Bu1KVKY/edit?tab=t.0)
- [Federated analysis studies](https://docs.google.com/spreadsheets/d/1vUDLtJvQESbyEKG9y48WJQ8VzD6K-hYIJnLNc8Wauqs/edit?gid=0#gid=0)
- [Federated analysis use-cases](https://docs.google.com/spreadsheets/d/1vUDLtJvQESbyEKG9y48WJQ8VzD6K-hYIJnLNc8Wauqs/edit?gid=968194630#gid=968194630)

## Pointers To External Repositories

These are intentionally preserved as working references.

### Servers And Site Integrations

- Oslo / NREC as likely server location
- JCVI server location: TBD
- UK Biobank and DX: see [ukb](ukb)
- TSD: https://github.com/precimed/tsd_hpc_api
- HUNT: https://github.com/lcmoore/FedFEMA/tree/huntcloud/HUNT_Cloud
- EADB: https://github.com/amorris28/eadb-ad-prediction/tree/main/federation
- Snellius real-world example: https://github.com/lcmoore/FedFEMA/tree/real_world_setup/Snellius/real_world
- JCVI simulated clients: TBD

### Framework Examples

- NVFlare wrapper around Slurm-style execution: https://github.com/NVIDIA/NVFlare/blob/main/examples/advanced/llm_hf/MULTINODE.md

### Use Cases

- Federated GWAS / FedGen: https://github.com/precimed/FedGen
