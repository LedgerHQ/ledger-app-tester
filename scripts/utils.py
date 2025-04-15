import os
import json
import logging


def logging_init() -> None:
    """Initialize the logger"""

    logging.root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logging.root.addHandler(handler)


def logging_set_level(verbose: int) -> None:
    """Set the logger level"""

    if verbose == 1:
        logging.root.setLevel(logging.INFO)
    elif verbose > 1:
        logging.root.setLevel(logging.DEBUG)


def set_gh_output(name: str, value: str) -> None:
    """Sets an output variable for a GitHub Actions workflow.
       This is used to pass data between steps in a workflow.

    Args:
        name: Name of the output variable
        value: Value of the output variable
    """

    # Check if the GITHUB_OUTPUT environment variable is set
    gh = os.environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a", encoding="utf-8") as outfile:
            outfile.write(f"{name}={value}\n")


def set_gh_summary(value: str) -> None:
    """Sets a summary status for a GitHub Actions workflow.
       This is used to write the summary of the workflow run.

    Args:
        value: Summary content (or filename)
    """

    # Check if the GITHUB_STEP_SUMMARY environment variable is set
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        with open(gh, "a", encoding="utf-8") as outfile:
            try:
                with open(value, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read())
            except FileNotFoundError:
                # Consider this is a simple string
                outfile.write(f"{value}\n")


def get_full_devices() -> list:
    """Get the full list of devices from the config file.

    Returns:
        list: List of devices
    """

    # Get the directory of the current script
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # Construct the absolute path to the JSON file
    file_path = os.path.join(script_directory, "../input_files/devices_list.json")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)
        devices = data[0]["devices"]
    return devices
