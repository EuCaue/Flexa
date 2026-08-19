# debug.py
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys

_ENV_DEBUG = os.environ.get("FLEXA_DEBUG", "").strip().lower()
IS_DEBUG = _ENV_DEBUG in ("1", "true", "yes", "on", "debug")


def is_debug() -> bool:
    """Return True if running in development / debug mode."""
    return IS_DEBUG


def debug(*args, **kwargs) -> None:
    """Print a debug message to stderr only when in development mode (FLEXA_DEBUG=1)."""
    if IS_DEBUG:
        print("[DEBUG:flexa]", *args, file=sys.stderr, **kwargs)
