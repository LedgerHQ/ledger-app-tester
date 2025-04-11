#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool to list the targeted devices.
"""

import logging
from argparse import ArgumentParser, Namespace
from utils import logging_init, logging_set_level, set_gh_output


# ===============================================================================
#          Parse command line options
# ===============================================================================
def arg_parse() -> Namespace:
    """Parse the commandline options"""

    parser = ArgumentParser("Selects targeted devices")

    parser.add_argument("--nanosp", action='store_true', help="Select NanoSP")
    parser.add_argument("--nanox", action='store_true', help="Select NanoX")
    parser.add_argument("--stax", action='store_true', help="Select Stax")
    parser.add_argument("--flex", action='store_true', help="Select Flex")

    parser.add_argument("-e",
                        "--event",
                        type=str,
                        required=True,
                        help="GitHub event name")

    parser.add_argument("-o",
                        "--output",
                        type=str,
                        required=True,
                        help="Output variable for the devices data.")

    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase verbosity.")

    args = parser.parse_args()

    if args.event in ("schedule", "pull_request"):
        args.nanosp = True
        args.nanox = True
        args.stax = True
        args.flex = True

    return args


# ===============================================================================
#          MAIN
# ===============================================================================
def main() -> None:
    """Main function"""

    logging_init()

    # Arguments parsing
    # -----------------
    args = arg_parse()

    # Arguments checking
    # ------------------
    logging_set_level(args.verbose)

    # Processing
    # ----------
    logging.info("Preparing the targeted devices list")
    devices = ""
    if args.nanosp:
        if len(devices) > 0:
            devices += " "
        devices += "nanosp"
    if args.nanox:
        if len(devices) > 0:
            devices += " "
        devices += "nanox"
    if args.stax:
        if len(devices) > 0:
            devices += " "
        devices += "stax"
    if args.flex:
        if len(devices) > 0:
            devices += " "
        devices += "flex"

    logging.info("Selected devices: %s", devices)

    set_gh_output(args.output, devices)


if __name__ == "__main__":
    main()
