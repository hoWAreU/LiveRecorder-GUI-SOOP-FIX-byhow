"""Windows notification-area controls for the desktop and web interfaces."""

from __future__ import annotations

import threading
from collections.abc import Callable

import pystray
from PIL import Image, ImageDraw


_LABELS = {
    "zh-TW": {
        "open": "開啟介面",
        "running": "錄製核心：執行中",
        "stopped": "錄製核心：未啟動",
        "exit": "停止錄製並結束程式",
    },
    "en": {
        "open": "Open interface",
        "running": "Recorder core: running",
        "stopped": "Recorder core: stopped",
        "exit": "Stop recording and exit",
    },
}


def _icon_image() -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((3, 3, 60, 60), radius=12, fill=(27, 33, 46, 255))
    draw.ellipse((13, 13, 50, 50), outline=(82, 128, 255, 255), width=6)
    draw.ellipse((27, 27, 36, 36), fill=(238, 243, 255, 255))
    return image


class TrayController:
    def __init__(
        self,
        *,
        open_ui: Callable[[], None],
        exit_app: Callable[[], None],
        recorder_running: Callable[[], bool],
        language: Callable[[], str | None],
    ) -> None:
        self._open_ui = open_ui
        self._exit_app = exit_app
        self._recorder_running = recorder_running
        self._language = language
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None
        self._icon = pystray.Icon(
            "LiveRecorder",
            _icon_image(),
            "LiveRecorder",
            menu=pystray.Menu(
                pystray.MenuItem(lambda _: self._label("open"), self._on_open, default=True),
                pystray.MenuItem(
                    lambda _: self._label("running" if self._recorder_running() else "stopped"),
                    lambda _icon, _item: None,
                    enabled=False,
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem(lambda _: self._label("exit"), self._on_exit),
            ),
        )

    def _label(self, key: str) -> str:
        labels = _LABELS["en" if self._language() == "en" else "zh-TW"]
        return labels[key]

    def _on_open(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        self._open_ui()

    def _on_exit(self, _icon: pystray.Icon, _item: pystray.MenuItem) -> None:
        self._exit_app()

    def start_background(self) -> None:
        if self._thread is not None:
            return

        def setup(icon: pystray.Icon) -> None:
            icon.visible = True
            self._ready.set()

        def run() -> None:
            try:
                self._icon.run(setup)
            except BaseException as exc:
                self._error = exc
                self._ready.set()

        self._thread = threading.Thread(target=run, name="LiveRecorder-tray", daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=5) or self._error is not None:
            self.stop()
            raise RuntimeError("無法建立 LiveRecorder 系統匣圖示") from self._error

    def stop(self) -> None:
        if self._thread is None:
            return
        self._icon.stop()
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=3)
        self._thread = None
