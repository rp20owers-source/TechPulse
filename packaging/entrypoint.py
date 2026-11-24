"""Frozen entry point with a private startup log and unattended smoke failure exit."""

import os
import sys
import traceback
from pathlib import Path

from techpulse.__main__ import main

if __name__ == "__main__":
    try:
        result = main()
    except Exception:
        directory = Path(
            os.environ.get(
                "TECHPULSE_DATA_DIR", Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TechPulse"
            )
        )
        directory.mkdir(parents=True, exist_ok=True)
        log = directory / "startup-error.log"
        log.write_text(traceback.format_exc(), encoding="utf8")
        if "--smoke-test" not in sys.argv and sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                None,
                "TechPulse could not start. A private diagnostic was saved to:\n" + str(log),
                "TechPulse startup",
                0x10,
            )
        result = 1
    raise SystemExit(result)
