# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

project = Path(SPECPATH)
datas = []

excluded_dirs = {".git", ".github", ".venv", "downloads", "logs", "backup_config", "__pycache__"}
excluded_files = {
    Path("config/config.ini"),
    Path("config/URL_config.ini"),
    Path(".dockerignore"),
    Path(".gitignore"),
    Path("demo.py"),
    Path("docker-compose.yaml"),
    Path("Dockerfile"),
    Path("index.html"),
    Path("pyproject.toml"),
    Path("README.md"),
    Path("requirements.txt"),
    Path("StopRecording.vbs"),
}

core_root = project / "recorder-core"
for source in core_root.rglob("*"):
    relative = source.relative_to(core_root)
    if not source.is_file() or any(part in excluded_dirs for part in relative.parts):
        continue
    if relative in excluded_files or source.suffix in {".pyc", ".log"}:
        continue
    datas.append((str(source), str(Path("recorder-core") / relative.parent)))

static_root = project / "webui" / "static"
for source in static_root.rglob("*"):
    if source.is_file():
        datas.append((str(source), str(Path("webui/static") / source.relative_to(static_root).parent)))

desktop_root = project / "desktop-ui" / "dist"
if not (desktop_root / "index.html").is_file():
    raise SystemExit("Missing desktop-ui/dist/index.html. Run npm ci and npm run build in desktop-ui first.")
for source in desktop_root.rglob("*"):
    if source.is_file():
        datas.append((str(source), str(Path("desktop-ui/dist") / source.relative_to(desktop_root).parent)))

hiddenimports = []
for package in ("httpx", "httpcore", "h2", "requests", "loguru", "Crypto", "distro", "tqdm", "execjs"):
    hiddenimports += collect_submodules(package)
hiddenimports += collect_submodules("email")
hiddenimports += collect_submodules("webview")
hiddenimports += ["pystray._win32"]
hiddenimports += [
    "smtplib", "gettext", "inspect", "configparser", "gzip", "ssl",
    "email.header", "email.mime.multipart", "email.mime.text",
]

a = Analysis(
    ["launcher.py"],
    pathex=[str(project), str(core_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="LiveRecorder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="LiveRecorder",
)
