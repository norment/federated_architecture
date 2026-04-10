# NREC

## Pattern

Use NREC as a server-hosting option when you need a dedicated non-TRE machine that participating clients can reach.

NREC is not itself a TRE client note in this repo. Its role here is as a possible NVFlare server location.

## Decision Point

Can all participating client sites open the required outbound connection to the NREC server FL port?

If yes, NREC can host the server side of [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md).

## What To Fix In Provisioning

- use the NREC server FQDN or stable IP in `project.yml`
- use explicit FL and admin ports
- ensure the chosen FL port is reachable from every participating client site
- ensure the admin port is reachable from the host that runs `fl_admin.sh`
- use one shared provisioning run for all kits

## First Validation Run

1. Provision kits on the NREC server host.
2. Start the server on NREC.
3. Start one reachable client.
4. Start the admin console.
5. Submit a tiny job.
6. Add further client sites after the first client works.

## Record Per Analysis

- which NREC host or VM runs the server
- which FL and admin ports are used
- which sites are expected to connect natively
- which sites require wrappers instead
- where results are downloaded

## Related Docs

- [Dedicated server + native clients](../tutorials/02-dedicated-server-native-clients.md)
- [NVFlare basics](../nvflare-basics.md)
