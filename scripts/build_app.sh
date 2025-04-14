#!/bin/bash
#
# script to Build an App and manage the status and log files
#

exeName=$(readlink "$0")
[[ -z ${exeName} ]] && exeName=$0
dirName=$(dirname "$exeName")

VERBOSE=false
IS_RUST=false
VAR_PARAM=""
VAR_VALUE=""

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
    echo "  -b <dir>    : Application build directory"
    echo "  -d <names>  : List of supported devices (separated with space)"
    echo "  -f <flags>  : List of extra flags (separated with space)"
    echo "  -m <mode>   : Required mode (scan, test or build)"
    echo "  -s <branch> : SDK branch"
    echo "  -P <name>   : Variant Param"
    echo "  -V <name>   : Variant Value"
    echo "  -r          : Rust application"
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

while getopts ":a:b:d:f:m:s:P:V:rvh" opt; do
    case ${opt} in
        a)  APP_NAME=${OPTARG}  ;;
        b)  BUILD_DIR=${OPTARG} ;;
        d)  DEVICES=${OPTARG}   ;;
        m)  MODE=${OPTARG}      ;;
        s)  BRANCH=${OPTARG}    ;;
        P)  VAR_PARAM=${OPTARG} ;;
        V)  VAR_VALUE=${OPTARG} ;;
        f)  EXTRA_FLAGS=${OPTARG} ;;
        r)  IS_RUST=true ;;
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
[[ -z "${BUILD_DIR}" ]] && help "Error: Build directory not specified"
[[ "${IS_RUST}" == "false" && -z "${BRANCH}" && -z "${MODE}" ]] && help "Error: Mode or Branch must be specified"

[[ -n "${VAR_PARAM}" && -z "${VAR_VALUE}" ]] && help "Error: Variant Value not specified"
[[ -z "${VAR_PARAM}" && -n "${VAR_VALUE}" ]] && help "Error: Variant Param not specified"

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
        git -C ${SDK_PATH} checkout "${BRANCH}"
    else
        case "${MODE}" in
            build) ;;
            test)
                # Using SDK from the container for the targeted device
                SDK_PATH="/opt/${target/s+/splus}-secure-sdk"
                ;;
            scan)
                # Using the HEAD of the dedicated API_LEVEL_xx branch for the targeted device
                VAL=$(jq --arg name "${target}" -r '[to_entries[] | select(.value[] | contains($name)) | select(.value[] | contains("-rc") | not) | .key | tonumber] | max' ${SDK_PATH}/api_levels.json)
                if [ -z "${VAL}" ]; then
                    echo "No API_LEVEL branch found. Keep master!"
                else
                    echo "API_LEVEL branch found: ${VAL}"
                    git -C ${SDK_PATH} checkout "API_LEVEL_${VAL}"
                fi
                EXTRA_FLAGS="${EXTRA_FLAGS} ENABLE_SDK_WERROR=1 scan-build"
                ;;
            *)    help "Error: Unknown mode ${MODE}" ;;
        esac
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
            echo "===== Compiling for VARIANT: ${VAR_PARAM} -> ${val}"
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
        echo "===== Compiling for default VARIANT"
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

DEVICES_LIST=$(jq -r '.[0].devices | join (" ")' "${dirName}/../input_files/devices_list.json")

FINAL_ERR=0
for target in ${DEVICES_LIST}; do

    # Check supported devices
    if [[ ! "${DEVICES}" =~ ${target} ]]; then

        echo -n "|:black_circle:" >> "${FILE_STATUS}"
        [[ "${VERBOSE}" == "true" ]] && echo "${target} not supported."

    else

        if [[ "${IS_RUST}" == "true" ]]; then
            build_RUST "${target}"
        else
            prepare_SDK "${target}"
            build_C "${target}"
        fi

        # Particular target name of Nanos+
        TARGET_BUILD="${target/s+/sp}"
        if [[ ${ERR} -ne 0 ]]; then
            echo -n "|:x:" >> "${FILE_STATUS}"
            if [[ -f "${FILE_ERROR}" ]]; then
                echo -n ", ${TARGET_BUILD}" >> "${FILE_ERROR}"
            else
                {
                    echo -e "\t• ${APP_NAME}"
                    echo -e -n "\t\t${TARGET_BUILD}"
                } > "${FILE_ERROR}"
            fi
        else
            echo -n "|:white_check_mark:" >> "${FILE_STATUS}"
        fi
        FINAL_ERR=$((FINAL_ERR + ERR))
    fi
done

exit "${FINAL_ERR}"
