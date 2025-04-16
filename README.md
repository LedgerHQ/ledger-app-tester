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
- Send the result on Slack (dedicated channel `#embedded-apps-tester`).

Also, some configuration files are available in the directory `input_files`: See [Configuration files](#configuration-files)

## Workflows Configuration

### Scheduling

Each workflow is executed independently, with its own schedule (thanks to `cron`):

- ___Build___ & ___Scan___: During the night, every day from Monday to Friday.
- ___Test___: During the night, every Monday.
- ___Check___: During the night, every Wednesday.

### SDK Reference

The SDK reference (branch) used differ from one operation to another.
The default configuration, used for scheduled triggering:

- ___Build___: `master` branch
- ___Scan___: `HEAD` of `API_LEVEL_xx` branch  (excluding `-rc`).
- ___Test___: Default SDK per device, directly from the docker container.
- ___Check___: Use the `master` branch of the SDK.

> __Note__: When triggering manually the __Test__, the default branch is `API_LEVEL_22`.

### Configuration files

Some parameters are configured thanks to json files, stored in the directory  [input_files](../input_files/).

#### Apps configuration

The Apps are configured in the file [apps_lists.json](../input_files/apps_lists.json).

Here, we define _Whitelist_ and _Blacklist_, for each operations. In each case, we just list the apps we want to setup:

```json
[
  {
    "check whitelist": [
      "app-boilerplate",
    ],
    "check blacklist": [],

    "test whitelist": [
      "app-boilerplate",
    ],
     "test blacklist": [],

   "scan whitelist": [
      "app-boilerplate",
     ],
    "scan blacklist": [],

    "build whitelist": [],
    "build blacklist": ["app-pocket"]
  }
]
```

#### Devices configuration

The devices are configured in the file [devices_list.json](../input_files/devices_list.json).

Here, we define the list of the default available devices that will be used on each operations.

Also, for the __Check__ (_Guideline Enforcer_), we need to define 1 device, on which the _scan-build_ will be run.

```json
[
  {
    "devices": ["nanos+", "nanox", "stax", "flex"]
  },
  {
    "device for check": "stax"
  }
]
```

#### Tests configuration

The _ragger_ tests are configured in the file [test_info.json](../input_files/test_info.json).

Here, we configure, when an App needs it

- Additional _Build flags_, needed by the App to run the tests.
- Additional _Test flags_, to be passed to `pytest`/`ragger` to execute the test.
- _Dependencies_, which are additional apps, needed for a test (like plugins, libraries)

```json
[
  {
    "name": "app-boilerplate1",
    "build_flags": "DEBUG=1"
  },
  {
    "name": "app-plugin-boilerplate",
    "dependencies": "app-ethereum"
  },
  {
    "name": "app-boilerplate2",
    "test_flags": "--fast"
  }
]
```

### Adding a new device

To add a new device, the modifications are:

- In `input_files/devices_list.json`: Add the new device in the list `devices`.
- If needed, also in `input_files/devices_list.json`: Update the default device used in the Check (Guildeline Enforcer)
- In `check_all.yml`: Add the new device in the input parameters.

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
