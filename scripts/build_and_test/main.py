import json
from pathlib import Path
from argparse import ArgumentParser
from build_app import build_all_devices
from test_app import test_all_devices
from scan_app import scan_all_devices
from device import Devices
from utils import git_setup, merge_json
from sha1 import override_sha1

SDK_NAME = "sdk"
SDK_URL = "https://github.com/LedgerHQ/ledger-secure-sdk.git"
SDK_BRANCH = "origin/master"


if __name__ == "__main__":
    parser = ArgumentParser()
    input_json = {}

    parser.add_argument("--skip_setup", action='store_true')

    # Devices
    parser.add_argument("--all", action='store_true')
    parser.add_argument("--nanos", action='store_true')
    parser.add_argument("--nanosp", action='store_true')
    parser.add_argument("--nanox", action='store_true')
    parser.add_argument("--stax", action='store_true')

    parser.add_argument("--test", action='store_true')
    parser.add_argument("--build", action='store_true')
    parser.add_argument("--scan_build", action='store_true')

    parser.add_argument("--sdk_ref", required=False, type=Path, default="origin/master")

    parser.add_argument("--input_file", required=False, type=Path, default=Path("input_files/test_input.json"))
    parser.add_argument("--output_file", required=False, type=Path, default=Path("output_files/output.json"))
    parser.add_argument("--logs_file", required=False, type=Path,
            default=Path("output_files/error_logs.txt"))
    parser.add_argument("--workdir", required=False, type=str, default="workdir")

    parser.add_argument("--use_sha1_from_live", required=False, action='store_true')
    parser.add_argument("--provider", required=False, type=str)
    parser.add_argument("--device", required=False, type=str)
    parser.add_argument("--version", required=False, type=str)

    args = parser.parse_args()

    abs_workdir = Path.cwd()/args.workdir

    if not abs_workdir.exists():
        abs_workdir.mkdir()

    nanos_enable = False
    nanosp_enable = False
    nanox_enable = False
    stax_enable = False

    if args.all or args.nanos:
        print("Nanos enabled")
        nanos_enable = True
    if args.all or args.nanosp:
        print("Nanosp enabled")
        nanosp_enable = True
    if args.all or args.nanox:
        print("Nanox enabled")
        nanox_enable = True
    if args.all or args.stax:
        print("Stax enabled")
        stax_enable = True

    devices = Devices(nanos_enable, nanosp_enable, nanox_enable, stax_enable)

    if Path(args.input_file).exists():
        with open(args.input_file) as json_file:
            input_json = json.load(json_file)
    else:
        print("Error: input file does not exist")
        exit()

    if args.use_sha1_from_live:
        if not args.provider:
            print("Error: you must specify provider")
            exit()
        if not args.device:
            print("Error: you must specify device")
            exit()
        if not args.version:
            print("Error: you must specify version")
            exit()

        input_json = override_sha1(input_json, args.provider, args.device, args.version)


    git_setup(SDK_NAME, args.sdk_ref, SDK_URL, abs_workdir)

    output = {}
    test_output = []
    build_output = []
    logs = ""

    for app_json in input_json:
        repo_name = app_json.get("name")
        if not args.skip_setup:
            repo_ref = app_json.get("ref")
            repo_url = app_json.get("url")
            print(f"Setup {repo_name}")
            git_setup(repo_name, repo_ref, repo_url, abs_workdir)

        if args.build:
            print(f"Build {repo_name}")
            build_app, log = build_all_devices(devices, abs_workdir/Path(SDK_NAME), app_json, abs_workdir)
            build_output.append(build_app)
            logs += log

        if args.test:
            print(f"Test {repo_name}")
            test_app, log = test_all_devices(devices, abs_workdir/Path(SDK_NAME), app_json, abs_workdir)
            build_output.append(test_app)
            logs += log

        if args.scan_build:
            print(f"Scan build {repo_name}")
            scan_app, log = scan_all_devices(devices, abs_workdir/Path(SDK_NAME), app_json, abs_workdir)
            build_output.append(scan_app)
            logs += log

    output = merge_json(build_output, test_output, "name")

    with open(args.output_file, 'w') as json_file:
        json.dump(output, json_file, indent=1)

    with open(args.logs_file, 'w') as file:
        file.write(logs)
