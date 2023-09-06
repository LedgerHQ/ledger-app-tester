# README

This repository contains a collection of scripts that can be used both locally and within a CI environment to streamline the process of managing and testing apps. Below, you'll find an overview of the key scripts and how to use them.
All the workflow can be manually triggered and configured from the **actions** page.

## Scripts Overview

### 1. Create App List

The `create_app_list` script is designed to parse GitHub repositories and generate a list of app variants. It takes a JSON file named `extra_info.json` (located in the `input_files/` directory) as a parameter, which includes essential information such as `build_path`. For each app, this script clones the repository and executes the `make listvariant` command to generate the list of variants.

**Output**: An output of this script can be found in `input_files/input.json`. It also incorporates all the information provided in `extra_info_file.json`.

**CI Usage**: This script is utilized by the `check_outdated_build_db.yaml` CI script.

**Note**: To use this script locally, you'll need to create a GitHub access token.

### 2. Build and Test

The `build_and_test` script performs either build or test operations on the apps listed in the input
file generated previously.

**Build Operation**:
- Sets up repositories and SDK.
- Chooses the correct build path and extra flags based on the input file.
- Performs the build operation for the specified device.

**Test Operation**:
- Installs required dependencies.
- Executes pytest in the test directory specified in the input file for the specified device.

**CI Usage**:
- `test_devices.yml`: Tests devices.
- `build_nanos.yml`: Builds for Nano S.
- `build_nanosp.yml`: Builds for Nano SP.
- `build_nanox.yml`: Builds for Nano X.
- `build_stax.yml`: Builds for STAX.

To reduce CI run times, builds were split by devices.

### 3. Planned Improvements

- **Support for ZEMU Tests**
- **Guideline Enforcer Test**

## Getting Started

To get started with this repository, follow these steps:

1. Clone the repository to your local machine.
2. Review the corresponding CI files and scripts to understand their usage.
3. Ensure you have set up a GitHub access token if you intend to use the scripts locally.
