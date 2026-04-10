# Snellius

## Pattern

Use Snellius as an NVFlare-native client site if the client host can open the required outbound connection to the chosen server host.

## Decision Point

Can the Snellius client host open an outbound connection to the server FL port?

If yes, use [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md).

## What To Fix In Provisioning

- use the actual server FQDN or stable IP in `project.yml`
- use explicit FL and admin ports
- use one shared provisioning run for all kits
- if the client connects and immediately disconnects, check hostname and certificate mismatch first

## First Validation Run

1. Provision kits on the server host.
2. Copy the Snellius client kit to the Snellius host.
3. Start server.
4. Start the Snellius client.
5. Start admin console.
6. Submit a tiny job.
7. Shut everything down after the run.

## Record Per Analysis

- which host runs the server for this run
- which FL and admin ports are used
- which NVFlare site name maps to Snellius
- where input data lives on each client
- where job results are downloaded

## Related Docs

- [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md)
- [NVFlare basics](../nvflare-basics.md)
