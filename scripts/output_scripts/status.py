import json
from argparse import ArgumentParser
from pathlib import Path

def check_status(json_data, key):
    for app_data in json_data:
        name = app_data["name"]
        target_data = app_data.get(key)  # Use .get() to safely access the key
        if target_data is not None and isinstance(target_data, dict):
            for _, status in target_data.items():
                if status == "Fail":
                    raise ValueError(f"Failed for {name}")

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--input_file", required=True, type=Path)
    parser.add_argument("--key", required=True)

    args = parser.parse_args()

    with open(args.input_file) as json_file:
        json_data = json.load(json_file)

    check_status(json_data, args.key)
