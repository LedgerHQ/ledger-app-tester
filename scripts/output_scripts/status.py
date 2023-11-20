import json
from argparse import Namespace


def check_status(json_data, key):
    # Iterate over each dictionary in the list
    for json_data in json_data:
        app_data = json_data.get(key, {})
        app_name = json_data.get("name", {})

        for d in ["nanos", "nanosp", "nanox", "stax"]:
            data = app_data.get(d, {})
            if isinstance(data, dict):  # nested structure
                if "Fail" in data.values():
                    raise ValueError(f"Failed for {app_name}")
            else:
                if data == "Fail":
                    raise ValueError(f"Failed for {app_name}")


def main(args: Namespace) -> None:
    with open(args.input_file) as json_file:
        json_data = json.load(json_file)
    check_status(json_data, args.key)
