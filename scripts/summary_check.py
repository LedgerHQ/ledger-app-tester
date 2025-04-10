#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to generate the summary report.
"""

import os
import logging
import sys
from typing import Optional, Tuple
from argparse import ArgumentParser, Namespace
from github import Github
from utils import logging_init, logging_set_level, set_gh_summary
from summary import errors_report, get_job_link


# ===============================================================================
#          Parse command line options
# ===============================================================================
def arg_parse() -> Namespace:
    """Parse the commandline options"""

    parser = ArgumentParser(description="Generate summary report for CI workflow")

    parser.add_argument("-t",
                        "--total_apps",
                        required=True,
                        type=int,
                        help="Total Apps count.")
    parser.add_argument("-e",
                        "--exclude",
                        required=False,
                        type=str,
                        help="List of excluded applications. "
                        "Accepts several successive values (separated with space). ")
    parser.add_argument("-j",
                        "--job",
                        required=True,
                        type=str,
                        help="Substring to check in jobs to get the URL.")

    parser.add_argument("-E",
                        "--Error",
                        required=False,
                        type=str,
                        help="Check Error files directory.")
    parser.add_argument("-C",
                        "--Check",
                        required=False,
                        type=str,
                        help="Check Status files directory.")
    parser.add_argument("-o",
                        "--output",
                        required=True,
                        type=str,
                        help="Error output file.")

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity.")

    return parser.parse_args()


# ===============================================================================
#          Apps status report
# ===============================================================================
def status_report(report_file: str,
                  run_id: int,
                  args: Namespace,
                  github_token: Optional[str] = None) -> Tuple[int, int]:
    """Generate the status report for the apps.

    Args:
        report_file: The file to write the report to.
        run_id: The workflow run ID.
        args: Command line arguments.
        github_token: GitHub token for authentication (optional).
    Returns:
        Tuple containing
         - The number of apps,
         - The number of check errors,
    """

    logging.info("Fetching jobs from GitHub")
    gh = Github(github_token) if github_token else Github()

    repo = gh.get_repo("LedgerHQ/ledger-app-tester")
    run = repo.get_workflow_run(run_id)
    jobs = list(run.jobs())

    nb_apps = 0
    nb_check_errors = 0

    lines = []
    # Format the header lines automatically
    headers = [" App Names ", " Jobs ", " Result "]
    lines.append("|" + "|".join(headers) + "|\n")
    lines.append("|" + "|".join(["-----------", ":----:", ":------:"]) + "|\n")

    # List all apps and their status, sorted alphabetically
    for cname in sorted(os.listdir(args.Check)):
        nb_apps += 1
        check_path = os.path.join(args.Check, cname)
        with open(check_path, encoding="utf-8") as infile:
            app_status = infile.readline()
        nb_check_errors += app_status.count(":x:")

        # Extract app name from file name
        app_name = os.path.splitext(os.path.basename(cname.split("_")[-1]))[0]

        # Construct the job status string
        job_status = f"|{get_job_link(app_name, args.job, jobs)}{app_status}"

        # Write the status to the report file
        app_url = f"https://github.com/LedgerHQ/{app_name}"
        lines.append(f"|[{app_name}]({app_url}){job_status}{app_status}\n")

    logging.info("Generating status report")
    with open(report_file, "w", encoding="utf-8") as outfile:
        outfile.writelines(lines)

    return nb_apps, nb_check_errors


# ===============================================================================
#          Apps status report
# ===============================================================================
def summary_report(github_event: str,
                   nb_apps_error: int,
                   nb_check_errors: int,
                   args: Namespace) -> None:
    """Generate the summary report for the apps.
    Args:
        github_event: The GitHub event name.
        nb_apps_error: The number of apps with errors.
        nb_check_errors: The number of check errors.
        args: Command line arguments.
    """

    logging.info("Generating summary report")

    # Header lines
    lines = [
        f":dart: Workflow event: {github_event}",
        f":rocket: Nb Apps checked: {args.total_apps}",
    ]
    # Error lines
    lines.append(f":loudspeaker: Nb Check Error(s) found: {nb_check_errors}")
    if nb_apps_error:
        lines.append(f":boom: Nb App(s) with error(s): {nb_apps_error}")
    # Excluded apps
    if args.exclude:
        lines.append(":mute: Excluded Apps:")
        for app in args.exclude.split(" "):
            lines.append(f"\t• {app}")
    lines.append("<br>")

    content = "\n".join(lines) + "\n"

    # Append app status details
    try:
        with open("app_status.md", encoding="utf-8") as infile:
            content += infile.read() + "\n<br>\n"
    except FileNotFoundError:
        logging.warning("File 'app_status.md' not found while generating summary")

    # Legend section
    legend = [
        "<details><summary>Legend</summary>",
        "",
        " - :white_check_mark: Success",
        " - :x: Failure",
        " - :construction: Workflow issue"
    ]
    legend.extend(["", "</details>"])
    content += "\n".join(legend) + "\n"

    with open("summary.md", "w", encoding="utf-8") as outfile:
        outfile.write(content)

    set_gh_summary("summary.md")


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
    github_event = os.environ.get("GH_EVENT_NAME")
    if github_event is None:
        logging.error("'GH_EVENT_NAME' environment variable is not set")
        sys.exit(1)

    # Processing
    # ----------
    logging.info("Generating '%s' summary...", github_event)

    # Generate reports
    if os.path.isdir("error"):
        nb_apps_error = errors_report(args.output, args.Error)
    else:
        nb_apps_error = 0
    nb_apps_analyzed, nb_check_errors = status_report("app_status.md",
                                                      int(workflow_run_id),
                                                      args,
                                                      github_token)

    # Check if apps are missing in the status report
    nb_apps_not_analyzed = args.total_apps - nb_apps_analyzed
    if nb_apps_not_analyzed != 0:
        set_gh_summary(f":warning: {nb_apps_not_analyzed} App(s) missing!!!\n<br>")

    # Generate full summary
    summary_report(github_event,
                   nb_apps_error,
                   nb_check_errors,
                   args)


if __name__ == "__main__":
    main()
