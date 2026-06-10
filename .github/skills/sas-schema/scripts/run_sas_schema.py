#!/usr/bin/env python3
"""Portable entrypoint for the sas-schema skill bundle."""

from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from portable_sas_schema.cli import main


if __name__ == "__main__":
    main()