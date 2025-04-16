#!/bin/bash
#
# script to Build an App and manage the status and log files
#

exeName=$(readlink "$0")
[[ -z ${exeName} ]] && exeName=$0
dirName=$(dirname "$exeName")

VERBOSE=false
WITH_VARIANTS=false
VAR_PARAM=""
VAR_VALUE=""
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
    echo "  -m <mode>   : Required mode (scan, test or build)"
    echo "  -s <branch> : SDK branch"
    echo "  -V          : Build all Variants"
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

while getopts ":a:m:s:Vvh" opt; do
    case ${opt} in
        a)  APP_NAME=${OPTARG}  ;;
        m)  MODE=${OPTARG}      ;;
        s)  BRANCH=${OPTARG}    ;;
        V)  WITH_VARIANTS=true  ;;
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

FILE_STATUS="build_status_${APP_NAME}.md"
FILE_ERROR="build_errors_${APP_NAME}.md"

#===============================================================================
#
#     Build Rust application
#
#===============================================================================
build_RUST() {
    local target="$1"
    local CURRENT_DIR=""
    local TARGET_BUILD=""

    CURRENT_DIR=$(pwd)
    TARGET_BUILD="${target/s+/splus}"
    cd "${APP_NAME}/${BUILD_DIR}" || exit 1
    case "${MODE}" in
        build|test)
            cargo +$RUST_NIGHTLY update ledger_device_sdk
            cargo +$RUST_NIGHTLY update ledger_secure_sdk_sys
            # Build, with particular case of Nanos+
            cargo ledger build "${TARGET_BUILD}"
            ERR=$?
            ;;
        scan)
            cargo +$RUST_NIGHTLY clippy --target "${TARGET_BUILD}" -- -Dwarnings
            ERR=$?
            ;;
    esac
    cd "${CURRENT_DIR}" || exit 1

}

#===============================================================================
#
#     Prepare SDK path and branch
#
#===============================================================================
prepare_SDK() {
    local target="$1"

    # Prepare SDK branch
    SDK_PATH="/opt/ledger-secure-sdk"
    if [[ -n "${BRANCH}" ]]; then
        [[ "${VERBOSE}" == "true" ]] && echo "Selecting branch '${BRANCH}' in ${SDK_PATH}."
        git -C ${SDK_PATH} checkout "${BRANCH}"
    else
        case "${MODE}" in
            build)
                [[ "${VERBOSE}" == "true" ]] && echo "Selecting branch 'master' in ${SDK_PATH}."
                git -C ${SDK_PATH} checkout master
                ;;
            test)
                # Using SDK from the container for the targeted device
                SDK_PATH="/opt/${target/s+/splus}-secure-sdk"
                [[ "${VERBOSE}" == "true" ]] && echo "Selecting default ${SDK_PATH}."
                ;;
            scan)
                # Using the HEAD of the dedicated API_LEVEL_xx branch for the targeted device
                VAL=$(jq --arg name "${target}" -r '[to_entries[] | select(.value[] | contains($name)) | select(.value[] | contains("-rc") | not) | .key | tonumber] | max' ${SDK_PATH}/api_levels.json)
                if [ -z "${VAL}" ]; then
                    BRANCH="master"
                    [[ "${VERBOSE}" == "true" ]] && echo "No API_LEVEL branch found. Keep master!"
                else
                    BRANCH="API_LEVEL_${VAL}"
                    [[ "${VERBOSE}" == "true" ]] && echo "Selecting branch '${BRANCH}' in ${SDK_PATH}."
                fi
                git -C ${SDK_PATH} checkout "${BRANCH}"
                ;;
            *)    help "Error: Unknown mode ${MODE}" ;;
        esac
    fi
}

#===============================================================================
#
#     Prepare Build Flags
#
#===============================================================================
prepare_Flags() {
    case "${MODE}" in
        build) ;;
        test)
            APP_FLAGS=$(jq --arg name "${APP_NAME}" -r '.[] | select(.name == $name) | .build_flags' ledger-app-tester/input_files/test_info.json)
            if [ "${APP_FLAGS}" != null ] && [ -n "${APP_FLAGS}" ]; then
                echo "Found Extra flags: ${APP_FLAGS}"
                EXTRA_FLAGS="${APP_FLAGS}"
            fi
            ;;
        scan)
            EXTRA_FLAGS="ENABLE_SDK_WERROR=1 scan-build"
            ;;
        *)    help "Error: Unknown mode ${MODE}" ;;
    esac
}

#===============================================================================
#
#     Get Available Variants
#
#===============================================================================
get_Variants() {
    local target="$1"
    local sdk_path="/opt/ledger-secure-sdk"
    local variants=""
    local target_build=""

    if [[ "${SDK}" == "rust" ]]; then
        [[ "${VERBOSE}" == "true" ]] && echo "Variants not supported on Rust Apps."
        return
    fi
    if [[ "${WITH_VARIANTS}" == "false" ]]; then
        [[ "${VERBOSE}" == "true" ]] && echo "Variants not requested."
        return
    fi

    # Particular target name of Nanos+
    target_build="${target/s+/s2}"
    # shellcheck disable=SC2068
    variants=$(TARGET="${target_build}" BOLOS_SDK="${sdk_path}" make -C "${APP_NAME}/${BUILD_DIR}" listvariants 2>/dev/null | grep VARIANTS)

    if [[ -n "${variants}" ]]; then
        VAR_PARAM=$(echo "${variants}" | cut -d' ' -f2)
        VAR_VALUE=$(echo "${variants}" | cut -d' ' -f3-)
        [[ "${VERBOSE}" == "true" ]] && echo "Found Variants: ${VAR_PARAM} -> ${VAR_VALUE}"
    else
        echo "No variants found."
    fi
}

#===============================================================================
#
#     Build C application
#
#===============================================================================
build_C() {
    local target="$1"

    local ARGS=""
    local BUILD_ARGS=""
    local TARGET_BUILD=""
    local val=""

    # Particular target name of Nanos+
    TARGET_BUILD="${target/s+/s2}"
    # Prepare make arguments
    ARGS=(-j -C "${APP_NAME}/${BUILD_DIR}")
    if [[ -n "${VAR_PARAM}" ]]; then
        for val in ${VAR_VALUE}; do
            echo "----------------------------------------------------"
            echo "     Compiling VARIANT: ${VAR_PARAM} -> ${val}"
            echo "----------------------------------------------------"
            BUILD_ARGS=("${ARGS[@]}")
            # Clean
            # shellcheck disable=SC2068
            TARGET="${TARGET_BUILD}" BOLOS_SDK="${SDK_PATH}" make ${BUILD_ARGS[@]} clean
            # Build
            BUILD_ARGS+=("${VAR_PARAM}=${val}")
            BUILD_ARGS+=("${EXTRA_FLAGS}")
            # shellcheck disable=SC2068
            # shellcheck disable=SC2086
            TARGET="${TARGET_BUILD}" BOLOS_SDK="${SDK_PATH}" make ${BUILD_ARGS[@]}
            ERR=$?
            if [[ ${ERR} -ne 0 ]]; then
                break
            fi
        done
    else
        if [[ "${WITH_VARIANTS}" == "true" ]]; then
            echo "----------------------------------------------------"
            echo "     Compiling default VARIANT"
            echo "----------------------------------------------------"
        fi
        BUILD_ARGS=("${ARGS[@]}")
        BUILD_ARGS+=("${EXTRA_FLAGS}")
        # Build
        # shellcheck disable=SC2068
        TARGET="${TARGET_BUILD}" BOLOS_SDK="${SDK_PATH}" make ${BUILD_ARGS[@]}
        ERR=$?
    fi
}

#===============================================================================
#
#     Main
#
#===============================================================================

ALL_DEVICES_LIST=$(jq -r '.[0].devices | join (" ")' "${dirName}/../input_files/devices_list.json")

SUPPORTED_DEVICES=$(ledger-manifest -od "${APP_NAME}/ledger_app.toml" -j   | jq -r '.devices | join(" ")')
BUILD_DIR=$(ledger-manifest -ob "${APP_NAME}/ledger_app.toml")
SDK=$(ledger-manifest -os "${APP_NAME}/ledger_app.toml")
SDK=${SDK,,}

prepare_Flags

FINAL_ERR=0
for target in ${ALL_DEVICES_LIST}; do

    echo "#########################################################################"
    echo "     Building for device ${target}"
    echo "#########################################################################"
    # Check supported devices
    if [[ ! "${SUPPORTED_DEVICES}" =~ ${target} ]]; then

        echo -n "|:black_circle:" >> "${FILE_STATUS}"
        [[ "${VERBOSE}" == "true" ]] && echo "${target} not supported."

    else

        if [[ "${SDK}" == "rust" ]]; then
            build_RUST "${target}"
        else
            prepare_SDK "${target}"
            get_Variants "${target}"
            build_C "${target}"
        fi

        # Particular target name of Nanos+
        TARGET_BUILD="${target/s+/sp}"
        if [[ ${ERR} -ne 0 ]]; then
            echo -n "|:x:" >> "${FILE_STATUS}"
            if [[ -f "${FILE_ERROR}" ]]; then
                echo -n ", ${TARGET_BUILD}" >> "${FILE_ERROR}"
            else
                echo -e -n "\t• ${APP_NAME}: ${TARGET_BUILD}" > "${FILE_ERROR}"
            fi
        else
            echo -n "|:white_check_mark:" >> "${FILE_STATUS}"
        fi
        FINAL_ERR=$((FINAL_ERR + ERR))
    fi
done

exit "${FINAL_ERR}"
