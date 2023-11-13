from argparse import ArgumentParser
from pathlib import Path
import json

from parse_github import parse_github

from gen_variant import gen_variant
from utils import git_setup, merge_json

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--access_token", required=True, type=str)
    parser.add_argument("--workdir", required=False, type=str, default="workdir")
    parser.add_argument("--extra_info_file", required=False, type=Path, default=Path("input_files/extra_info.json"))
    parser.add_argument("--repo_file", required=False, type=Path)
    parser.add_argument("--skip_setup", required=False, action='store_true')

    parser.add_argument("--full_output_file", required=False, type=Path, default=Path("output_files/full_out.json"))
    parser.add_argument("--repo_output_file", required=False, type=Path, default=Path("output_files/repo.json"))
    parser.add_argument("--variant_output_file", required=False, type=Path, default=Path("output_files/variant.json"))

    args = parser.parse_args()

    abs_workdir = Path.cwd()/args.workdir

    if not abs_workdir.exists():
        abs_workdir.mkdir()

    if args.extra_info_file.exists():
        with open(args.extra_info_file) as json_file:
            extra_info_json = json.load(json_file)
    else:
        print("Error opening extra_info_file")
        exit()

    if args.repo_file and args.repo_file.exists():
        with open(args.repo_file) as json_file:
            repo_json = json.load(json_file)
    else:
        print("Parsing github")
        repo_json = parse_github(args.access_token)

    merged_json = merge_json(repo_json, extra_info_json, "name")

    variant_json = []
    for repo in merged_json:
        repo_name = repo.get("name")
        repo_ref = repo.get("ref")
        repo_url = repo.get("url")
        repo_build_path = abs_workdir/Path(repo_name)/Path(repo.get("build_path", "."))

        if not args.skip_setup:
            print("Cloning repo")
            git_setup(repo_name, repo_ref, repo_url, abs_workdir)

        print("Generating variants")
        app_variant = gen_variant(repo_name, repo_build_path, abs_workdir)
        variant_json.append(app_variant)

    full_output = merge_json(merged_json, variant_json, "name")

    with open(args.variant_output_file, 'w') as json_file:
        json.dump(variant_json, json_file, indent=1)

    with open(args.repo_output_file, 'w') as json_file:
        json.dump(repo_json, json_file, indent=1)

    with open(args.full_output_file, 'w') as json_file:
        json.dump(full_output, json_file, indent=1)
