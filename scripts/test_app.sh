#!/bin/bash
#
# script to Test an App and manage the status and log files
#

exeName=$(readlink "$0")
[[ -z ${exeName} ]] && exeName=$0
dirName=$(dirname "$exeName")

VERBOSE=false
EXTRA_FLAGS=""

#===============================================================================
#
#     help - Prints script help and usage
#
#===============================================================================
# shellcheck disable=SC2154  # var is referenced but not assigned
help() {
    local err="$1"

    [[ -n "${err}" ]] && echo "${err}"

    echo
    echo "Usage: ${exeName} <options>"
    echo
    echo "Options:"
    echo
    echo "  -a <name>   : App name"
    echo "  -v          : Verbose mode"
    echo "  -h          : Displays this help"
    echo
    exit 1
}

#===============================================================================
#
#     Parsing parameters
#
#===============================================================================

while getopts ":a:vh" opt; do
    case ${opt} in
        a)  APP_NAME=${OPTARG}  ;;
        v)  VERBOSE=true ;;
        h)  help ;;

        \?) echo "Unknown option: -${OPTARG}" >&2; exit 1;;
        : ) echo "Missing option argument for -${OPTARG}" >&2; exit 1;;
        * ) echo "Unimplemented option: -${OPTARG}" >&2; exit 1;;
    esac
done

#===============================================================================
#
#     Checking parameters
#
#===============================================================================

[[ -z "${APP_NAME}" ]] && help "Error: Application name not specified"

FILE_STATUS="test_status_${APP_NAME}.md"
FILE_ERROR="test_errors_${APP_NAME}.md"

#===============================================================================
#
#     Prepare Build Flags
#
#===============================================================================
prepare_Flags() {
    APP_FLAGS=$(jq --arg name "${APP_NAME}" -r '.[] | select(.name == $name) | .test_flags' ledger-app-tester/input_files/test_info.json)
    if [ "${APP_FLAGS}" != null ] && [ -n "${APP_FLAGS}" ]; then
        echo "Found Test flags: ${APP_FLAGS}"
        EXTRA_FLAGS="${APP_FLAGS}"
    fi
}

#===============================================================================
#
#     Main
#
#===============================================================================

ALL_DEVICES_LIST=$(jq -r '.[0].devices | join (" ")' "${dirName}/../input_files/devices_list.json")

TEST_DIR=$(ledger-manifest -otp "${APP_NAME}/ledger_app.toml")
SDK=$(ledger-manifest -os "${APP_NAME}/ledger_app.toml")
SDK=${SDK,,}

prepare_Flags

FINAL_ERR=0
for target in ${ALL_DEVICES_LIST}; do

    echo "#########################################################################"
    echo "     Running Tests on device ${target}"
    echo "#########################################################################"
    # Determine the elf filename
    if [[ "${SDK}" == "rust" ]]; then
        if [ -f "${APP_NAME}/Cargo.toml" ]; then
            ELF_NAME=$(toml get --toml-path "${APP_NAME}/Cargo.toml" package.name)
        else
            ELF_NAME="${APP_NAME}"
        fi
        ELF_FILE="${APP_NAME}/target/${target/s+/splus}/release/${ELF_NAME}"
    else
        ELF_FILE="${APP_NAME}/build/${target/s+/s2}/bin/app.elf"
    fi

    # Check supported devices
    if [[ ! -f "${ELF_FILE}" ]]; then
        echo -n "|:black_circle:" >> "${FILE_STATUS}"
        [[ "${VERBOSE}" == "true" ]] && echo "${target} not available."

    else

        # Particular target name of Nanos+
        TARGET_TEST="${target/s+/sp}"

        # shellcheck disable=SC2086
        (cd "${APP_NAME}/${TEST_DIR}" && pytest --tb=short -v --device="${TARGET_TEST}" ${EXTRA_FLAGS})
        ERR=$?

        if [[ ${ERR} -ne 0 ]]; then
            echo -n "|:x:" >> "${FILE_STATUS}"
            if [[ -f "${FILE_ERROR}" ]]; then
                echo -n ", ${TARGET_TEST}" >> "${FILE_ERROR}"
            else
                echo -e -n "\t• ${APP_NAME}: ${TARGET_TEST}" > "${FILE_ERROR}"
            fi
        else
            echo -n "|:white_check_mark:" >> "${FILE_STATUS}"
        fi
        FINAL_ERR=$((FINAL_ERR + ERR))
    fi
done

exit "${FINAL_ERR}"
