#!/bin/bash
#
# script to Check an App and manage the status and log files
#

exeName=$(readlink "$0")
[[ -z ${exeName} ]] && exeName=$0

VERBOSE=false

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
    echo "  -a <dir>    : App directory"
    echo "  -b <dir>    : Application build directory (relative to the App directory)"
    echo "  -t <target> : Targeted device"
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

while getopts ":a:b:t:vh" opt; do
    case ${opt} in
        a)  APP_DIR=${OPTARG}  ;;
        b)  BUILD_DIR=${OPTARG} ;;
        t)  TARGET=${OPTARG}    ;;
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

[[ -z "${APP_DIR}" ]] && help "Error: Application directory not specified"
[[ -z "${BUILD_DIR}" ]] && help "Error: Build directory not specified"

FILE_STATUS="check_status_${APP_DIR}.md"
FILE_ERROR="check_errors_${APP_DIR}.md"

#===============================================================================
#
#     Main
#
#===============================================================================

# Prepare make arguments
ARGS=(-a "$(readlink -f "${APP_DIR}")" -b "${BUILD_DIR}")
[[ "${VERBOSE}" == "true" ]] && ARGS+=(-v)

if [[ -n "${TARGET}" ]]; then
    # Particular target name of Nanos+
    TARGET_BUILD="${TARGET/s+/sp}"
    SDK_PATH="${TARGET_BUILD^^}_SDK"
    ARGS+=(-t "${TARGET_BUILD}")
else
    SDK_PATH="/opt/ledger-secure-sdk"
fi
[[ "${VERBOSE}" == "true" ]] && echo "Selected SDK: ${SDK_PATH}"
# Check
# shellcheck disable=SC2068
(cd "${APP_DIR}" && BOLOS_SDK="${SDK_PATH}" /opt/enforcer.sh ${ARGS[@]})
ERR=$?

if [[ ${ERR} -ne 0 ]]; then
    echo -e "\t• ${APP_DIR}" > "${FILE_ERROR}"
fi

if [[ -f /tmp/check_status.md ]]; then
    cp /tmp/check_status.md "${FILE_STATUS}"
elif [[ ${ERR} -ne 0 ]]; then
    echo -n "|:x:" > "${FILE_STATUS}"
else
    echo -n "|:white_check_mark:" > "${FILE_STATUS}"
fi

exit "${ERR}"
