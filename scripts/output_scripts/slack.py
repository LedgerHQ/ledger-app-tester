import json
from argparse import Namespace


def count_test_status(json_list):
    success_count = 0
    fail_count = 0
    total_count = 0
    fail_list = {}

    # Iterate over each dictionary in the list
    for json_data in json_list:
        app_data = json_data.get("test", {})
        app_name = json_data.get("name", {})
        fail_list[app_name] = {}

        device_list = []
        for d in ["nanos", "nanosp", "nanox", "stax"]:
            build_data = app_data.get(d, {})

            status = build_data
            if status == "Success":
                total_count += 1
                success_count += 1
            elif status == "Fail":
                total_count += 1
                fail_count += 1
                device_list.append(d)

        if device_list:
            fail_list[app_name] = device_list

    return success_count, fail_count, total_count, fail_list


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

        for d in ["nanos", "nanosp", "nanox", "stax"]:
            build_data = app_data.get(d, {})

            if isinstance(build_data, dict):  # nested structure
                failed_variant_list = []
                for variant, status in build_data.items():
                    if status == "Success":
                        total_count += 1
                        success_count += 1
                    elif status == "Fail":
                        total_count += 1
                        fail_count += 1
                        failed_variant_list.append(variant)

                if failed_variant_list:
                    fail_list[app_name][d] = failed_variant_list
    return success_count, fail_count, total_count, fail_list


def main(args: Namespace) -> None:
    with open(args.input_file) as json_file:
        json_list = json.load(json_file)

    if args.key == "test":
        success_count, fail_count, total_count, fail_list = count_test_status(json_list)
    else:
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
                    device_status = ""
                    for device, variant in details.items():
                        if not device_status:
                            device_status = "\t\t"
                        else:
                            device_status += ", "
                        device_status += device
                    if device_status:
                        fail_status += f"{device_status} \n"

                else:
                    for device in details:
                        fail_status += f"\t\t- {device}\n"
        status_detail = f"{fail_status}"

    slack_json = {}
    slack_json["title"] = title
    slack_json["status"] = status
    if status_detail:
        slack_json["status_detail"] = status_detail

    slack_json["url"] = args.url

    if args.output_file:
        with open(args.output_file, 'w') as f:
            json.dump(slack_json, f, indent=1)
