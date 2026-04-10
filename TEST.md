# Test Plan

This repo uses `pytest` for unit tests.

The unit-test suite is designed to validate the checked-in example logic and the NVFlare-facing integration points without any external accounts, network access, or live NVFlare deployment.

## Scope

- deterministic synthetic-data generation and regression aggregation in `examples/hello_regression/common.py`
- client-process behavior in `examples/hello_regression/client.py`
- wrapper adapter behavior in `examples/hello_regression/tsd_wrapper.py` and `examples/hello_regression/dx_wrapper.py`
- job aggregation and environment selection in `examples/hello_regression/job.py`
- config parsing in `tre_wrappers/tsd.py` and `tre_wrappers/dx.py`

## Explicitly Out Of Scope

- live DX jobs
- live TSD sessions
- real NVFlare server/client/admin startup
- tutorial end-to-end validation

Those belong to higher-level integration checks, not the unit-test layer.

## Mocking Strategy

- replace `nvflare.client` process behavior with a fake in-memory object when testing `client.py`
- replace `run_tsd_job` and `run_dx_job` with fakes that return synthetic result bytes
- replace `TSDSettings.from_config` and `DXSettings.from_config` in adapter tests when the test is about adapter wiring rather than transport parsing
- use temporary directories for output files and config files

## Required Local Environment

Add `pytest` to the shared NVFlare environment used in this repo:

```bash
source ~/venvs/nvflare/bin/activate
pip install pytest
```

The rest of the example dependencies are already described in [`docs/prerequisites.md`](/home/oleksanf/github/cmig-research-group/federated_architecture/docs/prerequisites.md).

## Test Files

- `tests/test_common.py`
  Validates deterministic site configs, empty-input handling, and stable regression summaries.
- `tests/test_client.py`
  Validates explicit executor requirements, local executor behavior, and client success/error model emission.
- `tests/test_job.py`
  Validates aggregator behavior, summary-file writing, and `sim`/`prod` environment selection logic.
- `tests/test_wrappers.py`
  Validates that wrapper adapters require explicit config paths and pass the expected spec objects into mocked transports.
- `tests/test_transport_settings.py`
  Validates DX and TSD settings parsing without any real credentials or network calls.

## Commands

Run the default unit-test suite:

```bash
source ~/venvs/nvflare/bin/activate
pytest -q
```

Run one test module:

```bash
source ~/venvs/nvflare/bin/activate
pytest -q tests/test_wrappers.py
```

Run the local integration layer:

```bash
source ~/venvs/nvflare/bin/activate
pytest -q -m integration tests/integration
```

These integration tests exercise the real local tutorial topologies:

- tutorial 1 in `sim`
- tutorial 2 with a local `poc` test harness around the native-client path
- tutorial 3 in `poc`

Current status of the integration layer:

- tutorial 1 passes
- tutorial 2 passes in the local `poc` harness
- tutorial 3 passes with mocked DX and TSD transports

Tutorial 2 remains a user-facing `prod` tutorial in the docs. The integration harness uses a local `poc` workspace only for testing, so the native-client path can be exercised locally without relying on the provisioned admin-kit submission behavior.

`examples/hello_regression/job.py` now exposes three execution environments:

- `--env sim`
- `--env prod`
- `--env poc`

`--clients` is the topology input. The job runs against exactly those named clients.

For tutorial 3, the tests still start real local NVFlare server and client processes, but the external TSD and DX transports are replaced with local mock transport mode:

- `HELLO_REGRESSION_TSD_MOCK_MODE=local`
- `HELLO_REGRESSION_DX_MOCK_MODE=local`

That keeps the integration layer focused on NVFlare orchestration, startup kits, job submission, and wrapper-process routing without requiring real TSD or DX accounts.
