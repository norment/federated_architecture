# Tutorial 2 Server Endpoint Options

Tutorial 2 needs one thing before provisioning:

- a **publicly reachable FL endpoint** for the NVFlare server

That means a host and port that every participating client site can reach from outside.

For tutorial 2:

- expose the FL port, usually `8002`
- keep the admin port, usually `8003`, local unless you truly need remote admin access

## What Goes Into `.env`

For tutorial 2, these values describe the public client-facing FL endpoint:

- `SERVER_NAME`: the public DNS name or IP address that clients will use
- `PUBLIC_FL_PORT`: the public FL port that clients will use
- `LOCAL_FL_PORT`: the local FL port that the NVFlare server process listens on

`ADMIN_PORT` is usually still `8003`, but that is for your local admin shell and does not need to be reachable from the clients.

In the simple tutorial-2 pattern:

- clients connect to `SERVER_NAME:PUBLIC_FL_PORT`
- the server process listens locally on `LOCAL_FL_PORT`
- the local admin shell connects to `ADMIN_HOST:ADMIN_PORT`, usually `localhost:8003`

Do not put these into `.env`:

- SSH passwords
- site account passwords
- 2FA material
- API tokens for other services

Those are used only when logging in to machines or copying startup kits.

## Option 1: Dedicated Public Machine

This is the simplest operational setup.

Use this when:

- you already have a VM or server with a stable public DNS name or IP
- you can open the FL port on that host

Example `.env` values:

```bash
SERVER_NAME=server.example.org
LOCAL_FL_PORT=8002
PUBLIC_FL_PORT=8002
ADMIN_PORT=8003
ADMIN_HOST=localhost
```

Quick validation from another machine:

```bash
curl -v telnet://server.example.org:8002
nc -vz server.example.org 8002
```

If clients will connect through that endpoint, provision tutorial 2 with those values.

## Option 2: Local Machine Plus Existing Port Forwarding

Use this when:

- you can run the NVFlare server on your laptop or workstation
- your institution already provides a stable public host/port that forwards to your local `8002`

This can be:

- firewall/NAT forwarding managed by your institution
- an institutional bastion or relay with already-opened port forwarding
- another stable TCP forwarding setup you already control

The important point is that the forwarded endpoint must already be publicly reachable.

Example:

- NVFlare server process runs on your laptop on local `8002`
- public endpoint is `relay.example.org:18002`

Example `.env` values:

```bash
SERVER_NAME=relay.example.org
LOCAL_FL_PORT=8002
PUBLIC_FL_PORT=18002
ADMIN_PORT=8003
ADMIN_HOST=localhost
```

Quick validation from another machine:

```bash
curl -v telnet://relay.example.org:18002
nc -vz relay.example.org 18002
```

If the public endpoint changes, reprovision and redistribute the startup kits.

## Option 3: Local Machine Plus ngrok TCP

This is often the easiest way to get started if you do not already have a suitable public host.

Use this when:

- you want to run the NVFlare server locally on your laptop or workstation
- you do not have another stable public server

### ngrok prerequisites

You need:

- an ngrok account
- your ngrok auth token
- a valid payment method on the ngrok account

ngrok's TCP endpoint docs state that TCP endpoints are available on the free plan only after adding a valid payment method. The plan can remain free.

Relevant docs:

- https://ngrok.com/docs/getting-started
- https://ngrok.com/docs/tcp/
- https://ngrok.com/docs/universal-gateway/tcp-addresses

### ngrok setup

Install ngrok and connect it to your account:

```bash
ngrok config add-authtoken <YOUR_NGROK_AUTHTOKEN>
```

Then start a TCP tunnel for the NVFlare FL port:

```bash
ngrok tcp 8002
```

ngrok will print an endpoint like:

```text
tcp://2.tcp.eu.ngrok.io:11609 -> localhost:8002
```

For tutorial 2, use:

- `SERVER_NAME=2.tcp.eu.ngrok.io`
- `LOCAL_FL_PORT=8002`
- `PUBLIC_FL_PORT=11609`
- keep `ADMIN_PORT=8003` local

On the free plan, ngrok will not give you public port `8002`. It assigns a separate public TCP port such as `11609`, and that assigned public port is what goes into `PUBLIC_FL_PORT`.

Example `.env` values:

```bash
SERVER_NAME=2.tcp.eu.ngrok.io
LOCAL_FL_PORT=8002
PUBLIC_FL_PORT=11609
ADMIN_PORT=8003
ADMIN_HOST=localhost
```

Do not expose the admin port through ngrok unless you explicitly need remote admin access.

### ngrok validation

Before provisioning, test the public endpoint from another machine:

```bash
curl -v telnet://2.tcp.eu.ngrok.io:11609
nc -vz 2.tcp.eu.ngrok.io 11609
```

If those work, clients should be able to reach the FL endpoint.

### ngrok limitations

- on a free plan, the TCP endpoint is usually not stable across restarts
- if the endpoint changes, you must reprovision and redistribute the startup kits
- this is good for getting started, demos, and pilot runs
- for repeated use, a dedicated stable server or stable reserved TCP address is better

## Recommended Rule

For tutorial 2:

- if you already have a public server, use it
- otherwise, local machine plus `ngrok tcp 8002` is the easiest getting-started path
- in all cases, provision with the public FL endpoint that clients will actually dial
