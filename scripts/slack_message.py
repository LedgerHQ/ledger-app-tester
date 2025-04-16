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
from typing import Any
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
    parser.add_argument("-m",
                        "--missing",
                        required=True,
                        type=str,
                        help="Nb of Missing Apps in summary.")
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


def prepare_slack_payload(args: Namespace, status: str, run_id: str, status_detail: str) -> dict:
    """
    Prepares a JSON payload for sending a Slack message using slackapi/slack-github-action@v2.

    Args:
        args: The command line arguments containing the title, devices, and other parameters.
        status: A short status string (e.g., ":red-cross: Fail").
        status_detail: A detailed string that might contain newlines for formatting.

    Returns:
        A JSON string representing the Slack message payload.
    """

    title = f"*{args.title}*"
    if args.devices:
        title += f" on [{', '.join(args.devices)}]"
    url = f"<https://github.com/LedgerHQ/ledger-app-tester/actions/runs/{run_id}|View {args.title} on GitHub>"

    blocks: list[dict[str, Any]] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": title
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": status
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": url
            }
        }
    ]
    if status_detail:
        context_block = {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Failed for:\n{status_detail}"
                }
            ]
        }
        blocks.append(context_block)

    return {"blocks": blocks}


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
    elif args.missing and int(args.missing) > 0:
        status = f":rotating_light: Missing {args.missing} Apps in summary"
    else:
        status = ":large_green_circle: Success"

    # Processing
    # ----------
    logging.info("Preparing JSON data with workflow result")
    content = ""
    if args.errors:
        with open(args.errors, encoding="utf-8") as f:
            content = f.read()
    slack_json = prepare_slack_payload(args, status, run_id, content)

    logging.debug("JSON_DATA:\n%s", json.dumps(slack_json, indent=4))

    if args.json:
        with open(args.json, 'w', encoding="utf-8") as f:
            json.dump(slack_json, f, indent=1)


if __name__ == "__main__":
    main()
