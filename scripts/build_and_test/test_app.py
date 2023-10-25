from pathlib import Path
from device import Devices, Device
from build_app import build_variant
from utils import run_cmd

def test(model: str, app_test_path: Path, app_build_path: Path, test_params: str):
    output = {}
    error, log = run_cmd(f"pytest {app_test_path}/ --tb=short -v --device {model} {test_params}", cwd=app_build_path, no_throw=True)

    if (error):
        output = "Fail"
        print("\t=> KO")
    else:
        output = "Success"
    return output, log


def install_dependencies(app_test_path: Path):
    error, log = run_cmd("pip install -r requirements.txt", cwd=app_test_path, no_throw=True)
    return error, log

def test_device(device: Device, variant_param: str, app_build_path: Path, app_test_path: Path,
        sdk_path: Path, extra_flags: str, blacklist: str, test_params: str):
    test_output = {}
    log = ""

    if not device.selected:
        return None, log

    if device.model_name in blacklist:
        return "Skipped", log

    error, log = install_dependencies(app_test_path)
    if error:
        print("Error installing dependencies")
        return "Fail", log

    error, log = build_variant(device.target_name, sdk_path, "", "", app_build_path, extra_flags)
    if error:
        return "Fail", log

    test_output, log = test(device.model_name, app_test_path, app_build_path, test_params)

    print(test_output)
    return test_output, log


def test_all_devices(devices: Devices, sdk_path: Path, app_json: dict, workdir: Path):
    repo_name = app_json.get("name")
    variant_param = app_json.get("variant_param")
    app_build_path = workdir / Path(app_json.get("name") + "/" + app_json.get("build_path", "."))
    app_test_path = workdir / Path(app_json.get("name") + "/" + app_json.get("test_dir", "."))
    extra_flags = app_json.get("extra_flags", "")
    blacklist = app_json.get("build_blacklist", "[]")

    output = {
        "name": repo_name,
    }
    output["test"] = {}

    blacklist = app_json.get(f"test_blacklist", [])

    test_params = app_json.get("test_param_nanos", "")
    nanos_output, nanos_log = test_device(devices.nanos, variant_param, app_build_path, app_test_path,
            sdk_path, extra_flags, blacklist, test_params)

    test_params = app_json.get("test_param_nanosp", "")
    nanosp_output, nanosp_log = test_device(devices.nanosp, variant_param, app_build_path, app_test_path,
            sdk_path, extra_flags, blacklist, test_params)


    test_params = app_json.get("test_param_nanox", "")
    nanox_output, nanox_log = test_device(devices.nanox, variant_param, app_build_path, app_test_path,
            sdk_path, extra_flags, blacklist, test_params)

    test_params = app_json.get("test_param_stax", "")
    stax_output, stax_log = test_device(devices.stax, variant_param, app_build_path, app_test_path,
                sdk_path, extra_flags, blacklist, test_params)

    if nanos_output:
        output["test"]["nanos"] = nanos_output
    if nanosp_output:
        output["test"]["nanosp"] = nanosp_output
    if nanox_output:
        output["test"]["nanox"] = nanox_output
    if stax_output:
        output["test"]["stax"] = stax_output
    print(output)

    log = nanos_log + nanosp_log + nanox_log + stax_log

    return output, log
