# NVFlare Basics For TRE Researchers

## Core Model

- one server coordinates the run
- one client runs per participating site
- an admin submits a job after server and clients are online
- raw data stays at each site
- clients return only the agreed outputs

## Main Networking Constraint

Clients connect outbound to the server.

For any TRE, the first question is:

"Can a client process at this site open an outbound connection to the server host and port?"

If yes, the site can often be NVFlare-native.

If no, use a wrapper pattern:

- run the NVFlare client on a reachable machine next to the server or in another allowed environment
- let that client call the TRE's own API, batch system, or job runner
- return only the agreed outputs back into the federation

For these tutorials:

- clients need the FL server port
- clients do not need the admin port
- there is no separate overseer port to open

If you later need HA or overseer-based server discovery, see [advanced NVFlare notes](advanced-nvflare.md).

## Two Deployment Patterns

### NVFlare-native

Use this when the site can:

- run Python and NVFlare
- reach the server host and port outbound
- start a client process for the analysis session

Examples in this repo:

- Snellius as a native client site
- HuntCloud if firewall exception is available

### Wrapper client

Use this when the site cannot make the direct NVFlare connection but does expose:

- a Slurm API
- a controlled batch API
- a platform API such as TSD HPC API or DNAnexus DX

Examples in this repo:

- TSD via upload -> submit job -> wait -> download result
- UKB RAP / DNAnexus via `dx run` or Swiss Army Knife

## Execution Modes

This repo uses three execution modes:

- `sim`: run the job through the NVFlare simulator on one host
- `prod`: run against live provisioned server, client, and admin processes
- `poc`: prepare a local multi-process NVFlare workspace for one-host development

In this repo, the tutorials use fixed modes:

- tutorial 1 uses `sim`
- tutorial 2 uses `prod`
- tutorial 3 uses `poc`

Tutorial 3 still submits the job with `--env prod`, because the job talks to live local NVFlare processes in the prepared POC workspace rather than to the simulator.

## Certificates And Signing In `prod`

Provisioned NVFlare startup kits include certificates, private keys, and signed material for the server, clients, and admin user.

That means a `prod` run is not just "the same as `sim`, but with more processes." It also adds trust setup:

- participants must come from the same provisioning run
- names and host identities must match what was provisioned
- the correct startup kit must be used for each server, client, and admin participant

This is why `prod` failures often look like deployment failures rather than application failures:

- hostname or certificate name mismatch
- mixed startup kits from different provisioning runs
- stale workspace after reprovisioning
- wrong participant startup directory during launch or submission

## Operating Model

This repo assumes an analysis-session model, not a persistent service:

- start server
- start clients
- submit job
- download results
- stop everything

If one analyst does not have accounts or 2FA access to all sites, the run has to be coordinated across collaborators.

## Minimum Per-Site Checklist

- Who starts the client at this site?
- Can the site be NVFlare-native, or does it need a wrapper?
- What host runs the client or wrapper?
- What outbound connection is needed?
- What credentials, VPN, or 2FA are required?
- Where do outputs land?
- What exactly is allowed to leave the site?

## Common Failure Modes

- Outbound port blocked from client site to server
- Server hostname or certificate name mismatch
- Mixed startup kits from different provisioning runs
- Site-specific API auth failures
- OTP reuse issues on TSD
- Assumptions about shared filesystems that do not hold across sites
