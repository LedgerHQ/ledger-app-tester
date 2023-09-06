from pathlib import Path
from device import Devices, Device
from utils import run_cmd

def build_variant(target: str, sdk_path: str, variant_param: str, variant_value: str, app_build_path:
        Path, extra_flags: str=""):
    error = run_cmd(f"TARGET={target} BOLOS_SDK={sdk_path} make clean", cwd=app_build_path, no_throw=True)
    if variant_param:
        error = run_cmd(f"TARGET={target} BOLOS_SDK={sdk_path} make {variant_param}={variant_value} {extra_flags}", cwd=app_build_path, no_throw=True)
    else:
        error = run_cmd(f"TARGET={target} BOLOS_SDK={sdk_path} make -j {extra_flags}", cwd=app_build_path, no_throw=True)

    if error:
        print("\t=> KO")

    return error


def build_all_variants(target: str, sdk_path: str, variant_param: str, variant_list: list, app_build_path: Path):
    output = {}
    for variant in variant_list:
        error = build_variant(target, sdk_path, variant_param, variant, app_build_path)

        if (error):
            output[variant] = "Fail"
        else:
            output[variant] = "Success"

    return output


def build_device(device: Device, variant_param: str, app_build_path: Path, sdk_path: Path, app_json: dict):
    blacklist = app_json.get("build_blacklist", "[]")

    if device.model_name in blacklist:
        return "Skipped"

    variants = app_json.get(f"variants_{device.model_name}", [])
    variant_output = {}
    if device.selected and len(variants) > 0:
        variant_output = build_all_variants(device.target_name, sdk_path, variant_param, variants, app_build_path)

    return variant_output


def build_all_devices(devices: Devices, sdk_path: Path, app_json: dict, workdir: Path):
    repo_name = app_json.get("name")
    variant_param = app_json.get("variant_param")
    app_build_path = workdir / Path(app_json.get("name") + "/" + app_json.get("build_path", "."))

    output = {
        "name": repo_name,
    }
    output["build"] = {}

    nanos_output = build_device(devices.nanos, variant_param, app_build_path, sdk_path, app_json)

    nanosp_output = build_device(devices.nanosp, variant_param, app_build_path, sdk_path, app_json)

    nanox_output = build_device(devices.nanox, variant_param, app_build_path, sdk_path, app_json)

    stax_output = build_device(devices.stax, variant_param, app_build_path, sdk_path, app_json)

    if nanos_output:
        output["build"]["nanos"] = nanos_output
    if nanosp_output:
        output["build"]["nanosp"] = nanosp_output
    if nanox_output:
        output["build"]["nanox"] = nanox_output
    if stax_output:
        output["build"]["stax"] = stax_output

    return output
