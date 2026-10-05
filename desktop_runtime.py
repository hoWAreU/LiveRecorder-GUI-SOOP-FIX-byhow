"""Run the React desktop UI in a native WebView2 window."""

from __future__ import annotations

import threading

from app_runtime import BUNDLE_ROOT
from webui import server as recorder_server


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
