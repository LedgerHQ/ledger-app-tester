#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to prepare the slack message in a JSON format.
"""

import os
import sys
import json
import logging
import re
from argparse import ArgumentParser, Namespace
from utils import logging_init, logging_set_level, get_full_devices


devices = get_full_devices()


# ===============================================================================
#          Parse command line options
# ===============================================================================
def arg_parse() -> Namespace:
    """Parse the commandline options"""

    parser = ArgumentParser("Prepare a JSON data with workflow result to send it to Slack")
    parser.add_argument("-t",
                        "--title",
                        required=True,
                        type=str,
                        help="Message title.")
    parser.add_argument("-e",
                        "--errors",
                        required=False,
                        type=str,
                        help="Details report file.")
    parser.add_argument("-j",
                        "--json",
                        type=str,
                        help="Output file for the JSON data")
    parser.add_argument("-d",
                        "--devices",
                        nargs="+",
                        required=False,
                        default=["all"],
                        type=str,
                        choices=sorted(devices + ["nanosp", "all"]),
                        help="List of devices to filter on. "
                        "Accepts several successive values (separated with space).  Defaults to 'all'.")
    parser.add_argument("-n",
                        "--nb",
                        required=False,
                        type=str,
                        help="Total Nb of Apps.")

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity.")

    return parser.parse_args()


# ===============================================================================
#          Count the apps listed in a file
# ===============================================================================
def count_apps(filepath: str) -> int:
    """Counts the number of 'app-' patterns in a file."""

    try:
        with open(filepath, encoding="utf-8") as file:
            content = file.read()
            pattern = r"• app-"  # Raw string for regex
            matches = re.findall(pattern, content, re.MULTILINE)
            return len(matches)
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        return 0


# ===============================================================================
#          MAIN
# ===============================================================================
def main() -> None:
    """Main function"""

    logging_init()

    # Arguments parsing
    # -----------------
    args = arg_parse()

    # Arguments checking
    # ------------------
    logging_set_level(args.verbose)

    # GitHub environment variables
    run_id = os.environ.get("GH_RUN_ID")
    if run_id is None:
        logging.error("'GH_RUN_ID' environment variable is not set")
        sys.exit(1)

    if args.errors:
        fail_count = count_apps(args.errors)
        status = f":red-cross: Fail for {fail_count} / {args.nb} Apps"
    else:
        status = ":large_green_circle: Success"

    # Processing
    # ----------
    logging.info("Preparing JSON data with workflow result")
    slack_json = {}
    slack_json["title"] = f"{args.title} on [{', '.join(args.devices)}]"
    slack_json["status"] = status
    slack_json["url"] = f"https://github.com/LedgerHQ/ledger-app-tester/actions/runs/{run_id}"
    if args.errors:
        with open(args.errors, encoding="utf-8") as f:
            content = f.read()
        slack_json["status_detail"] = f"Failed for:\n{content}"

    logging.debug("JSON_DATA:\n%s", json.dumps(slack_json, indent=4))

    if args.json:
        with open(args.json, 'w', encoding="utf-8") as f:
            json.dump(slack_json, f, indent=1)


if __name__ == "__main__":
    main()
