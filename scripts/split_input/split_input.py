import json
from pathlib import Path
from argparse import ArgumentParser


if __name__ == "__main__":
    parser = ArgumentParser()
    input_json = {}

    parser.add_argument("--input_file", required=False, type=Path,
                        default=Path("input_files/input.json"))
    parser.add_argument("--split_count", required=False, type=Path, default=10)

    args = parser.parse_args()

    if Path(args.input_file).exists():
        with open(args.input_file) as json_file:
            input_json = json.load(json_file)
    else:
        print("Error: input file does not exist")
        exit()

    num_files = args.split_count

    items_per_file = len(input_json) // num_files

    for file_num in range(num_files):
        start_idx = file_num * items_per_file
        end_idx = (file_num + 1) * items_per_file if file_num < num_files - 1 else len(input_json)

        file_name = f"input_{file_num + 1}.json"
        with open(file_name, 'w') as file:
            json.dump(input_json[start_idx:end_idx], file, indent=1)
    # Split data into ten JSON files

    print(f"Data split into {args.split_count} JSON files.")
