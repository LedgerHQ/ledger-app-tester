#!/bin/bash
#
# script to build an App and manage the status and log files
#

exeName=$(readlink "$0")
[[ -z ${exeName} ]] && exeName=$0

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
    echo "  -b <dir>    : Application build directory (relative to repository path)"
    echo "  -t <target> : Targeted device"
    echo "  -d <names>  : List of supported devices (separated with space)"
    echo "  -f <flags>  : List of extra flags (separated with space)"
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

while getopts ":a:b:t:d:f:P:V:rvh" opt; do
    case ${opt} in
        a)  APP_NAME=${OPTARG}  ;;
        b)  BUILD_DIR=${OPTARG} ;;
        t)  TARGET=${OPTARG}    ;;
        d)  DEVICES=${OPTARG}   ;;
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
[[ -z "${TARGET}" ]] && help "Error: TARGET not specified"

[[ -n "${VAR_PARAM}" && -z "${VAR_VALUE}" ]] && help "Error: Variant Value not specified"
[[ -z "${VAR_PARAM}" && -n "${VAR_VALUE}" ]] && help "Error: Variant Param not specified"

FILE_STATUS="build_status_${APP_NAME}.md"
FILE_ERROR="build_errors_${APP_NAME}.md"

#===============================================================================
#
#     Main
#
#===============================================================================

# Check supported devices
if [[ ! "${DEVICES}" =~ ${TARGET} ]]; then
    echo -n "|:black_circle:" >> "${FILE_STATUS}"
    [[ "${VERBOSE}" == "true" ]] && echo "${TARGET} not supported."
    exit 0
fi

if [[ "${IS_RUST}" == "true" ]]; then
    CURRENT_DIR=$(pwd)
    cd "${BUILD_DIR}" || exit 1
    cargo +$RUST_NIGHTLY update ledger_device_sdk
    cargo +$RUST_NIGHTLY update ledger_secure_sdk_sys
    # Build, with particular case of Nanos+
    cargo ledger build "${TARGET/s+/splus}"
    ERR=$?
    cd "${CURRENT_DIR}" || exit 1
else
    # Prepare make arguments
    ARGS=(-j -C "${BUILD_DIR}" "${EXTRA_FLAGS}")
    # Particular target name of Nanos+
    TARGET_BUILD="${TARGET/s+/s2}"
    if [[ -n "${VAR_PARAM}" ]]; then
        for val in ${VAR_VALUE}; do
            echo "===== Compiling for VARIANT: ${VAR_PARAM} -> ${val}"
            BUILD_ARGS=("${ARGS[@]}")
            BUILD_ARGS+=("${VAR_PARAM}=${val}")
            # Clean
            # shellcheck disable=SC2068
            TARGET="${TARGET_BUILD}" BOLOS_SDK="$GITHUB_WORKSPACE/sdk" make ${BUILD_ARGS[@]} clean
            # Build
            # shellcheck disable=SC2068
            # shellcheck disable=SC2086
            TARGET="${TARGET_BUILD}" BOLOS_SDK="$GITHUB_WORKSPACE/sdk" make ${BUILD_ARGS[@]}
            ERR=$?
            if [[ ${ERR} -ne 0 ]]; then
                break
            fi
        done
    else
        echo "===== Compiling for default VARIANT"
        # Build
        # shellcheck disable=SC2068
        TARGET="${TARGET_BUILD}" BOLOS_SDK="$GITHUB_WORKSPACE/sdk" make ${ARGS[@]}
        ERR=$?
    fi
fi

# Particular target name of Nanos+
TARGET_BUILD="${TARGET/s+/sp}"
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

exit "${ERR}"
