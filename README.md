# README

This repository contains a collection of workflows & scripts that to be used within a CI environment
to streamline the process of managing and testing apps.
All the workflows can be manually triggered and configured from the [action page](https://github.com/LedgerHQ/ledger-app-tester/actions).

## Workflows Overview

In the [workflows](.github/workflows) directory, some files (whose name starts by `_`)
are internal workflows, only intended to be called from other top level workflows.
The important ones are:

- `fast-check.yml`: Linter for the internal workflows/scripts.
- `build_all.yml`: Build all available Apps.
- `scan_all.yml`: Scan build all available Apps.
- `test_all.yml`: Test (with _ragger_ framework) all available Apps.
- `check_all.yml`: Run the Guideline Enforcer on all available Apps.

They are triggered on the following conditions:

- On a new Pull request.
- Scheduled (each one with its own setup).
- Manually (from the dedicated page of the repository).

The workflows accept few input parameters when executed manually:

- Device(s) to target.
- SDK reference to be used (default is `master` for the Build, and the `HEAD` of `API_LEVEL` for the Test).
- Request to send the result on Slack (dedicated channel `#embedded-apps-tester`).

Also, some configuration files are available in the directory `input_files`:

- `test_lists.json`: List of _Whitelist_ and _Blacklist_ Apps for each test.
- `test_info.json`: List of config for the _ragger_ tests execution.

## Workflows Configuration

### Scheduling

Each workflow is executed independently, with its own schedule (thanks to `cron`):

- ___Build___ & ___Scan___: During the night, every day from Monday to Friday.
- ___Test___: During the night, every Monday.
- ___Check___: During the night, every Wednesday.

### SDK Reference

The SDK reference (branch) used differ from one task to another:

- ___Build___ & ___Scan___:
  - Manual trigger: The user enters manually the reference. Default is `master`.
  - Automatic: The reference is `master`.
- ___Test___:
  - Manual trigger: The user enters manually the reference. Default is `master`.
  - Automatic: The reference is retrieved automatically from the SDK repository,
    and set to the _latest_ available for each device.

### Adding a new device

To add a new device, the modifications are:

- In each top level workflow, add a new _input parameter_, and update the job `devices_config` accordingly.
- In `_setup_devices.yml`: Adapt the job `define_devices`.
- In `_build_app.yml` & `_test_app.yml`: Add the corresponding steps `Run` and `Check failure`.
- In `_test_app.yml`: Ensure the correct SDK reference is selected, or add a new step for this.
- In `setup_devices.py`: Add a new parameter and adapt the code.
- In `parse_all_apps.py`: Add the new device in the list `devices`.

> Note: To ensure finding all related parts, a simple grep on an existing one (e.g. __stax__) is sufficient.

## Workflows Output

Once a workflow has been executed, it outputs a _summary_, and upload the significant _artifacts_.

In the Summary, the information is:

- The github event that has triggered the workflow.
- The number of Apps being tested.
- The number of errors encountered (and the number of apps concerned by those errors).
- A table with all tested Apps per device, and an icon giving the status:
  - ✅ Success
  - ❌ Failure
  - ⚫ Not selected
  - 🚧 Workflow issue
  - 🚫 No test executed because of Build issue

## Workflows internals

The internal operations are described [here](doc/internals.md)

## Artifacts

The artifacts management is described [here](doc/artifacts.md)
