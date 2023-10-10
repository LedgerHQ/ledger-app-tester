import json
from argparse import ArgumentParser
from pathlib import Path

def count_status(json_list, key):
    success_count = 0
    fail_count = 0
    total_count = 0
    fail_list = {}

    variant = None
    # Iterate over each dictionary in the list
    for json_data in json_list:
        app_data = json_data.get(key, {})
        app_name = json_data.get("name", {})
        fail_list[app_name] = {}

        failed_devices = ""
        for key_data, build_data in app_data.items():
            if isinstance(build_data, dict):  # nested structure
                variant, status = build_data.popitem()
            else:
                status = build_data
                

            if status == "Success":
                total_count += 1
                success_count += 1
            elif status == "Fail":
                total_count += 1
                fail_count += 1
                if variant:
                    fail_list[app_name][key_data] = variant
                else:
                    failed_devices += f"{key_data}, "

        if key == "test" and failed_devices:
            fail_list[app_name] = failed_devices

    return success_count, fail_count, total_count, fail_list


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--input_file", required=True, type=Path)
    parser.add_argument("--output_file", required=False, type=Path)
    parser.add_argument("--key", required=False, type=str, default="build")
    parser.add_argument("--devices", required=False, type=str)

    args = parser.parse_args()


    with open(args.input_file) as json_file:
        json_list = json.load(json_file)

    success_count, fail_count, total_count, fail_list = count_status(json_list, args.key)

    title = f"{args.key}"

    if args.devices:
        title += f" on {args.devices}"


    status_detail = ""
    if fail_count == 0:
        status = f":large_green_circle: Success for {total_count} apps"
    else:
        status = f":red-cross: Fail for {fail_count} / {total_count} apps"
        fail_status = "Failed for:\n"
        for app_name, details in fail_list.items():
            if details:
                fail_status += f"\t•  {app_name}\n"
                if isinstance(details, dict):
                    for device, variant in details.items():
                        fail_status += f"\t\t  - {device} : {variant} \n"
                else:
                    fail_status += f"\t\t  -  {details}\n"
        status_detail = f"{fail_status}"

    slack_json = {}
    slack_json["title"] = title
    slack_json["status"] = status
    if status_detail:
        slack_json["status_detail"] = status_detail

    if args.output_file:
        with open(args.output_file, 'w') as f:
            json.dump(slack_json, f, indent=1)

