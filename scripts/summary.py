#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to generate the summary report.
"""

import os
import logging
import sys
from typing import List, Optional, Tuple
from argparse import ArgumentParser, Namespace
from github import Github
from utils import logging_init, logging_set_level, set_gh_summary
from parse_all_apps import devices


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
                        help="Test Error files directory.")
    parser.add_argument("-T",
                        "--Test",
                        required=False,
                        type=str,
                        help="Test Status files directory.")
    parser.add_argument("-B",
                        "--Build",
                        required=False,
                        type=str,
                        help="Build Status files directory.")
    parser.add_argument("-o",
                        "--output",
                        required=True,
                        type=str,
                        help="Error output file.")
    parser.add_argument("-V", "--Variants", action="store_true", default=False, help="Handle Variants.")

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity.")

    return parser.parse_args()


# ===============================================================================
#          Apps error report
# ===============================================================================
def errors_report(report_file: str, indir: str) -> int:
    nb_apps = 0
    logging.info("Generating errors report")
    with open(report_file, "w", encoding="utf-8") as outfile:
        for filename in os.listdir(indir):
            nb_apps += 1
            with open(f"{indir}/{filename}", encoding="utf-8") as infile:
                outfile.write(infile.read())
                outfile.write("\n")
    return nb_apps


# ===============================================================================
#          Get job Link in GitHub
# ===============================================================================
def get_job_link(app_name: str, job_name: str, jobs) -> str:
    """Get the job link from GitHub.
    Args:
        app_name: The name of the app.
        job_name: The job name to search for.
        jobs: List of jobs from GitHub.
    Returns:
        The job link if found, otherwise 'N/A'.
    """

    job = next((job for job in jobs if app_name in job.name and job_name in job.name), None)
    if job:
        return f"[{job_name}]({job.html_url})"
    logging.warning("'%s' job not found for app '%s'", job_name, app_name)
    return "N/A"


# ===============================================================================
#          Generate full job Status
# ===============================================================================
def construct_job_status(app_name: str,
                         bname: str,
                         tdir: str,
                         build_status: List[str],
                         job_name: str,
                         jobs) -> Tuple[str, int]:
    """Construct the job status string.
    Args:
        app_name: The name of the app.
        bname: The name of the build file.
        tdir: The directory containing the test status files.
        build_status: The build status string.
        job_name: The job name to search for.
        jobs: List of jobs from GitHub.
    Returns:
        Job status line and nb errors.
    """

    tname = bname.replace("build", "test", 1)
    test_path = os.path.join(tdir, tname)
    try:
        with open(test_path, encoding="utf-8") as infile:
            test_status = infile.readline().split("|")[1:]
    except FileNotFoundError:
        logging.warning("File '%s' not found", test_path)
        test_status = [":construction:" for _ in build_status]

    # Combine build and test statuses
    merged_tokens = [
        "|:warning:" if b_status in (":x:", ":construction:")
        else ("|:black_circle:" if t_status == ":black_circle:" else f"|{t_status}")
        for b_status, t_status in zip(build_status, test_status)
    ]

    job_status = f"|{get_job_link(app_name, job_name, jobs)}"
    job_status += "<br>"
    job_status += f"{get_job_link(app_name, 'Test', jobs)}"
    job_status += "".join(merged_tokens)

    return job_status, test_status.count(":x:")


# ===============================================================================
#          Apps status report
# ===============================================================================
def status_report(report_file: str,
                  job_name: str,
                  run_id: int,
                  bdir: str,
                  tdir: Optional[str] = None,
                  github_token: Optional[str] = None) -> Tuple[int, int, int, int]:
    """Generate the status report for the apps.

    Args:
        report_file: The file to write the report to.
        job_name: The job name to search for in the workflow.
        run_id: The workflow run ID.
        bdir: The directory containing the build status files.
        tdir: The directory containing the test status files (optional).
        github_token: GitHub token for authentication (optional).
    Returns:
        Tuple containing
         - The number of apps,
         - The number of build errors,
         - The number of test errors,
         - The number of skipped errors.
    """

    logging.info("Fetching jobs from GitHub")
    gh = Github(github_token) if github_token else Github()

    repo = gh.get_repo("LedgerHQ/ledger-app-tester")
    run = repo.get_workflow_run(run_id)
    jobs = list(run.jobs())

    nb_apps = 0
    nb_build_errors = 0
    nb_test_errors = 0
    nb_skip_errors = 0

    lines = []
    # Format the header lines automatically
    headers = [" App Names ", " Jobs "] + [f" {d} " for d in devices]
    lines.append("|" + "|".join(headers) + "|\n")
    lines.append("|" + "|".join(["-----------", ":----:"] + [f":{'-'*len(d)}:" for d in devices]) + "|\n")

    # List all apps and their status, sorted alphabetically
    for bname in sorted(os.listdir(bdir)):
        nb_apps += 1
        build_path = os.path.join(bdir, bname)
        with open(build_path, encoding="utf-8") as infile:
            app_status = infile.readline()
        nb_build_errors += app_status.count(":x:")
        build_status = app_status.split("|")[1:]

        # Extract app name from file name
        app_name = os.path.splitext(os.path.basename(bname.split("_")[-1]))[0]

        # Construct the job status string
        if tdir is None:
            job_status = f"|{get_job_link(app_name, job_name, jobs)}{app_status}"
        else:
            # If test directory is provided, Analyze both Build and Test Status
            job_status, test_erros = construct_job_status(app_name,
                                                          bname,
                                                          tdir,
                                                          build_status,
                                                          job_name,
                                                          jobs)
            nb_test_errors += test_erros

        # Write the status to the report file
        app_url = f"https://github.com/LedgerHQ/{app_name}"
        lines.append(f"|[{app_name}]({app_url}){job_status}{app_status}\n")

        if app_status.count(":black_circle:") == len(devices):
            nb_skip_errors += 1

    logging.info("Generating status report")
    with open(report_file, "w", encoding="utf-8") as outfile:
        outfile.writelines(lines)

    return nb_apps, nb_build_errors, nb_test_errors, nb_skip_errors


# ===============================================================================
#          Apps status report
# ===============================================================================
def summary_report(github_event: str,
                   nb_apps_error: int,
                   nb_build_errors: int,
                   nb_test_errors: int,
                   nb_skip_errors: int,
                   args: Namespace) -> None:
    """Generate the summary report for the apps.
    Args:
        github_event: The GitHub event name.
        nb_apps_error: The number of apps with errors.
        nb_build_errors: The number of build errors.
        nb_test_errors: The number of test errors.
        nb_skip_errors: The number of skipped errors.
        args: Command line arguments.
    """

    logging.info("Generating summary report")

    # Header lines
    lines = [
        f":dart: Workflow event: {github_event}",
        f":pushpin: Variants: {'' if args.Variants else 'NOT '}included!",
        f":rocket: Nb Apps checked: {args.total_apps}",
    ]
    # Error lines
    if nb_skip_errors > 0:
        lines.append(f":no_entry: Nb Apps skipped: {nb_skip_errors}")
    lines.append(f":loudspeaker: Nb Build Error(s) found: {nb_build_errors}")
    if args.Test is not None:
        lines.append(f":loudspeaker: Nb Test Error(s) found: {nb_test_errors}")
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
        " - :black_circle: Not selected",
        " - :construction: Workflow issue"
    ]
    if args.Test is not None:
        legend.append(" - :warning: Build issue, No test!")
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
    nb_apps_analyzed, nb_build_errors, nb_test_errors, nb_skip_errors = status_report("app_status.md",
                                                                                      args.job,
                                                                                      int(workflow_run_id),
                                                                                      args.Build,
                                                                                      args.Test,
                                                                                      github_token)

    # Check if apps are missing in the status report
    nb_apps_not_analyzed = args.total_apps - nb_apps_analyzed
    if nb_apps_not_analyzed != 0:
        set_gh_summary(f":warning: {nb_apps_not_analyzed} App(s) missing!!!\n<br>")

    # Generate full summary
    summary_report(github_event,
                   nb_apps_error,
                   nb_build_errors,
                   nb_test_errors,
                   nb_skip_errors,
                   args)


if __name__ == "__main__":
    main()
