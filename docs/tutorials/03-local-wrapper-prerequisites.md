# Tutorial 3 Prerequisites

Tutorial 3 is local from NVFlare's perspective:

- the server runs on your laptop or workstation
- the wrapper clients also run on that same host
- the admin shell also runs on that same host
- only the wrapper code talks to TSD

So unlike tutorial 2, tutorial 3 does not need a public FL endpoint.

## Python Environment

Create the tutorial-3 environment on the local host:

```bash
python3 -m venv ~/venvs/nvflare_tutorial3
source ~/venvs/nvflare_tutorial3/bin/activate
python -m pip install --upgrade pip
pip install nvflare numpy tsd-api-client
```

## TSD Access

For the two-site tutorial, make sure:

- your host can reach `api.tsd.usit.no`
- your host is on VPN or otherwise whitelisted for TSD
- you have `tacl`
- you have access to both `p33` and `p697`
- you have password and OTP available when refresh is needed

Do not put password or OTP in tracked config files.

## One-Time `tacl` Registration

```bash
source ~/venvs/nvflare_tutorial3/bin/activate

tacl --register p33
tacl --register p697
```

## Prime TSD Before Each Federated Session

Run this before each tutorial-3 session:

```bash
source ~/venvs/nvflare_tutorial3/bin/activate

./scripts/prime_tsd_session.sh --username p33-yourusername
./scripts/prime_tsd_session.sh --username p697-yourusername
```

The script verifies File API and HPC access and refreshes cached tokens under your home directory.

## Next Step

When both priming commands succeed, continue with:

```bash
./scripts/tutorial3_local.sh init ~/nvflare_wrapper_demo \
  --p33-user p33-yourusername \
  --p697-user p697-yourusername
```

## Related Docs

- [Tutorial 3: Wrapper clients for TRE sites](03-wrapper-clients.md)
- [Prerequisites](../prerequisites.md)
- [TSD site notes](../sites/tsd.md)
