import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

sys.path.insert(1, str(Path(__file__).resolve().parent))


def parse_args() -> Namespace:
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(help="Specific operation", dest="operation")

    # split_input
    subparser = subparsers.add_parser('split_input')
    subparser.add_argument("--split_count", required=False, type=int, default=10)
    subparser.add_argument("--input_file", required=False, type=Path, default=Path("input_files/input.json"))

    # build_and_test
    subparser = subparsers.add_parser('build_and_test')
    subparser.add_argument("--skip_setup", action='store_true')

    subparser.add_argument("--all", action='store_true')
    subparser.add_argument("--nanos", action='store_true')
    subparser.add_argument("--nanosp", action='store_true')
    subparser.add_argument("--nanox", action='store_true')
    subparser.add_argument("--stax", action='store_true')

    subparser.add_argument("--test", action='store_true')
    subparser.add_argument("--build", action='store_true')
    subparser.add_argument("--scan_build", action='store_true')

    subparser.add_argument("--sdk_ref", required=False, type=Path, default="origin/master")

    subparser.add_argument("--input_file", required=False, type=Path, default=Path("input_files/test_input.json"))
    subparser.add_argument("--output_file", required=False, type=Path, default=Path("output_files/output.json"))
    subparser.add_argument("--logs_file", required=False, type=Path,
                           default=Path("output_files/error_logs.txt"))
    subparser.add_argument("--workdir", required=False, type=str, default="workdir")

    subparser.add_argument("--use_sha1_from_live", required=False, action='store_true')
    subparser.add_argument("--provider", required=False, type=str)
    subparser.add_argument("--device", required=False, type=str)
    subparser.add_argument("--version", required=False, type=str)

    # output_scripts
    # # convert
    subparser = subparsers.add_parser('convert_output')
    subparser.add_argument("--input_file", required=True, type=Path)
    subparser.add_argument("--output_file", required=False, type=Path)
    subparser.add_argument("--key", required=False, type=str, default="build")
    # # merge
    subparser = subparsers.add_parser('merge_output', description="Merge JSON files based on a specified key")
    subparser.add_argument("--input_pattern", help="Pattern for input JSON files (e.g., input*.json)")
    subparser.add_argument("--output_file", help="Output merged JSON file")
    subparser.add_argument("--key", help="Key to use for merging")
    # # status
    subparser = subparsers.add_parser('status_output')
    subparser.add_argument("--input_file", required=True, type=Path)
    subparser.add_argument("--key", required=True)
    # # slack
    subparser = subparsers.add_parser('slack_output')
    subparser.add_argument("--input_file", required=True, type=Path)
    subparser.add_argument("--output_file", required=False, type=Path)
    subparser.add_argument("--key", required=False, type=str, default="build")
    subparser.add_argument("--devices", required=False, type=str)
    subparser.add_argument("--url", required=False, type=str)

    # create_app_list
    subparser = subparsers.add_parser('create_app_list')
    subparser.add_argument("--access_token", required=True, type=str)
    subparser.add_argument("--workdir", required=False, type=str, default="workdir")
    subparser.add_argument("--extra_info_file", required=False, type=Path, default=Path("input_files/extra_info.json"))
    subparser.add_argument("--repo_file", required=False, type=Path)
    subparser.add_argument("--skip_setup", required=False, action='store_true')

    subparser.add_argument("--full_output_file", required=False, type=Path, default=Path("output_files/full_out.json"))
    subparser.add_argument("--repo_output_file", required=False, type=Path, default=Path("output_files/repo.json"))
    subparser.add_argument("--variant_output_file", required=False, type=Path,
                           default=Path("output_files/variant.json"))

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.operation == 'split_input':
        import split_input
        split_input.main(args)
    elif args.operation == 'build_and_test':
        import build_and_test
        build_and_test.main(args)
    elif args.operation == 'convert_output':
        import output_scripts.convert
        output_scripts.convert.main(args)
    elif args.operation == 'merge_output':
        import output_scripts.merge
        output_scripts.merge.main(args)
    elif args.operation == 'status_output':
        import output_scripts.status
        output_scripts.status.main(args)
    elif args.operation == 'slack_output':
        import output_scripts.slack
        output_scripts.slack.main(args)
    elif args.operation == 'create_app_list':
        import create_app_list
        create_app_list.main(args)
