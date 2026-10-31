from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Firemod — reversible Amazon Fire TV toolkit")
    parser.add_argument("--demo", action="store_true", help="Preview the interface without opening ADB")
    parser.add_argument("--screenshot", type=Path, help="Save a demo screenshot, then exit")
    parser.add_argument("--diagnose", metavar="SERIAL", help="Print a read-only device report as JSON")
    args = parser.parse_args()
    if args.diagnose:
        from .adb import Adb, find_adb
        from .engine import Engine
        path = find_adb()
        if not path:
            parser.error("ADB was not found. Set FIREMOD_ADB or install Android Platform-Tools.")
        print(json.dumps(asdict(Engine(Adb(path, args.diagnose)).inspect()), indent=2))
        return
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QApplication

    from .gui import Window
    application = QApplication(sys.argv[:1])
    application.setApplicationName("Firemod")
    application.setOrganizationName("Firemod")
    window = Window(demo=args.demo or bool(args.screenshot))
    window.show()
    if args.screenshot:
        def capture():
            args.screenshot.parent.mkdir(parents=True, exist_ok=True)
            if not window.grab().save(str(args.screenshot)):
                raise RuntimeError("Screenshot could not be saved.")
            application.quit()
        QTimer.singleShot(800, capture)
    sys.exit(application.exec())


if __name__ == "__main__":
    main()
