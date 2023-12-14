TARGET_NANOS = "nanos"
TARGET_NANOSP = "nanos2"
TARGET_NANOX = "nanox"
TARGET_STAX = "stax"

NANOS_API_LEVEL = 1
NANOSP_API_LEVEL = 1
NANOX_API_LEVEL = 5
STAX_API_LEVEL = 14


class Device:
    def __init__(self, target_name: str, model_name: str, sdk_name: str, api_level: int, enabled: bool):
        self.selected = enabled
        self.target_name = target_name
        self.model_name = model_name
        self.sdk_name = sdk_name
        self.api_level = api_level


class Devices:
    def __init__(self, nanos_enable: bool, nanosp_enable: bool, nanox_enable: bool, stax_enable: bool):
        self.nanos = Device("nanos", "nanos", "$NANOS_SDK", NANOS_API_LEVEL, nanos_enable)
        self.nanosp = Device("nanos2", "nanosp", "$NANOSP_SDK", NANOSP_API_LEVEL, nanosp_enable)
        self.nanox = Device("nanox", "nanox", "$NANOX_SDK", NANOX_API_LEVEL, nanox_enable)
        self.stax = Device("stax", "stax", "$STAX_SDK", STAX_API_LEVEL, stax_enable)
