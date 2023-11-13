import argparse
import glob
import json


def merge_jsons(json1, json2, key):
    # Create a dictionary to store the merged data by name
    merged_data = {}

    # Merge data from the first JSON array
    for item in json1:
        name = item["name"]
        if name not in merged_data:
            merged_data[name] = item[key]
        else:
            merged_data[name].update(item[key])

    # Merge data from the second JSON array
    for item in json2:
        name = item["name"]
        if name not in merged_data:
            merged_data[name] = item[key]
        else:
            merged_data[name].update(item[key])

    # Convert the merged dictionary back to a list of JSON objects
    merged_json = [{"name": name, key: merged_data[name]} for name in merged_data]

    return merged_json


def merge_multiple_jsons(input_files, key):
    result = {}
    for j in input_files:
        with open(j, 'r') as f:
            data = json.load(f)
            result = merge_jsons(result, data, key)
    return result


def main():
    parser = argparse.ArgumentParser(description="Merge JSON files based on a specified key")
    parser.add_argument("--input_pattern", help="Pattern for input JSON files (e.g., input*.json)")
    parser.add_argument("--output_file", help="Output merged JSON file")
    parser.add_argument("--key", help="Key to use for merging")

    args = parser.parse_args()

    input_files = glob.glob(args.input_pattern)
    if not input_files:
        print("No input files found.")
        return

    merged_json = merge_multiple_jsons(input_files, args.key)
    with open(args.output_file, 'w') as f:
        json.dump(merged_json, f, indent=1)


if __name__ == "__main__":
    main()
