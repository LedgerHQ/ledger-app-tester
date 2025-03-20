#!/bin/bash
#
# script to build an App and manage the status and log files
#

exeName=$(readlink "$0")
[[ -z ${exeName} ]] && exeName=$0

VERBOSE=false
IS_RUST=false

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
    echo "  -d <dir>    : Application test directory (relative to repository path)"
    echo "  -e <name>   : elf name"
    echo "  -f <flags>  : List of extra flags (separated with space)"
    echo "  -t <target> : Targeted device"
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

while getopts ":a:d:e:f:t:rvh" opt; do
    case ${opt} in
        a)  APP_NAME=${OPTARG}  ;;
        d)  TEST_DIR=${OPTARG} ;;
        e)  ELF_NAME=${OPTARG}  ;;
        f)  EXTRA_FLAGS=${OPTARG} ;;
        t)  TARGET=${OPTARG}    ;;
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
[[ -z "${ELF_NAME}" ]] && help "Error: Elf name not specified"
[[ -z "${TARGET}" ]] && help "Error: Target not specified"
[[ -z "${TEST_DIR}" ]] && help "Error: Test directory not specified"

FILE_STATUS="test_status_${APP_NAME}.md"
FILE_ERROR="test_errors_${APP_NAME}.md"

#===============================================================================
#
#     Main
#
#===============================================================================

# Check supported devices (with special check for NanoS+)
if [[ "${IS_RUST}" == "true" ]]; then
    ELF_FILE="${APP_NAME}/target/${TARGET/sp/splus}/release/${ELF_NAME}"
else
    ELF_FILE="${APP_NAME}/build/${TARGET/sp/s2}/bin/${ELF_NAME}"
fi
if [[ ! -f "${ELF_FILE}" ]]; then
    echo -n "|:black_circle:" >> "${FILE_STATUS}"
    [[ "${VERBOSE}" == "true" ]] && echo "${TARGET} not available."
    exit 0
fi

# shellcheck disable=SC2086
(cd "${TEST_DIR}" && pytest --tb=short -v --device="${TARGET}" ${EXTRA_FLAGS})
ERR=$?

if [[ ${ERR} -ne 0 ]]; then
    echo -n "|:x:" >> "${FILE_STATUS}"
    if [[ -f "${FILE_ERROR}" ]]; then
        echo -n ", ${TARGET}" >> "${FILE_ERROR}"
    else
        {
            echo -e "\t• ${APP_NAME}"
            echo -e -n "\t\t${TARGET}"
        } > "${FILE_ERROR}"
    fi
else
    echo -n "|:white_check_mark:" >> "${FILE_STATUS}"
fi

exit "${ERR}"
