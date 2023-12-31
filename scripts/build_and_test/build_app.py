import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union

from build_and_test.device import Devices, Device
from utils import run_cmd


def build_variant(target: str,
                  sdk_path: Path,
                  variant_param: Optional[str],
                  variant_value: str,
                  app_build_path: Path,
                  extra_flags: str = "") -> Tuple[int, str]:

    if not os.path.exists(app_build_path):
        print("\t=> KO")
        return True, f"Error: {app_build_path} does not exists\n"

    run_cmd(f"TARGET={target} BOLOS_SDK={sdk_path} make clean", cwd=app_build_path, no_throw=True)
    if variant_param:
        error, log = run_cmd(f"TARGET={target} BOLOS_SDK={sdk_path} make {variant_param}={variant_value} {extra_flags}",
                             cwd=app_build_path, no_throw=True)
    else:
        error, log = run_cmd(f"TARGET={target} BOLOS_SDK={sdk_path} make -j {extra_flags}",
                             cwd=app_build_path, no_throw=True)

    if error:
        print("\t=> KO")

    return error, log


def build_all_variants(target: str,
                       sdk_path: Path,
                       variant_param: Optional[str],
                       variant_list: list,
                       app_build_path: Path) -> Tuple[Dict[str, str], str]:
    output = {}
    error_log = ""
    for variant in variant_list:
        error, log = build_variant(target, sdk_path, variant_param, variant, app_build_path)

        if (error):
            output[variant] = "Fail"
            error_log += log
        else:
            output[variant] = "Success"

    return output, error_log


def build_device(device: Device,
                 variant_param: Optional[str],
                 app_build_path: Path,
                 sdk_path: Path,
                 app_json: dict) -> Tuple[Union[str, Dict[str, str]], str]:
    blacklist = app_json.get("build_blacklist", [])
    error_log = ""

    if not device.selected:
        return "Unselected", error_log

    if device.model_name in blacklist:
        return "Blacklisted", error_log

    variants = app_json.get(f"variants_{device.model_name}", [])
    variant_output: Dict[str, str] = {}
    if len(variants) > 0:
        variant_output, error_log = build_all_variants(device.target_name,
                                                       sdk_path,
                                                       variant_param,
                                                       variants,
                                                       app_build_path)

    return variant_output, error_log


def build_all_devices(devices: Devices, sdk_path: Path, app_json: dict, workdir: Path):
    repo_name = app_json["name"]
    variant_param = app_json.get("variant_param")
    app_build_path = workdir / Path(repo_name + "/" + app_json.get("build_path", "."))

    output = {
        "name": repo_name,
    }
    output["build"] = {}

    nanos_output, nanos_log = build_device(devices.nanos, variant_param, app_build_path, sdk_path, app_json)

    nanosp_output, nanosp_log = build_device(devices.nanosp, variant_param, app_build_path, sdk_path, app_json)

    nanox_output, nanox_log = build_device(devices.nanox, variant_param, app_build_path, sdk_path, app_json)

    stax_output, stax_log = build_device(devices.stax, variant_param, app_build_path, sdk_path, app_json)

    if nanos_output and devices.nanos.selected:
        output["build"]["nanos"] = nanos_output
    if nanosp_output and devices.nanosp.selected:
        output["build"]["nanosp"] = nanosp_output
    if nanox_output and devices.nanox.selected:
        output["build"]["nanox"] = nanox_output
    if stax_output and devices.stax.selected:
        output["build"]["stax"] = stax_output

    log = nanos_log + nanosp_log + nanox_log + stax_log
    return output, log
