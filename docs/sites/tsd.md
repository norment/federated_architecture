# TSD

## Pattern

Use a wrapper client.

Run the NVFlare client on a reachable machine outside TSD. In tutorial 3, the intended pattern is to run that wrapper client on the same non-TRE host as the NVFlare server.

That wrapper client should call the TSD HPC API, wait for completion, download the agreed outputs, and return only those outputs to the federated run.

## References

- TSD HPC API reference repo: https://github.com/precimed/tsd_hpc_api
- Local UK-style wrapper notes in this repo: [Wrapper clients for TRE sites](../tutorials/03-wrapper-clients.md)

## Prerequisites

- `tacl` installed and registered for the TSD project
- project username
- password and OTP available when tokens expire
- the external host that runs the wrapper must be whitelisted for the TSD project
- a TSD project admin should request that whitelisting by contacting `tsd-drift@usit.uio.no`
- VPN when required by the project setup

## Wrapper Lifecycle

1. Build a zip of the pipeline files.
2. Upload the zip to TSD import storage.
3. Upload a generated job script.
4. Submit the job through the HPC API.
5. Wait for completion.
6. Download and unpack the result archive.

## Required Per-Project Settings

- TSD project id
- TSD username
- host that is whitelisted to call the TSD side
- import directory
- export directory
- working directory inside TSD
- memory limit
- time limit
- name of the result archive to download
- exact commands inside the uploaded job script

## Failure Mode To Expect

TSD OTP codes are single-use within the time window. If multiple token refreshes happen close together, reuse of the same OTP can fail even if the code still looks current.

## First Validation Run

Before wiring TSD into NVFlare, validate the wrapper sequence by itself:

1. upload a tiny archive
2. submit a trivial TSD job
3. wait for completion
4. download a known output file

## Related Docs

- [Wrapper clients for TRE sites](../tutorials/03-wrapper-clients.md)
