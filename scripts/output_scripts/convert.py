import json
from argparse import ArgumentParser
from pathlib import Path

def json_to_markdown(json_list, key):
    # Set up the markdown table headers
    markdown_table = "| App Name | nanos | nanosp | nanox | stax |\n"
    markdown_table += "|----------|-------|--------|-------|------|\n"

    # Iterate over each dictionary in the list
    for json_data in json_list:
        # Extract app_name and app_data from the json_data
        app_name = json_data["name"]
        app_data = json_data.get(key, {})

        # Start constructing the row with app_name
        row = "| {} |".format(app_name)

        # Iterate over each device and append the status
        for d in ["nanos", "nanosp", "nanox", "stax"]:
            build_data = app_data.get(d, {})
            if isinstance(build_data, dict):  # nested structure
                status_icon = ":red_circle:" if "Fail" in build_data.values() else ":heavy_check_mark:" if "Success" in build_data.values() else ":fast_forward:" if "Skipped" in build_data.values() else ""
            else: 
                status_icon = ":heavy_check_mark:" if build_data == "Success" else ":red_circle:" if build_data == "Fail" else ":fast_forward:" if build_data == "Skipped" else ""
            row += " {} |".format(status_icon)

        markdown_table += row + "\n"
    return markdown_table


def count_status(json_list, key):
    counts = {
        "Success": 0,
        "Fail": 0,
        "Total": 0
    }

    # Iterate over each dictionary in the list
    for json_data in json_list:
        app_data = json_data.get(key, {})

        for build_data in app_data.values():
            if isinstance(build_data, dict):  # nested structure
                for status in build_data.values():
                    counts["Total"] += 1
                    if status == "Success":
                        counts["Success"] += 1
                    elif status == "Fail":
                        counts["Fail"] += 1
            else:  # direct structure
                counts["Total"] += 1
                if build_data == "Success":
                    counts["Success"] += 1
                elif build_data == "Fail":
                    counts["Fail"] += 1

    return f"""
Success: {counts['Success']}
Failures: {counts['Fail']}
Total: {counts['Total']}
"""


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--input_file", required=True, type=Path)
    parser.add_argument("--output_file", required=False, type=Path)
    parser.add_argument("--key", required=False, type=str, default="build")

    args = parser.parse_args()

    with open(args.input_file) as json_file:
        json_list = json.load(json_file)

    markdown_table = json_to_markdown(json_list, args.key)
    markdown_table += count_status(json_list, args.key)

    print(markdown_table)

    if args.output_file:
        with open(args.output_file, 'w') as file:
            file.write(markdown_table)
