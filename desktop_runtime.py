"""Run the React desktop UI in a native WebView2 window."""

from __future__ import annotations

import threading
from typing import Any

from app_runtime import BUNDLE_ROOT
from webui import server as recorder_server


class ModePickerBridge:
    """Handle the first choice without starting recording before it is made."""

    def __init__(self) -> None:
        # pywebview recursively inspects public js_api attributes. Keep the
        # native Window private or it will traverse its entire object graph.
        self._mode: str | None = None
        self._window: Any = None
        self._lock = threading.Lock()

    def choose_mode(self, mode: str) -> dict[str, str]:
        if mode not in ("desktop", "web"):
            raise ValueError("不支援的介面模式")
        with self._lock:
            if self._mode is not None:
                return {"mode": self._mode}
            self._mode = mode

        if mode == "desktop":
            try:
                recorder_server.start_enabled_rooms("桌面版")
            except Exception as exc:
                recorder_server.RECORDER.append(f"自動啟動錄製失敗：{exc}", "error")
            try:
                self._window.title = "LiveRecorder 控制台"
                self._window.maximize()
            except Exception:
                pass  # The React view can still load at the picker's size.
        else:
            # Let the JS bridge reply before destroying the picker window.
            closer = threading.Timer(0.2, self._window.destroy)
            closer.daemon = True
            closer.start()
        return {"mode": mode}


def run_mode_picker() -> str | None:
    import webview

    index = BUNDLE_ROOT / "desktop-ui" / "dist" / "index.html"
    if not index.is_file():
        raise FileNotFoundError(f"找不到桌面介面：{index}。請先執行 desktop-ui 的 npm run build。")

    httpd = recorder_server.create_server(0, auto_start=False)
    worker = threading.Thread(target=httpd.serve_forever, name="mode-picker-http", daemon=True)
    worker.start()
    bridge = ModePickerBridge()
    completed = False
    try:
        port = httpd.server_address[1]
        bridge._window = webview.create_window(
            "LiveRecorder · 選擇介面", f"http://127.0.0.1:{port}/desktop/?launcher=1",
            js_api=bridge, width=820, height=500, min_size=(700, 450),
            background_color="#121720",
        )
        webview.start(gui="edgechromium", private_mode=False)
        completed = True
        return bridge._mode
    finally:
        httpd.shutdown()
        worker.join(timeout=3)
        if completed and bridge._mode == "web":
            # launch_web starts a new server in this process. Keep the recorder's
            # Windows Job alive so its later core process remains tied to it.
            httpd.server_close()
        else:
            recorder_server.close_server(httpd)


def run_desktop() -> None:
    import webview

    index = BUNDLE_ROOT / "desktop-ui" / "dist" / "index.html"
    if not index.is_file():
        raise FileNotFoundError(f"找不到桌面介面：{index}。請先執行 desktop-ui 的 npm run build。")

    httpd = recorder_server.create_server(0)
    worker = threading.Thread(target=httpd.serve_forever, name="desktop-ui-http", daemon=True)
    worker.start()
    try:
        port = httpd.server_address[1]
        webview.create_window(
            "LiveRecorder 控制台", f"http://127.0.0.1:{port}/desktop/",
            width=1280, height=780, min_size=(950, 650), maximized=True,
            background_color="#121720",
        )
        webview.start(gui="edgechromium", private_mode=False)
    finally:
        httpd.shutdown()
        worker.join(timeout=3)
        recorder_server.close_server(httpd)
