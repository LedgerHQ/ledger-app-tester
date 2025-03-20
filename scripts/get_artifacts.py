#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to list and retrieve artifacts.
"""

import logging
import os
import sys
from argparse import ArgumentParser, Namespace
from github import Github
from utils import logging_init, logging_set_level, set_gh_output


# ===============================================================================
#          Parse command line options
# ===============================================================================
def arg_parse() -> Namespace:
    """Parse the commandline options"""

    parser = ArgumentParser("Selects applications and dump relevant workflow data from their "
                            "manifests as a JSON")
    parser.add_argument("-p",
                        "--pattern",
                        required=True,
                        type=str,
                        help="Artifact pattern to search.")
    parser.add_argument("-s",
                        "--substr",
                        required=False,
                        type=str,
                        help="Substring to remove from artifact results.")
    parser.add_argument("-e",
                        "--exist",
                        required=False,
                        type=str,
                        help="Environment variable name for existing pattern.")
    parser.add_argument("-r",
                        "--result",
                        required=False,
                        type=str,
                        help="Environment variable name for results.")

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity.")

    return parser.parse_args()


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
    workflow_run_id = os.environ.get("GH_RUN_ID")
    if workflow_run_id is None:
        logging.error("'GH_RUN_ID' environment variable is not set")
        sys.exit(1)

    # Processing
    # ----------
    logging.info("Fetching artifacts from GitHub")
    gh = Github(github_token) if github_token else Github()

    repo = gh.get_repo("LedgerHQ/ledger-app-tester")
    workflow_run = repo.get_workflow_run(int(workflow_run_id))
    artifacts = workflow_run.get_artifacts()

    artifact_list = [a.name for a in artifacts if args.pattern in a.name]
    if args.substr:
        artifact_list = [a.replace(args.substr, "") for a in artifact_list]

    if len(artifact_list) == 0:
        logging.warning("Artifact '%s' NOT found", args.pattern)
        sys.exit(0)

    if args.result:
        set_gh_output(args.result, f"{artifact_list}")
    else:
        print(f"Found {len(artifact_list)} artifact(s):\n{artifact_list}")

    if args.exist:
        res: bool = len(artifact_list) > 0
        set_gh_output(args.exist, f"{res}")


if __name__ == "__main__":
    main()
