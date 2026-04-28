#!/usr/bin/env python3
"""Bootstrap: clone kivy-thor and run its build script.

Creates at the current working directory:
    dependencies/  – kivy-thor clone (it handles the rest)
    wheelhouse/    – created by build_kt.py for output wheels

Usage:
    python scripts/build_kt.py all macos
    python scripts/build_kt.py kivythor macos
    python scripts/build_kt.py thorgpu ios

Set KIVY_THOR_LOCAL to use a specific local kivy-thor checkout instead of
the sibling directory or GitHub:

    KIVY_THOR_LOCAL=/path/to/kivy-thor scripts/build_kt.py all macos

Android SDK/NDK are auto-discovered from the project's .psproject directory.
Override with ANDROID_HOME / ANDROID_NDK_HOME if needed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

KIVY_THOR_URL = "https://github.com/Py-Swift/kivy-thor.git"


def _sync_local(local: Path, dest: Path) -> None:
    """Copy local kivy-thor checkout into dependencies/, skipping .git/venv."""
    if dest.exists():
        shutil.rmtree(dest)
    print(f"==> Syncing local kivy-thor: {local} \u2192 {dest}")
    shutil.copytree(
        local, dest,
        ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "*.egg-info", "build"),
    )


def _setup_android_env(root: Path) -> None:
    """Read NDK version from pyproject.toml and set ANDROID_HOME / ANDROID_NDK_HOME.

    Path is always: <root>/<root.name>/.psproject/android-sdk/ndk/<version>
    Hard-exits if the directory isn't present.
    """
    import tomllib

    pyproject = root / root.name / "pyproject.toml"
    with open(pyproject, "rb") as fh:
        cfg = tomllib.load(fh)

    ndk_version = cfg["tool"]["psproject"]["android"]["ndk"]
    sdk_dir = root / root.name / ".psproject" / "android-sdk"
    ndk_dir = sdk_dir / "ndk" / ndk_version

    if not ndk_dir.is_dir():
        print(f"ERROR: Android NDK {ndk_version} not found at {ndk_dir}", file=sys.stderr)
        sys.exit(1)

    os.environ["ANDROID_HOME"] = str(sdk_dir)
    os.environ["ANDROID_NDK_HOME"] = str(ndk_dir)
    print(f"==> ANDROID_HOME={sdk_dir}")
    print(f"==> ANDROID_NDK_HOME={ndk_dir}")


def main() -> None:
    root = Path.cwd()
    deps = root / "dependencies"
    deps.mkdir(exist_ok=True)

    kt_dir = deps / "kivy-thor"
    local = os.environ.get("KIVY_THOR_LOCAL", None)

    # Auto-detect sibling kivy-thor in the workspace (e.g. ../kivy-thor)
    sibling_kt = root.parent / "kivy-thor"
    if local:
        _sync_local(Path(local).expanduser().resolve(), kt_dir)
    elif sibling_kt.is_dir():
        _sync_local(sibling_kt, kt_dir)
    elif not kt_dir.exists():
        print(f"==> Cloning kivy-thor into {kt_dir}")
        subprocess.run(["git", "clone", KIVY_THOR_URL, str(kt_dir)], check=True)
    else:
        print(f"==> kivy-thor exists, pulling latest...")
        subprocess.run(["git", "pull"], check=True, cwd=kt_dir)

    # ── Android SDK / NDK ────────────────────────────────────────────────────
    _setup_android_env(root)

    # build_kt.py discovers sibling repos from CWD and clones them if missing
    os.chdir(deps)

    # Wheelhouse lives at project root, not inside dependencies/
    os.environ.setdefault("WHEELHOUSE", str(root / "wheelhouse"))

    build_script = kt_dir / "scripts" / "build_kt.py"
    cmd = [sys.executable, str(build_script), *sys.argv[1:]]
    print(f"==> {' '.join(cmd)}")
    os.execvp(sys.executable, cmd)


if __name__ == "__main__":
    main()
