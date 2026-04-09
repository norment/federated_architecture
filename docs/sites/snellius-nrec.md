# Snellius + NREC

## Pattern

Use NVFlare-native clients.

- server on NREC
- client on Snellius
- optional additional client on another reachable host

## Decision Point

Can the Snellius client host open an outbound connection to the NREC server FL port?

If yes, use [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md).

## What To Fix In Provisioning

- use the server FQDN or stable IP in `project.yml`
- use explicit FL and admin ports
- prefer high ports such as `29002` and `29003`
- use one shared provisioning run for all kits
- if the client connects and immediately disconnects, check hostname and certificate mismatch first

## First Validation Run

1. Provision kits on the server host.
2. Copy client kits to Snellius and any other client sites.
3. Start server.
4. Start clients.
5. Start admin console.
6. Submit a tiny job.
7. Shut everything down after the run.

## Record Per Analysis

- which host runs the server
- which ports are used
- which site names map to which real sites
- where input data lives on each client
- where job results are downloaded

## Related Docs

- [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md)
- [NVFlare basics](../nvflare-basics.md)
