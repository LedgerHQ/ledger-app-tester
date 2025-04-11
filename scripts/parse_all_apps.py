#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to list the available applications on the LedgerHQ GitHub organization and dump the
relevant workflow data from their manifests as a JSON file.
"""

import os
import json
import logging
from typing import List, Optional
from argparse import ArgumentParser, Namespace
from dataclasses import asdict, dataclass, field
from ledgered.github import AppRepository, Condition, GitHubLedgerHQ
from utils import logging_init, logging_set_level, set_gh_output


devices = ["nanos+", "nanox", "stax", "flex"]
sdks = ["C", "Rust"]


@dataclass
class AppInfo:
    """Application information"""

    repo_name: str
    sdk: str
    devices: list[str]
    build_directory: str
    variant_param: Optional[str] = None
    variants_values: List[str] = field(default_factory=list)

    def __init__(self, app: AppRepository, filtered_devices: set[str]):
        self.build_directory = str(app.manifest.app.build_directory)
        if self.build_directory[-1] == ".":
            self.build_directory += "/"
        else:
            self.build_directory = f"./{self.build_directory}/"
        self.devices = sorted(list(set(app.manifest.app.devices) & set(filtered_devices)))
        self.repo_name = app.name
        self.sdk = app.manifest.app.sdk
        self.variant_param = app.variant_param
        self.variants_values = app.variants


# ===============================================================================
#          Parse command line options
# ===============================================================================
def arg_parse() -> Namespace:
    """Parse the commandline options"""

    parser = ArgumentParser("Selects applications and dump relevant workflow data from their "
                            "manifests as a JSON")
    parser.add_argument("-d",
                        "--devices",
                        nargs="+",
                        required=False,
                        default=["all"],
                        type=str,
                        choices=sorted(devices + ["nanosp", "all"]),
                        help="List of devices to filter on. "
                        "Accepts several successive values (separated with space).  Defaults to 'all'.")
    parser.add_argument("-e",
                        "--exclude",
                        nargs="+",
                        required=False,
                        default=[],
                        help="List of applications to exclude from the list. "
                        "Accepts several successive values (separated with space). ")
    parser.add_argument("-o",
                        "--only",
                        nargs="+",
                        required=False,
                        default=[],
                        help="List of applications to select. "
                        "Accepts several successive values (separated with space). "
                        "Takes precedence other `--exclude`.")
    parser.add_argument("-l",
                        "--limit",
                        required=False,
                        default=0,
                        type=int,
                        help="Limit the number of applications to collect.")
    parser.add_argument("-s",
                        "--sdk",
                        required=False,
                        default="all",
                        type=str,
                        choices=["all"] + sorted(sdks + [s.lower() for s in sdks]),
                        help="SDK to filter on. Only apps using the SDK are selected. "
                        "Defaults to '%(default)s'.")
    parser.add_argument("-j",
                        "--json",
                        required=False,
                        type=str,
                        help="Variable name for the JSON data and output file name.")
    parser.add_argument("-n",
                        "--nb",
                        required=False,
                        type=str,
                        help="Output variable name for the Nb of Apps.")

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity.")

    args = parser.parse_args()

    # Devices filtering
    selected_devices = []
    for d in args.devices:
        if d.lower() == "nanosp":
            d = "nanos+"
        if d.lower() in devices:
            selected_devices.append(d)
            continue
        if d.lower() == "all":
            selected_devices = devices
            break
    args.devices = selected_devices

    # SDK filtering
    selected_sdk: list[str]
    if args.sdk == "all":
        selected_sdk = [s.lower() for s in sdks]
    else:
        selected_sdk = [args.sdk]
    args.sdk = selected_sdk

    # lowering every string in the lists, easier to compare
    args.sdk = [name.lower() for name in args.sdk]
    if args.only:
        # `only` takes precedence over `exclude`, so `exclude` is emptied (ignored)
        args.only = [name.lower() for name in args.only]
        args.exclude = []
    args.exclude = [name.lower() for name in args.exclude]

    return args


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
    github_token = os.environ.get("GH_TOKEN")

    selected_apps: List[dict] = []
    app: AppRepository

    # Processing
    # ----------
    logging.info("Fetching application repositories from GitHub")
    gh = GitHubLedgerHQ(github_token) if github_token else GitHubLedgerHQ()
    apps = gh.apps.filter(archived=Condition.WITHOUT,
                          only_list=args.only,
                          exclude_list=args.exclude,
                          sdk=args.sdk)

    apps.sort(key=lambda r: r.name)
    if args.limit and len(apps) > args.limit:
        logging.info("Limiting to %d applications", args.limit)
        del apps[(args.limit - len(apps)):]

    for app in apps:
        logging.info("Managing app '%s'", app.name)
        selected_apps.append(asdict(AppInfo(app, args.devices)))

    if args.json:
        set_gh_output(args.json, json.dumps(selected_apps))
        with open(f"{args.json}.json", "w", encoding="utf-8") as f:
            json.dump(selected_apps, f)
    else:
        print(json.dumps(selected_apps, indent=4))

    if args.nb:
        set_gh_output(args.nb, f"{len(selected_apps)}")
    else:
        print(f"Nb of Apps: {len(selected_apps)}")


if __name__ == "__main__":
    main()
