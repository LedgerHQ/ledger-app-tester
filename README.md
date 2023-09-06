# README

This repository contains a collection of scripts that can be used both locally and within a CI environment to streamline the process of managing and testing apps. Below, you'll find an overview of the key scripts and how to use them.
All the workflow can be manually triggered and configured from the **actions** page.

## Scripts Overview

### 1. Create App List

The `create_app_list` script is designed to parse GitHub repositories and generate a list of app variants. It takes a JSON file named `extra_info.json` (located in the `input_files/` directory) as a parameter, which includes essential information such as `build_path`. For each app, this script clones the repository and executes the `make listvariant` command to generate the list of variants.

**Output**: An output of this script can be found in `input_files/input.json`. It also incorporates all the information provided in `extra_info_file.json`.

**CI Usage**: This script is utilized by the `check_outdated_build_db.yaml` CI script.

**Note**: To use this script locally, you'll need to create a GitHub access token.

### 2. Build and Test and Scan

The `build_and_test` script performs either build or test or scan operations on the apps listed in the input
file generated previously.

**Build Operation**:
- Sets up repositories and SDK.
- Chooses the correct build path and extra flags based on the input file.
- Performs the build operation for the specified device.

**Test Operation**:
- Installs required dependencies.
- Executes pytest in the test directory specified in the input file for the specified device.

**Scan Operation**:
- Sets up repositories and SDK.
- Chooses the correct build path and extra flags based on the input file.
- Performs the scan build operation for the specified device.

**CI Usage**:
- `test_all.yml`: Tests devices.
- `build_all.yml`: Builds for selected devices.
- `scan_all.yml`: Scans for selected devices
- `refresh_inputs.yml`: Check whether the input list needs updating.

To reduce CI run times, the input file is automatically splitted into 10 sub-inputs, and then all the inputs are run through a matrix strategy.
### 3. Planned Improvements

- **Support for ZEMU Tests**

## Getting Started

To get started with this repository, follow these steps:

1. Clone the repository to your local machine.
2. Ensure you have set up a GitHub access token if you intend to use the scripts locally.
3. Make sure to run the scripts inside the ledger-app-dev-tools docker to use a proper build setup.

Alternatively you can run the script from the actions tab of the repo. 
You can view the result in the summary of the GH action: 
:red_circle: means a fail.
:heavy_check_mark: means success,
:fast_forward: means the action was explicitely blacklisted in the input file.
nothing: means there was no variant associated to the device when running make listvariants.
