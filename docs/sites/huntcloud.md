# HuntCloud

## Pattern

Prefer NVFlare-native.

Fall back to a wrapper only if HuntCloud cannot allow the required outbound connection to the NVFlare server.

## Decision Point

Can the HuntCloud client host open an outbound connection to the server FL port?

- If yes: use [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md)
- If no: use [Wrapper clients for TRE sites](../tutorials/03-wrapper-clients.md)

## What To Verify First

- which HuntCloud host will run the client
- who can request or approve the firewall exception
- server hostname and FL port
- whether the client host resolves the server hostname correctly
- whether logs and downloaded job artifacts are kept on persistent storage

## First Validation Run

Do this before any domain-specific workload:

1. tiny two-site hello world
2. one HuntCloud client and one known-good native client
3. built-in or toy NVFlare job
4. only then move to the real analysis code

## Record Per Analysis

- HuntCloud host name
- server host name
- FL port and admin port
- client site name used in provisioning
- path where logs are written
- path where outputs are downloaded or exported

## Related Docs

- [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md)
- [Wrapper clients for TRE sites](../tutorials/03-wrapper-clients.md)
