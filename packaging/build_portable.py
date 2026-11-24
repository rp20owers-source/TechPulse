"""Rebuildable local Windows preview; public binary publication has separate gates."""

import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != "win32":
        raise SystemExit("Build the Windows artifact on Windows")
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "TechPulse",
        "--paths",
        str(ROOT / "src"),
        "--exclude-module",
        "PySide6.QtWebEngineCore",
        "--exclude-module",
        "PySide6.QtWebEngineWidgets",
        "--exclude-module",
        "PySide6.QtPdf",
        "--exclude-module",
        "PySide6.QtQml",
        "--exclude-module",
        "PySide6.QtQuick",
        "--exclude-module",
        "PySide6.QtDesigner",
        "--exclude-module",
        "tkinter",
        "--collect-data",
        "reportlab",
        str(ROOT / "packaging" / "entrypoint.py"),
    ]
    # A developer PATH may include unrelated Qt/ICU DLLs (for example Poppler).
    # Let hooks collect package-native libraries and resolve OS DLLs from Windows.
    build_env = os.environ.copy()
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    build_env["PATH"] = os.pathsep.join(
        [str(Path(sys.executable).parent), str(system_root / "System32"), str(system_root)]
    )
    subprocess.run(command, cwd=ROOT, env=build_env, check=True)
    target = ROOT / "dist" / "TechPulse"
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "README.md"):
        shutil.copy2(ROOT / name, target / name)
    shutil.copytree(ROOT / "LICENSES", target / "LICENSES", dirs_exist_ok=True)
    inventory = []
    for distribution in importlib.metadata.distributions():
        name, version = distribution.metadata["Name"], distribution.version
        files = [
            f for f in distribution.files or [] if "license" in str(f).lower() or "copying" in str(f).lower()
        ]
        destination = target / "distribution-notices" / (name + "-" + version)
        copied = []
        for file in files:
            source = Path(distribution.locate_file(file))
            if source.is_file() and source.suffix.lower() not in {".py", ".pyc", ".pyd", ".dll"}:
                # Stable per-distribution relative path prevents collisions.
                relative = Path(str(file).replace("..", "__"))
                output = destination / relative
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output)
                copied.append(str(relative))
        inventory.append(
            {
                "distribution": name,
                "version": version,
                "license_expression": distribution.metadata.get("License-Expression"),
                "license": distribution.metadata.get("License"),
                "copied_notices": copied,
                "note": "Installed environment inventory, not proof every component is bundled",
            }
        )
    (target / "installed-distribution-inventory.json").write_text(
        json.dumps(inventory, indent=2), encoding="utf8"
    )
    (target / "PREVIEW-RELEASE-GATES.txt").write_text(
        "LOCAL DEVELOPMENT PREVIEW ONLY. No clean-machine, signing or corresponding-library-source acceptance is claimed. Do not publish this directory as an approved installer. See source THIRD_PARTY_NOTICES.md and docs/research/RELEASE_READINESS.md.\n",
        encoding="utf8",
    )
    print(target)


if __name__ == "__main__":
    main()
