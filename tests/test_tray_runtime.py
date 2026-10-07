from __future__ import annotations

import os
import threading
import unittest
from unittest.mock import patch

from desktop_runtime import DesktopTraySession, ModePickerBridge
from tray_runtime import TrayController
from webui import server as recorder_server


class FakeWindow:
    def __init__(self) -> None:
        self.hidden = threading.Event()
        self.shown = 0
        self.destroyed = 0
        self.maximized = 0

    def hide(self) -> None:
        self.hidden.set()

    def show(self) -> None:
        self.shown += 1

    def destroy(self) -> None:
        self.destroyed += 1

    def maximize(self) -> None:
        self.maximized += 1


class TrayRuntimeTests(unittest.TestCase):
    def test_desktop_close_hides_until_explicit_exit(self) -> None:
        window = FakeWindow()
        session = DesktopTraySession(window, lambda: True)
        self.assertFalse(session.on_closing())
        self.assertTrue(window.hidden.wait(2))
        session.open_ui()
        self.assertEqual(window.shown, 1)
        session.exit_app()
        self.assertEqual(window.destroyed, 1)
        self.assertTrue(session.on_closing())

    def test_picker_close_without_desktop_choice_exits(self) -> None:
        window = FakeWindow()
        session = DesktopTraySession(window, lambda: False)
        self.assertTrue(session.on_closing())
        self.assertFalse(window.hidden.is_set())

    def test_menu_labels_follow_language_and_core_status(self) -> None:
        state = {"language": "zh-TW", "running": False}
        opened: list[bool] = []
        exited: list[bool] = []
        tray = TrayController(
            open_ui=lambda: opened.append(True),
            exit_app=lambda: exited.append(True),
            recorder_running=lambda: state["running"],
            language=lambda: state["language"],
        )
        self.assertEqual(tray._label("stopped"), "錄製核心：未啟動")
        state.update(language="en", running=True)
        self.assertEqual(tray._label("running"), "Recorder core: running")
        tray._on_open(None, None)
        tray._on_exit(None, None)
        self.assertEqual((len(opened), len(exited)), (1, 1))

    def test_unsaved_language_preserves_browser_preference(self) -> None:
        with patch.object(recorder_server, "UI_LANGUAGE_FILE") as language_file:
            language_file.read_text.side_effect = FileNotFoundError
            self.assertIsNone(recorder_server.read_ui_language())

    def test_picker_starts_tray_only_for_desktop(self) -> None:
        class FakeSession:
            started = 0

            def start(self) -> None:
                self.started += 1

        bridge = ModePickerBridge()
        bridge._window = FakeWindow()
        bridge._tray_session = FakeSession()
        with patch.object(recorder_server, "start_enabled_rooms"):
            self.assertEqual(bridge.choose_mode("desktop"), {"mode": "desktop"})
        self.assertEqual(bridge._tray_session.started, 1)
        self.assertEqual(bridge._window.maximized, 1)

    def test_web_tray_exit_shuts_down_server(self) -> None:
        class FakeServer:
            def __init__(self) -> None:
                self.stopped = threading.Event()
                self.shutdown_called = False

            def serve_forever(self) -> None:
                self.stopped.wait(2)

            def shutdown(self) -> None:
                self.shutdown_called = True
                self.stopped.set()

        class FakeTray:
            def __init__(self, **kwargs) -> None:
                self.exit_app = kwargs["exit_app"]
                self.stopped = False

            def start_background(self) -> None:
                self.exit_app()

            def stop(self) -> None:
                self.stopped = True

        fake_server = FakeServer()
        with (
            patch.object(recorder_server, "create_server", return_value=fake_server),
            patch.object(recorder_server, "close_server") as close_server,
            patch("tray_runtime.TrayController", FakeTray),
            patch.dict(os.environ, {"LIVE_RECORDER_PORT": "8765", "LIVE_RECORDER_NO_BROWSER": "1"}),
        ):
            recorder_server.main()
        self.assertTrue(fake_server.shutdown_called)
        close_server.assert_called_once_with(fake_server)


if __name__ == "__main__":
    unittest.main()
