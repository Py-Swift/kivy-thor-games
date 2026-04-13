#!/usr/bin/env python3
"""Bootstrap: clone kivy-thor and run its build script.

Creates at the current working directory:
    dependencies/  – kivy-thor clone (it handles the rest)
    wheelhouse/    – created by build_kt.py for output wheels

Usage:
    python scripts/build_kt.py all macos
    python scripts/build_kt.py kivythor macos
    python scripts/build_kt.py thorgpu ios
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

KIVY_THOR_URL = "https://github.com/Py-Swift/kivy-thor.git"


def main() -> None:
    root = Path.cwd()
    deps = root / "dependencies"
    deps.mkdir(exist_ok=True)

    kt_dir = deps / "kivy-thor"
    if not kt_dir.exists():
        print(f"==> Cloning kivy-thor into {kt_dir}")
        subprocess.run(["git", "clone", KIVY_THOR_URL, str(kt_dir)], check=True)
    else:
        print(f"==> kivy-thor exists, pulling latest...")
        subprocess.run(["git", "pull"], check=True, cwd=kt_dir)

    # build_kt.py discovers sibling repos from CWD and clones them if missing
    os.chdir(deps)

    build_script = kt_dir / "scripts" / "build_kt.py"
    cmd = [sys.executable, str(build_script), *sys.argv[1:]]
    print(f"==> {' '.join(cmd)}")
    os.execvp(sys.executable, cmd)


if __name__ == "__main__":
    main()
