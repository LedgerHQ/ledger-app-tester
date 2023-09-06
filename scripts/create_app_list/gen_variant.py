#!/usr/bin/env python3

from pathlib import Path
from makefile_dump import get_app_listvariants
from collections import namedtuple

Models = namedtuple('Models', ['sdk_value', 'device_name'])

MODELS = [Models("$NANOS_SDK", "nanos"),
        Models("$NANOX_SDK", "nanox"),
        Models("$NANOSP_SDK", "nanosp"),
        Models("$STAX_SDK", "stax")]


def gen_variant(app_name: str, build_path: str, output_file: Path = "", workdir: Path = "") -> dict:
    print(f"Generating for {app_name}")

    database_params = {
        "name": app_name,
    }

    # Retrieve available variants
    for model in MODELS:
        try:
            variant_param_name, variants = get_app_listvariants(build_path, model.sdk_value, allow_failure=True)
        except:
            print("Skipping generation due to error")
            continue

        database_params["variant_param"] = variant_param_name
        database_params["variants_" + model.device_name] = variants

    return database_params
