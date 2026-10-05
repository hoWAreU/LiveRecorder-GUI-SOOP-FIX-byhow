from __future__ import annotations

import os
import runpy
import shutil
import sys
from pathlib import Path


FROZEN = bool(getattr(sys, "frozen", False))
APP_ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
BUNDLE_ROOT = Path(getattr(sys, "_MEIPASS", APP_ROOT)).resolve() if FROZEN else APP_ROOT
CORE = BUNDLE_ROOT / "recorder-core"
CONFIG_ROOT = APP_ROOT / "config" if FROZEN else CORE / "config"
DOWNLOAD_ROOT = APP_ROOT / "downloads" if FROZEN else CORE / "downloads"
LOG_ROOT = APP_ROOT / "logs" if FROZEN else CORE / "logs"
BACKUP_ROOT = APP_ROOT / "backup_config" if FROZEN else CORE / "backup_config"

if FROZEN:
    os.environ.setdefault("LIVE_RECORDER_DATA_ROOT", str(APP_ROOT))


def ensure_runtime_layout() -> None:
    for directory in (CONFIG_ROOT, DOWNLOAD_ROOT, LOG_ROOT, BACKUP_ROOT):
        directory.mkdir(parents=True, exist_ok=True)
    source_config = CORE / "config"
    for runtime_name, example_name in (
        ("config.ini", "config.example.ini"),
        ("URL_config.ini", "URL_config.example.ini"),
    ):
        runtime = CONFIG_ROOT / runtime_name
        example = source_config / example_name
        if not runtime.exists() and example.exists():
            shutil.copyfile(example, runtime)


def core_command() -> tuple[list[str], Path]:
    if FROZEN:
        return [sys.executable, "--core"], CORE
    core_python = CORE / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    executable = str(core_python) if core_python.exists() else sys.executable
    return [executable, "-X", "utf8", "-u", "main.py"], CORE


def run_core() -> None:
    main_file = CORE / "main.py"
    if not main_file.exists():
        raise SystemExit(f"找不到錄製核心：{main_file}")
    os.chdir(CORE)
    if FROZEN:
        # PyInstaller's windowed child may inherit a Windows ANSI (GBK/CP950)
        # TextIOWrapper even though the UI reads the pipe as UTF-8. Force both
        # sides of the pipe to the same encoding; this also permits Korean room
        # names that cannot be represented by GBK.
        for stream_name, file_descriptor in (("stdout", 1), ("stderr", 2)):
            stream = getattr(sys, stream_name)
            if stream is None:
                stream = os.fdopen(
                    os.dup(file_descriptor), "w", encoding="utf-8",
                    errors="replace", buffering=1,
                )
                setattr(sys, stream_name, stream)
            elif hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    sys.path.insert(0, str(CORE))
    sys.argv = [str(main_file)]
    runpy.run_path(str(main_file), run_name="__main__")
