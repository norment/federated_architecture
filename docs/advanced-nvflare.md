# Advanced NVFlare Notes

This page is for NVFlare features that are intentionally not used in the beginner tutorials.

The beginner templates in this repo assume:

- one FL server
- no high-availability failover
- no separate Overseer service

## Overseer And Overseer Agent

In NVFlare, the `Overseer` is the component used for high availability. Its job is to keep track of which FL server is currently the active one and tell the rest of the system where to connect.

The `OverseerAgent` is the component that runs on the FL server, FL clients, and admin side and talks to the Overseer on their behalf.

For a single-server deployment, you usually do not need a real Overseer service.

## Why You Might Add An Overseer Agent

You would look at this only if you want one of these:

- multiple FL servers with failover
- a stable way for clients and admins to discover the current active server
- HA-oriented deployment rather than the single-session pattern used in this repo

## Minimal DummyOverseerAgent Snippet

If you want the startup kits to include a static overseer-agent configuration for a single server, add this to `project.yml` under `builders`:

```yaml
- path: nvflare.lighter.impl.static_file.StaticFileBuilder
  args:
    overseer_agent:
      path: nvflare.ha.dummy_overseer_agent.DummyOverseerAgent
      overseer_exists: false
      args:
        sp_end_point: ${SERVER_NAME}:${FL_PORT}:${ADMIN_PORT}
```

This does not create a real Overseer service. It configures a dummy agent that always returns the server endpoint you hard-coded in `sp_end_point`.

That is why the beginner tutorials in this repo now omit it: it adds one more concept without solving a real problem for the single-server case.

## Real HA Setup

If you need actual server failover, read the NVFlare HA docs and configure a real Overseer rather than only `DummyOverseerAgent`.

Official NVFlare docs:

- FLARE Architecture: https://nvflare.readthedocs.io/en/main/system_architecture/system_architecture.html
- High Availability and Server Failover: https://nvflare.readthedocs.io/en/main/programming_guide/high_availability.html
- Terminologies and Roles: https://nvflare.readthedocs.io/en/2.6.0/user_guide/security/terminologies_and_roles.html

## Where This Came From

The `DummyOverseerAgent` snippet that was previously in this repo came from [here](https://github.com/lcmoore/FedFEMA/blob/main/JCVI/RealWorld/project.yaml).
