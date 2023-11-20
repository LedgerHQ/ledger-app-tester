"""
This is a pure duplicate of
https://github.com/LedgerHQ/ledger-app-workflows/blob/master/scripts/makefile_dump.py
This is to allow easily generating the db from the apps code.
"""

from pathlib import Path
from typing import Tuple, List

from create_app_list.utils import run_cmd


def get_app_listvariants(app_build_path: Path,
                         sdk: str = "$NANOS_SDK",
                         allow_failure: bool = False) -> Tuple[str, List[str]]:
    # Using listvariants Makefile target
    listvariants = run_cmd(f"make BOLOS_SDK={sdk} listvariants", cwd=app_build_path, no_throw=allow_failure)
    if "VARIANTS" not in listvariants:
        raise ValueError(f"Invalid variants retrieved: {listvariants}")

    # Drop Makefile logs previous to listvariants output
    listvariants = listvariants.split("VARIANTS ")[1]
    listvariants = listvariants.split("\n")[0]

    variants = listvariants.split(" ")
    variant_param_name = variants.pop(0)
    assert variants, "At least one variant should be defined in the app Makefile"
    return variant_param_name, variants
