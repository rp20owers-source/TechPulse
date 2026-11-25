"""Permanent per-user desktop entry point, independent of the development folder."""

import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "app" / "src"))

if __name__ == "__main__":
    try:
        from techpulse.__main__ import main

        result = main()
    except Exception:
        directory = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "TechPulse"
        directory.mkdir(parents=True, exist_ok=True)
        log = directory / "startup-error.log"
        log.write_text(traceback.format_exc(), encoding="utf8")
        if "--smoke-test" not in sys.argv and sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(
                None, "TechPulse could not start. Details:\n" + str(log), "TechPulse", 0x10
            )
        result = 1
    raise SystemExit(result)
