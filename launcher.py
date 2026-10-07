from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from app_runtime import APP_ROOT, CORE, ensure_runtime_layout, run_core


def launch_desktop(root: tk.Tk | None = None) -> None:
    if root:
        root.destroy()
    try:
        from desktop_runtime import run_desktop
        run_desktop()
    except Exception as exc:
        messagebox.showwarning("桌面介面無法啟動", f"React 桌面介面無法啟動：\n{exc}\n\n將開啟傳統桌面介面。")
        from gui import RecorderGUI
        RecorderGUI().mainloop()


def launch_web(root: tk.Tk | None = None) -> None:
    if root:
        root.destroy()
    from webui import server

    try:
        server.main()
    except SystemExit as exc:
        # PyInstaller is windowed, so a console-only port conflict would be invisible.
        messagebox.showerror("網頁服務無法啟動", str(exc))


def launch_legacy_picker() -> None:
    """Keep a Tkinter chooser available when WebView2 cannot start."""
    root = tk.Tk()
    root.title("LiveRecorder")
    root.geometry("500x310")
    root.resizable(False, False)
    root.configure(bg="#18191d")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Root.TFrame", background="#18191d")
    style.configure("Card.TFrame", background="#232428")
    style.configure("Title.TLabel", background="#232428", foreground="#f4f4f5", font=("Microsoft JhengHei UI", 21, "bold"))
    style.configure("Sub.TLabel", background="#232428", foreground="#92959f", font=("Microsoft JhengHei UI", 10))
    style.configure("Mode.TButton", background="#292a2f", foreground="#f4f4f5", bordercolor="#3a3c43", padding=(18, 15), font=("Microsoft JhengHei UI", 12, "bold"))
    style.map("Mode.TButton", background=[("active", "#34363d"), ("pressed", "#4b7cff")])
    style.configure("Web.TButton", background="#4b7cff", foreground="#ffffff", bordercolor="#4b7cff", padding=(18, 15), font=("Microsoft JhengHei UI", 12, "bold"))
    style.map("Web.TButton", background=[("active", "#5c89ff"), ("pressed", "#365fd6")])

    outer = ttk.Frame(root, padding=22, style="Root.TFrame")
    outer.pack(fill="both", expand=True)
    card = ttk.Frame(outer, padding=26, style="Card.TFrame")
    card.pack(fill="both", expand=True)
    ttk.Label(card, text="LIVE RECORDER", style="Title.TLabel").pack(anchor="w")
    ttk.Label(card, text="請選擇要使用的操作介面", style="Sub.TLabel").pack(anchor="w", pady=(4, 24))

    actions = ttk.Frame(card, style="Card.TFrame")
    actions.pack(fill="x")
    ttk.Button(actions, text="▣  桌面版", style="Mode.TButton", command=lambda: launch_desktop(root)).pack(side="left", fill="x", expand=True, padx=(0, 7))
    ttk.Button(actions, text="◎  網頁版", style="Web.TButton", command=lambda: launch_web(root)).pack(side="left", fill="x", expand=True, padx=(7, 0))
    ttk.Label(card, text="桌面版適合單機操作；網頁版會在預設瀏覽器開啟。", style="Sub.TLabel").pack(anchor="w", pady=(20, 0))
    root.mainloop()


def main() -> None:
    ensure_runtime_layout()
    if "--core" in sys.argv:
        run_core()
        return
    if "--self-test" in sys.argv:
        if sys.stdout is not None:
            sys.stdout.reconfigure(encoding="utf-8", errors="strict", line_buffering=True)
            print("UTF-8 自我測試：그릴래영")
        test_log = APP_ROOT / "self-test.log"
        test_log.write_text("start\n", encoding="utf-8")
        def mark(step: str) -> None:
            with test_log.open("a", encoding="utf-8") as file:
                file.write(step + "\n")
        os.chdir(CORE)
        sys.path.insert(0, str(CORE))
        import httpx  # noqa: F401
        mark("httpx")
        import requests  # noqa: F401
        mark("requests")
        import loguru  # noqa: F401
        mark("loguru")
        import execjs  # noqa: F401
        mark("execjs")
        from Crypto.Cipher import AES  # noqa: F401
        mark("crypto")
        import smtplib  # noqa: F401
        import msg_push  # noqa: F401
        mark("msg_push")
        import ffmpeg_install  # noqa: F401
        import i18n  # noqa: F401
        mark("core_helpers")
        import src  # noqa: F401
        mark("src")
        from src import spider  # noqa: F401
        mark("spider")
        import webview  # noqa: F401
        mark("webview")
        if not (CORE.parent / "desktop-ui" / "dist" / "index.html").exists():
            raise SystemExit(2)
        mark("desktop_ui")
        if not (CORE / "config" / "config.example.ini").exists():
            raise SystemExit(2)
        mark("ok")
        test_log.unlink(missing_ok=True)
        return
    if "--desktop" in sys.argv:
        launch_desktop()
        return
    if "--desktop-classic" in sys.argv:
        from gui import RecorderGUI
        RecorderGUI().mainloop()
        return
    if "--web" in sys.argv:
        launch_web()
        return
    if not (CORE / "main.py").exists():
        messagebox.showerror("缺少錄製核心", f"找不到：\n{CORE / 'main.py'}")
        return

    try:
        from desktop_runtime import run_mode_picker
        selected_mode = run_mode_picker()
    except Exception as exc:
        messagebox.showwarning("新版啟動器無法啟動", f"React 啟動器無法啟動：\n{exc}\n\n將開啟備用選擇視窗。")
        launch_legacy_picker()
        return
    if selected_mode == "web":
        launch_web()


if __name__ == "__main__":
    main()
