from __future__ import annotations

import errno
import json
import mimetypes
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from collections import deque
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from opencc import OpenCC
from app_runtime import APP_ROOT, BUNDLE_ROOT, CONFIG_ROOT, CORE, DOWNLOAD_ROOT, core_command

if os.name == "nt":
    import ctypes
    from ctypes import wintypes


ROOT = APP_ROOT
STATIC = BUNDLE_ROOT / "webui" / "static"
DESKTOP_STATIC = BUNDLE_ROOT / "desktop-ui" / "dist"
UI_LANGUAGE_FILE = APP_ROOT / ".ui-language.json"
UI_LANGUAGE_LOCK = threading.Lock()
CONFIG = CONFIG_ROOT / "config.ini"
URL_CONFIG = CONFIG_ROOT / "URL_config.ini"
TO_TRADITIONAL = OpenCC("s2twp")


def read_ui_language() -> str | None:
    with UI_LANGUAGE_LOCK:
        try:
            saved = json.loads(UI_LANGUAGE_FILE.read_text(encoding="utf-8")).get("language")
        except (OSError, ValueError, TypeError, AttributeError):
            saved = None
    return saved if saved in ("zh-TW", "en") else None


class LocalHTTPServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR can permit multiple processes to listen on the same
    # port. Never let a new UI instance silently share an older recorder's port.
    allow_reuse_address = False

    def server_bind(self) -> None:
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()
QUALITIES = ("2K", "1080P", "720P", "540P", "360P", "240P")
LEGACY_QUALITY = {"原畫": "1080P", "原画": "1080P", "藍光": "1080P", "蓝光": "1080P", "超清": "720P", "高清": "540P", "標清": "360P", "标清": "360P", "流暢": "240P", "流畅": "240P"}


def create_kill_on_close_job():
    """Return a Windows Job handle that terminates all members on close."""
    if os.name != "nt":
        return None

    class IoCounters(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", BasicLimitInformation),
            ("IoInfo", IoCounters),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return None
    info = ExtendedLimitInformation()
    info.BasicLimitInformation.LimitFlags = 0x00002000
    if not kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
        kernel32.CloseHandle(job)
        return None
    return job


def assign_to_job(job, process_handle: int) -> bool:
    if os.name != "nt" or not job:
        return False
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    return bool(kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(process_handle)))


def close_job(job) -> None:
    if os.name == "nt" and job:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel32.CloseHandle(job)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def ensure_configs() -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    for runtime, example in ((CONFIG, CONFIG.with_name("config.example.ini")), (URL_CONFIG, URL_CONFIG.with_name("URL_config.example.ini"))):
        if not runtime.exists() and example.exists():
            shutil.copyfile(example, runtime)


def get_ini(section: str, key: str, default: str = "") -> str:
    active = False
    for line in read_text(CONFIG).splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            active = stripped == f"[{section}]"
        elif active and re.match(rf"^\s*{re.escape(key)}\s*=", line):
            return line.split("=", 1)[1].strip()
    return default


def set_ini(section: str, key: str, value: str) -> None:
    lines = read_text(CONFIG).splitlines()
    active = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            active = stripped == f"[{section}]"
        elif active and re.match(rf"^\s*{re.escape(key)}\s*=", line):
            lines[index] = f"{key} = {value}"
            CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    section_index = next((i for i, line in enumerate(lines) if line.strip() == f"[{section}]"), None)
    if section_index is None:
        raise KeyError(f"找不到設定區段：[{section}]")
    insert_at = next((i for i in range(section_index + 1, len(lines)) if lines[i].strip().startswith("[")), len(lines))
    lines.insert(insert_at, f"{key} = {value}")
    CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_rooms() -> list[dict]:
    rooms = []
    for raw in read_text(URL_CONFIG).splitlines():
        line = raw.strip()
        if not line or line.startswith("##"):
            continue
        enabled = not line.startswith("#")
        line = line.lstrip("#").strip()
        if not line or line.startswith("每行格式") or "://" not in line:
            continue
        parts = [part.strip() for part in re.split("[,，]", line, maxsplit=2)]
        if len(parts) == 1:
            quality, url, name = "1080P", parts[0], ""
        elif parts[0] in QUALITIES:
            quality, url, name = parts[0], parts[1], parts[2] if len(parts) > 2 else ""
        elif parts[0] in LEGACY_QUALITY:
            quality, url, name = LEGACY_QUALITY[parts[0]], parts[1], parts[2] if len(parts) > 2 else ""
        else:
            quality, url, name = "1080P", parts[0], parts[1]
        name = TO_TRADITIONAL.convert(re.sub(r"^主播:\s*", "", name))
        rooms.append({"id": str(len(rooms)), "enabled": enabled, "quality": quality, "url": url, "name": name})
    return rooms


def save_rooms(rooms: list[dict]) -> None:
    lines = []
    for room in rooms:
        prefix = "" if room.get("enabled", True) else "#"
        quality = room.get("quality") if room.get("quality") in QUALITIES else "1080P"
        url = str(room.get("url", "")).strip()
        name = str(room.get("name", "")).strip()
        if url:
            lines.append(f"{prefix}{quality},{url}" + (f",{name}" if name else ""))
    URL_CONFIG.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


class Recorder:
    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None
        self.logs: deque[dict] = deque(maxlen=3000)
        self.sequence = 0
        self.lock = threading.Lock()
        self.started_at: float | None = None
        self.windows_job = create_kill_on_close_job()

    @property
    def running(self) -> bool:
        return bool(self.process and self.process.poll() is None)

    def append(self, text: str, level: str = "info") -> None:
        text = TO_TRADITIONAL.convert(re.sub(r"\x1b\[[0-9;]*m", "", text).rstrip())
        if not text:
            return
        with self.lock:
            self.sequence += 1
            self.logs.append({"id": self.sequence, "text": text, "level": level, "time": time.strftime("%H:%M:%S")})

    def start(self) -> tuple[bool, str]:
        if self.running:
            return False, "錄製核心已在執行"
        if not any(room["enabled"] for room in parse_rooms()):
            return False, "請先啟用至少一個直播間"
        command, core_cwd = core_command()
        flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        env = os.environ.copy()
        env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"})
        self.process = subprocess.Popen(
            command, cwd=core_cwd,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace", creationflags=flags, env=env,
        )
        if os.name == "nt" and self.windows_job and not assign_to_job(self.windows_job, self.process._handle):
            self.append("警告：無法建立程序連動關閉，關閉視窗前請先停止所有直播", "error")
        self.started_at = time.time()
        self.append("=== 錄製核心已啟動 ===", "success")
        threading.Thread(target=self._read, daemon=True).start()
        return True, "錄製核心已啟動"

    def _read(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            level = "error" if "ERROR" in line or "錯誤" in line else "info"
            self.append(line, level)
        code = self.process.wait()
        self.append(f"=== 錄製核心已結束（代碼 {code}）===", "error" if code else "success")

    def stop(self) -> tuple[bool, str]:
        if not self.running:
            return False, "錄製核心尚未執行"
        assert self.process
        pid = self.process.pid
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            self.process.send_signal(signal.SIGTERM)
        self.append("正在停止錄製核心…")
        return True, "停止指令已送出"

    def get_logs(self, since: int) -> list[dict]:
        with self.lock:
            return [item for item in self.logs if item["id"] > since]

    def close(self) -> None:
        close_job(self.windows_job)
        self.windows_job = None


RECORDER = Recorder()
PREVIEW_CACHE: dict[str, tuple[bytes, str, float]] = {}
PREVIEW_CACHE_LOCK = threading.Lock()
RECORDING_PREVIEW_CACHE: dict[str, tuple[bytes, float, float]] = {}
VIDEO_EXTENSIONS = {".ts", ".mkv", ".flv", ".mp4"}


def recording_roots() -> list[Path]:
    roots = [DOWNLOAD_ROOT]
    configured = get_ini("录制设置", "直播保存路径(不填则默认)").strip()
    if configured:
        path = Path(configured).expanduser()
        roots.insert(0, path if path.is_absolute() else CORE / path)
    return list(dict.fromkeys(path.resolve() for path in roots if path.exists()))


def capture_recording_preview(bj_id: str) -> bytes | None:
    """Capture a recent frame from the newest recording for this streamer."""
    candidates: list[Path] = []
    bj_key = bj_id.casefold()
    for root in recording_roots():
        try:
            candidates.extend(
                path for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
                and bj_key in str(path.relative_to(root)).casefold()
            )
        except OSError:
            continue
    if not candidates:
        return None
    source = max(candidates, key=lambda path: path.stat().st_mtime)
    try:
        source_mtime = source.stat().st_mtime
    except OSError:
        return None
    # Do not present an old recording as if it were a current live frame.
    if time.time() - source_mtime > 120:
        return None
    cached = RECORDING_PREVIEW_CACHE.get(bj_id)
    if cached and cached[1] == source_mtime and time.time() - cached[2] < 12:
        return cached[0]
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-sseof", "-3",
        "-i", str(source), "-map", "0:v:0", "-frames:v", "1",
        "-vf", "scale=960:-2", "-q:v", "4", "-f", "image2pipe", "-vcodec", "mjpeg", "pipe:1",
    ]
    try:
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=8, creationflags=flags, check=False,
        )
        if result.returncode == 0 and result.stdout.startswith(b"\xff\xd8\xff"):
            RECORDING_PREVIEW_CACHE[bj_id] = (result.stdout, source_mtime, time.time())
            return result.stdout
    except (OSError, subprocess.TimeoutExpired):
        pass
    return cached[0] if cached else None


def fetch_soop_preview(broad_no: str, bj_id: str) -> tuple[bytes, str, str]:
    """Fetch a SOOP thumbnail, falling back to the last valid image."""
    preview_url = f"https://liveimg.sooplive.com/m/{broad_no}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/138 Safari/537.36",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Referer": "https://play.sooplive.com/",
    }
    last_error: Exception | None = None
    for attempt in range(2):
        try:
            request = urllib.request.Request(
                f"{preview_url}?t={int(time.time() * 1000)}-{attempt}", headers=headers
            )
            with urllib.request.urlopen(request, timeout=6) as response:
                data = response.read(8 * 1024 * 1024)
                content_type = response.headers.get_content_type()
            is_image = content_type.startswith("image/") or data.startswith(
                (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF8", b"RIFF")
            )
            if not is_image or len(data) < 100:
                raise ValueError("SOOP preview response is not a valid image")
            if not content_type.startswith("image/"):
                content_type = "image/jpeg"
            with PREVIEW_CACHE_LOCK:
                PREVIEW_CACHE[broad_no] = (data, content_type, time.time())
            return data, content_type, "fresh"
        except Exception as exc:
            last_error = exc
            if getattr(exc, "code", None) == HTTPStatus.NOT_FOUND:
                break
            if attempt == 0:
                time.sleep(0.25)
    with PREVIEW_CACHE_LOCK:
        cached = PREVIEW_CACHE.get(broad_no)
    if cached:
        return cached[0], cached[1], "stale"

    # A broadcast thumbnail returns 404 after that broadcast ends. Keep the
    # preview useful by showing the streamer's current profile image instead.
    safe_bj_id = urllib.parse.quote(bj_id, safe="")
    bucket = urllib.parse.quote(bj_id[:2], safe="")
    profile_url = f"https://stimg.sooplive.com/LOGO/{bucket}/{safe_bj_id}/m/{safe_bj_id}.webp"
    try:
        request = urllib.request.Request(profile_url, headers=headers)
        with urllib.request.urlopen(request, timeout=6) as response:
            data = response.read(8 * 1024 * 1024)
            content_type = response.headers.get_content_type()
        if not content_type.startswith("image/") or len(data) < 100:
            raise ValueError("SOOP profile response is not a valid image")
        return data, content_type, "profile"
    except Exception:
        raise last_error or RuntimeError("SOOP preview unavailable")


class Handler(BaseHTTPRequestHandler):
    server_version = "LiveRecorderWeb/1.0"

    def log_message(self, _format: str, *_args) -> None:
        pass

    def send_json(self, payload, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/ui-language":
            self.send_json({"language": read_ui_language()})
        elif parsed.path == "/api/state":
            self.send_json({
                "rooms": parse_rooms(), "running": RECORDER.running,
                "startedAt": RECORDER.started_at,
                "settings": {
                    "output": get_ini("录制设置", "直播保存路径(不填则默认)"),
                    "format": get_ini("录制设置", "视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频", "ts"),
                    "interval": get_ini("录制设置", "循环时间(秒)", "300"),
                    "fps": get_ini("录制设置", "偏好帧率(自动|30|60)", "自动").replace("自动", "自動"),
                    "proxyEnabled": get_ini("录制设置", "是否使用代理ip(是/否)", "否") == "是",
                    "proxy": get_ini("录制设置", "代理地址"),
                    "soopUsername": get_ini("账号密码", "sooplive账号"),
                    "hasSoopPassword": bool(get_ini("账号密码", "sooplive密码")),
                    "hasSoopCookie": bool(get_ini("Cookie", "sooplive_cookie")),
                },
            })
        elif parsed.path == "/api/logs":
            since = int(urllib.parse.parse_qs(parsed.query).get("since", ["0"])[0])
            self.send_json({"logs": RECORDER.get_logs(since), "running": RECORDER.running})
        elif parsed.path == "/api/preview":
            url = urllib.parse.parse_qs(parsed.query).get("url", [""])[0]
            match = re.search(r"play\.sooplive\.(?:com|co\.kr)/([^/]+)/(\d+)", url)
            if not match:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            try:
                bj_id, broad_no = match.group(1), match.group(2)
                recording_frame = capture_recording_preview(bj_id)
                if recording_frame:
                    data, content_type, preview_source = recording_frame, "image/jpeg", "recording"
                else:
                    data, content_type, preview_source = fetch_soop_preview(broad_no, bj_id)
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Preview-Source", preview_source)
                self.end_headers()
                self.wfile.write(data)
            except Exception:
                self.send_error(HTTPStatus.BAD_GATEWAY)
        elif parsed.path.startswith("/api/"):
            self.send_json({"error": "找不到 API"}, 404)
        else:
            if parsed.path == "/legacy":
                self.send_response(308)
                self.send_header("Location", "/legacy/")
                self.end_headers()
                return
            legacy = parsed.path.startswith("/legacy/")
            static_root = STATIC if legacy else DESKTOP_STATIC
            if legacy:
                relative = parsed.path.removeprefix("/legacy/")
            elif parsed.path == "/desktop" or parsed.path.startswith("/desktop/"):
                relative = parsed.path.removeprefix("/desktop/")
            else:
                relative = parsed.path.lstrip("/")
            if relative in ("", "desktop"):
                relative = "index.html"
            target = (static_root / relative).resolve()
            if static_root.resolve() not in target.parents and target != static_root.resolve():
                self.send_error(HTTPStatus.FORBIDDEN)
                return
            if not target.is_file():
                target = static_root / "index.html"
            if not target.is_file():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            data = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

    def do_POST(self) -> None:
        try:
            payload = self.read_json()
            if self.path == "/api/ui-language":
                language = payload.get("language")
                if language not in ("zh-TW", "en"):
                    raise ValueError("不支援的介面語言")
                with UI_LANGUAGE_LOCK:
                    temporary = UI_LANGUAGE_FILE.with_suffix(".tmp")
                    temporary.write_text(json.dumps({"language": language}), encoding="utf-8")
                    temporary.replace(UI_LANGUAGE_FILE)
                self.send_json({"language": language})
            elif self.path == "/api/recorder/start":
                ok, message = RECORDER.start()
                self.send_json({"ok": ok, "message": message}, 200 if ok else 409)
            elif self.path == "/api/recorder/stop":
                ok, message = RECORDER.stop()
                self.send_json({"ok": ok, "message": message}, 200 if ok else 409)
            elif self.path == "/api/rooms/save":
                save_rooms(payload.get("rooms", []))
                self.send_json({"ok": True, "rooms": parse_rooms()})
            elif self.path == "/api/room/control":
                rooms = parse_rooms()
                room_index = int(payload.get("index", -1))
                if room_index < 0 or room_index >= len(rooms):
                    raise IndexError("找不到指定的直播間")
                enabled = bool(payload.get("enabled"))
                rooms[room_index]["enabled"] = enabled
                save_rooms(rooms)
                message = "此直播間已開始監看與錄製" if enabled else "此直播間已停止錄製"
                if enabled and not RECORDER.running:
                    _, start_message = RECORDER.start()
                    message = f"{message}；{start_message}"
                elif not enabled and RECORDER.running and not any(room["enabled"] for room in rooms):
                    _, stop_message = RECORDER.stop()
                    message = f"{message}；{stop_message}"
                RECORDER.append(f"[{rooms[room_index]['name'] or rooms[room_index]['url']}] {message}", "success")
                self.send_json({"ok": True, "message": message, "rooms": parse_rooms(), "running": RECORDER.running})
            elif self.path == "/api/settings":
                interval = max(10, int(payload.get("interval", 300)))
                set_ini("录制设置", "直播保存路径(不填则默认)", str(payload.get("output", "")).strip())
                set_ini("录制设置", "视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频", str(payload.get("format", "ts")))
                set_ini("录制设置", "循环时间(秒)", str(interval))
                set_ini("录制设置", "偏好帧率(自动|30|60)", str(payload.get("fps", "自動")).replace("自動", "自动"))
                set_ini("录制设置", "是否使用代理ip(是/否)", "是" if payload.get("proxyEnabled") else "否")
                set_ini("录制设置", "代理地址", str(payload.get("proxy", "")).strip())
                set_ini("账号密码", "sooplive账号", str(payload.get("soopUsername", "")).strip())
                if payload.get("soopPassword"):
                    set_ini("账号密码", "sooplive密码", str(payload["soopPassword"]))
                if payload.get("soopCookie"):
                    set_ini("Cookie", "sooplive_cookie", str(payload["soopCookie"]).strip())
                self.send_json({"ok": True})
            elif self.path == "/api/open-downloads":
                configured = get_ini("录制设置", "直播保存路径(不填则默认)").strip()
                target = Path(configured).expanduser() if configured else DOWNLOAD_ROOT
                if not target.is_absolute():
                    target = CORE / target
                target.mkdir(parents=True, exist_ok=True)
                if os.name == "nt":
                    os.startfile(target)
                else:
                    subprocess.Popen(["xdg-open", str(target)])
                self.send_json({"ok": True})
            else:
                self.send_json({"error": "找不到 API"}, 404)
        except Exception as exc:
            self.send_json({"error": TO_TRADITIONAL.convert(str(exc))}, 400)


def start_enabled_rooms(source: str = "Web UI") -> None:
    enabled_rooms = [room for room in parse_rooms() if room["enabled"]]
    if enabled_rooms and os.environ.get("LIVE_RECORDER_UI_PREVIEW") != "1":
        ok, message = RECORDER.start()
        RECORDER.append(
            f"{source} 啟動時偵測到 {len(enabled_rooms)} 個已啟用直播：{message}",
            "success" if ok else "error",
        )


def create_server(port: int, *, auto_start: bool = True) -> ThreadingHTTPServer:
    ensure_configs()
    host = "127.0.0.1"
    server = LocalHTTPServer((host, port), Handler)
    if auto_start:
        start_enabled_rooms()
    return server


def close_server(server: ThreadingHTTPServer) -> None:
    if RECORDER.running:
        RECORDER.stop()
    server.server_close()
    RECORDER.close()


def main() -> None:
    from tray_runtime import TrayController

    port = int(os.environ.get("LIVE_RECORDER_PORT", "8765"))
    try:
        server = create_server(port)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE or getattr(exc, "winerror", None) == 10048:
            raise SystemExit(
                f"無法啟動網頁版：127.0.0.1:{port} 已被其他服務占用。"
                "請確認舊服務是否仍在錄製；安全停止後再重新啟動新版。"
            ) from None
        raise
    address = f"http://127.0.0.1:{port}/"
    stopped = threading.Event()
    server_errors: list[BaseException] = []

    def serve() -> None:
        try:
            server.serve_forever()
        except BaseException as exc:
            server_errors.append(exc)
        finally:
            stopped.set()

    worker = threading.Thread(target=serve, name="web-ui-http", daemon=True)
    worker.start()
    tray: TrayController | None = None
    try:
        tray = TrayController(
            open_ui=lambda: webbrowser.open(address),
            exit_app=stopped.set,
            recorder_running=lambda: RECORDER.running,
            language=read_ui_language,
        )
        tray.start_background()
        print(f"LiveRecorder Web UI：{address}")
        if os.environ.get("LIVE_RECORDER_NO_BROWSER") != "1":
            opener = threading.Timer(0.3, lambda: webbrowser.open(address))
            opener.daemon = True
            opener.start()
        stopped.wait()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        worker.join(timeout=3)
        if tray is not None:
            tray.stop()
        close_server(server)
    if server_errors:
        raise RuntimeError("LiveRecorder 網頁服務異常結束") from server_errors[0]


if __name__ == "__main__":
    main()
