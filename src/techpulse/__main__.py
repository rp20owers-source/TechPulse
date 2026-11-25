"""Desktop entry point and noninteractive health checks."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(description="TechPulse local research terminal")
    parser.add_argument(
        "--smoke-test", action="store_true", help="Open the native UI briefly, validate all pages, then exit"
    )
    parser.add_argument("--data-dir", help="Override local state directory")
    args = parser.parse_args()
    if args.data_dir:
        import os

        os.environ["TECHPULSE_DATA_DIR"] = args.data_dir
    if args.smoke_test:
        from PySide6.QtWidgets import QApplication

        from .app import PAGES, MainWindow
        from .paths import data_directory
        from .startup import checked_store

        app = QApplication([])
        window = MainWindow(checked_store(data_directory()))
        window.show()
        app.processEvents()
        for mode in (0, 1):
            window.workspace.setCurrentIndex(mode)
            for i, page in enumerate(PAGES):
                window.nav.setCurrentRow(i)
                app.processEvents()
                if window.page != page:
                    raise RuntimeError(f"Navigation failed: {page}")
        if window.page_errors:
            raise RuntimeError(str(window.page_errors))
        window.close()
        print("TechPulse native smoke check: all 16 pages in both workspaces opened")
        return 0
    from .app import launch

    return launch()


if __name__ == "__main__":
    sys.exit(main())
