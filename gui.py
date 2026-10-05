from __future__ import annotations

import os
import queue
import re
import signal
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import json
import io
import urllib.request
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, scrolledtext
from PIL import Image, ImageTk
from opencc import OpenCC
from app_runtime import APP_ROOT, CONFIG_ROOT, CORE, DOWNLOAD_ROOT, core_command


ROOT = APP_ROOT
URL_CONFIG = CONFIG_ROOT / "URL_config.ini"
APP_CONFIG = CONFIG_ROOT / "config.ini"
GUI_CONFIG = ROOT / ".gui-settings.json"
QUALITIES = ("2K", "1080P", "720P", "540P", "360P", "240P")
LEGACY_QUALITY = {"原畫": "1080P", "原画": "1080P", "藍光": "1080P", "蓝光": "1080P", "超清": "720P", "高清": "540P", "標清": "360P", "标清": "360P", "流暢": "240P", "流畅": "240P"}
TO_TRADITIONAL = OpenCC("s2twp")


def ensure_runtime_configs() -> None:
    """Create private runtime configs from safe templates on first launch."""
    config_dir = CORE / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    for runtime_name, example_name in (
        ("config.ini", "config.example.ini"),
        ("URL_config.ini", "URL_config.example.ini"),
    ):
        runtime_path = config_dir / runtime_name
        example_path = config_dir / example_name
        if not runtime_path.exists() and example_path.exists():
            shutil.copyfile(example_path, runtime_path)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def set_ini_value(path: Path, section: str, key: str, value: str) -> None:
    lines = read_text(path).splitlines()
    in_section = False
    changed = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = stripped == f"[{section}]"
        elif in_section and re.match(rf"^\s*{re.escape(key)}\s*=", line):
            lines[index] = f"{key} = {value}"
            changed = True
            break
    if not changed:
        section_index = next((i for i, line in enumerate(lines) if line.strip() == f"[{section}]"), None)
        if section_index is None:
            raise KeyError(f"找不到設定區段：[{section}]")
        insert_at = next((i for i in range(section_index + 1, len(lines)) if lines[i].strip().startswith("[")), len(lines))
        lines.insert(insert_at, f"{key} = {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_ini_value(path: Path, section: str, key: str, default: str = "") -> str:
    in_section = False
    for line in read_text(path).splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = stripped == f"[{section}]"
        elif in_section and re.match(rf"^\s*{re.escape(key)}\s*=", line):
            return line.split("=", 1)[1].strip()
    return default


class RecorderGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        ensure_runtime_configs()
        self.title("Live Recorder 控制台")
        self.geometry("1440x860")
        self.minsize(1080, 680)
        self.process: subprocess.Popen[str] | None = None
        self.output_queue: queue.Queue[str] = queue.Queue()
        self.preview_queue: queue.Queue[tuple[str, int, object]] = queue.Queue()
        self.preview_request_id = 0
        self.preview_photo = None
        self._layout_after_id = None
        self.theme = self._load_theme()
        self._build_style()
        self._build_ui()
        self._bind_shortcuts()
        self.bind("<Configure>", self._schedule_adaptive_layout, add="+")
        self.apply_theme()
        self.load_rooms()
        self.load_settings()
        if os.environ.get("LIVE_RECORDER_UI_PREVIEW") != "1":
            self.after(350, self._auto_start_enabled_rooms)
        self.after(100, self._drain_output)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_style(self) -> None:
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

    def _bind_shortcuts(self) -> None:
        self.bind("<Control-n>", lambda _event: self.show_room_dialog())
        self.bind("<Control-comma>", lambda _event: self.show_settings_dialog())
        self.bind("<F2>", lambda _event: self.show_room_dialog(edit=True))
        self.bind("<Delete>", lambda _event: self.delete_room())

    def _prepare_dialog(self, dialog: tk.Toplevel, width: int, height: int) -> None:
        dialog.transient(self)
        dialog.resizable(False, False)
        dialog.configure(bg=self.colors["bg"])
        dialog.bind("<Escape>", lambda _event: dialog.destroy())
        self.update_idletasks()
        x = self.winfo_x() + max((self.winfo_width() - width) // 2, 0)
        y = self.winfo_y() + max((self.winfo_height() - height) // 2, 0)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.grab_set()

    def _schedule_adaptive_layout(self, event=None) -> None:
        if event is not None and event.widget is not self:
            return
        if self._layout_after_id is not None:
            self.after_cancel(self._layout_after_id)
        self._layout_after_id = self.after(40, self._apply_adaptive_layout)

    def _apply_adaptive_layout(self) -> None:
        self._layout_after_id = None
        width = max(self.winfo_width(), 1080)
        sidebar_width = min(360, max(270, int(width * 0.23)))
        details_width = min(440, max(360, int(width * 0.29)))
        try:
            self.workspace.sashpos(0, sidebar_width)
            self.workspace.sashpos(1, sidebar_width + details_width)
        except tk.TclError:
            pass

    def _load_theme(self) -> str:
        try:
            value = json.loads(GUI_CONFIG.read_text(encoding="utf-8")).get("theme")
            return value if value in ("light", "dark") else "dark"
        except (OSError, ValueError, TypeError):
            return "dark"

    def apply_theme(self) -> None:
        dark = self.theme == "dark"
        colors = {
            "bg": "#15171a" if dark else "#f3f5f8",
            "surface": "#202226" if dark else "#ffffff",
            "surface_alt": "#282b30" if dark else "#f7f8fa",
            "console": "#121417" if dark else "#f8f9fb",
            "field": "#181a1e" if dark else "#ffffff",
            "text": "#f4f5f7" if dark else "#18212f",
            "muted": "#989da8" if dark else "#687284",
            "border": "#363a42" if dark else "#d9dee7",
            "accent": "#4f7cff" if dark else "#2563eb",
            "accent_hover": "#638bff" if dark else "#1d4ed8",
            "select": "#30343b" if dark else "#eaf0fb",
            "select_text": "#ffffff" if dark else "#172554",
            "success": "#40c98a" if dark else "#16875b",
            "danger": "#ff5b67" if dark else "#c93645",
        }
        self.colors = colors
        self.configure(bg=colors["bg"])
        self.style.configure("App.TPanedwindow", background=colors["border"], sashwidth=4, relief="flat")
        self.style.configure("TFrame", background=colors["bg"])
        self.style.configure("Panel.TFrame", background=colors["surface"])
        self.style.configure("Console.TFrame", background=colors["console"])
        self.style.configure("TLabel", background=colors["bg"], foreground=colors["text"], font=("Microsoft JhengHei UI", 10))
        self.style.configure("Panel.TLabel", background=colors["surface"], foreground=colors["text"])
        self.style.configure("PanelSub.TLabel", background=colors["surface"], foreground=colors["muted"])
        self.style.configure("PanelMeta.TLabel", background=colors["surface"], foreground=colors["muted"], font=("Microsoft JhengHei UI", 9))
        self.style.configure("Console.TLabel", background=colors["console"], foreground=colors["text"])
        self.style.configure("ConsoleSub.TLabel", background=colors["console"], foreground=colors["muted"])
        self.style.configure("Title.TLabel", background=colors["surface"], foreground=colors["text"], font=("Microsoft JhengHei UI", 18, "bold"))
        self.style.configure("Section.TLabel", background=colors["surface"], foreground=colors["text"], font=("Microsoft JhengHei UI", 12, "bold"))
        self.style.configure("Sub.TLabel", background=colors["surface"], foreground=colors["muted"])
        self.style.configure("TButton", background=colors["surface_alt"], foreground=colors["text"], bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], padding=(12, 8), font=("Microsoft JhengHei UI", 10), relief="flat")
        self.style.map("TButton", background=[("active", colors["border"]), ("pressed", colors["accent"])])
        self.style.configure("Accent.TButton", background=colors["accent"], foreground="#ffffff", bordercolor=colors["accent"], font=("Microsoft JhengHei UI", 10, "bold"))
        self.style.map("Accent.TButton", background=[("active", colors["accent_hover"]), ("pressed", "#1d4ed8")])
        self.style.configure("Danger.TButton", background=colors["surface_alt"], foreground=colors["danger"], bordercolor=colors["danger"])
        self.style.map("Danger.TButton", background=[("active", colors["danger"])], foreground=[("active", "#ffffff")])
        self.style.configure("LiveBadge.TLabel", background="#173d2e" if dark else "#e3f6ed", foreground=colors["success"], padding=(9, 4), font=("Microsoft JhengHei UI", 9, "bold"))
        self.style.configure("PausedBadge.TLabel", background=colors["surface_alt"], foreground=colors["muted"], padding=(9, 4), font=("Microsoft JhengHei UI", 9, "bold"))
        self.style.configure("CoreBadge.TLabel", background=colors["console"], foreground=colors["success"], font=("Microsoft JhengHei UI", 9, "bold"))
        self.style.configure("TCheckbutton", background=colors["bg"], foreground=colors["text"])
        self.style.map("TCheckbutton", background=[("active", colors["bg"])], foreground=[("disabled", colors["muted"])])
        self.style.configure("Panel.TCheckbutton", background=colors["surface"], foreground=colors["text"])
        self.style.map("Panel.TCheckbutton", background=[("active", colors["surface"])])
        self.style.configure("Console.TCheckbutton", background=colors["console"], foreground=colors["text"])
        self.style.map("Console.TCheckbutton", background=[("active", colors["console"])])
        self.style.configure("TEntry", fieldbackground=colors["field"], foreground=colors["text"], bordercolor=colors["border"], insertcolor=colors["text"])
        self.style.configure("TCombobox", fieldbackground=colors["field"], background=colors["surface"], foreground=colors["text"], arrowcolor=colors["text"], bordercolor=colors["border"])
        self.style.map("TCombobox", fieldbackground=[("readonly", colors["field"])], foreground=[("readonly", colors["text"])])
        self.style.configure("Treeview", background=colors["surface"], fieldbackground=colors["surface"], foreground=colors["text"], bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], relief="flat", rowheight=42, font=("Microsoft JhengHei UI", 10))
        self.style.map("Treeview", background=[("selected", colors["select"])], foreground=[("selected", colors["select_text"])])
        self.style.configure("Treeview.Heading", background=colors["surface_alt"], foreground=colors["muted"], relief="flat", padding=(8, 7), font=("Microsoft JhengHei UI", 9, "bold"))
        self.style.map("Treeview.Heading", background=[("active", colors["surface_alt"])])
        self.style.configure("TNotebook", background=colors["bg"], bordercolor=colors["border"])
        self.style.configure("TNotebook.Tab", background=colors["border"], foreground=colors["text"], padding=(14, 7))
        self.style.map("TNotebook.Tab", background=[("selected", colors["surface"])], foreground=[("selected", colors["accent"])])
        self.log.configure(bg="#222327" if dark else "#ffffff", fg="#adb3c2" if dark else "#263244", insertbackground=colors["text"], selectbackground=colors["select"])
        self.preview.configure(bg=colors["surface"], highlightbackground=colors["border"])
        self.preview.itemconfigure("preview_text", fill=colors["muted"])
        self.tree.tag_configure("enabled", foreground=colors["text"])
        self.tree.tag_configure("paused", foreground=colors["muted"])
        self.theme_btn.configure(text="切換亮色" if dark else "切換暗色")

    def toggle_theme(self) -> None:
        self.theme = "dark" if self.theme == "light" else "light"
        GUI_CONFIG.write_text(json.dumps({"theme": self.theme}, ensure_ascii=False, indent=2), encoding="utf-8")
        self.apply_theme()

    def _build_ui(self) -> None:
        self.enabled_var = tk.BooleanVar(value=True)
        self.quality_var = tk.StringVar(value="1080P")
        self.url_var = tk.StringVar()
        self.name_var = tk.StringVar()
        columns = ("enabled", "quality", "url", "name", "control")
        self.output_var = tk.StringVar()
        self.format_var = tk.StringVar(value="ts")
        self.interval_var = tk.StringVar(value="300")
        self.fps_var = tk.StringVar(value="自動")
        self.proxy_enabled_var = tk.BooleanVar()
        self.proxy_var = tk.StringVar()
        self.soop_cookie_var = tk.StringVar()
        self.soop_username_var = tk.StringVar()
        self.soop_password_var = tk.StringVar()

        self.workspace = ttk.Panedwindow(self, orient="horizontal", style="App.TPanedwindow")
        self.workspace.pack(fill="both", expand=True)
        sidebar = ttk.Frame(self.workspace, padding=16, width=280, style="Panel.TFrame")
        details = ttk.Frame(self.workspace, padding=20, width=320, style="Panel.TFrame")
        console = ttk.Frame(self.workspace, padding=20, style="Console.TFrame")
        self.workspace.add(sidebar, weight=0)
        self.workspace.add(details, weight=0)
        self.workspace.add(console, weight=1)

        ttk.Label(sidebar, text="LIVE RECORDER", style="Title.TLabel").pack(anchor="w")
        self.status_var = tk.StringVar(value="● 尚未啟動")
        ttk.Label(sidebar, textvariable=self.status_var, style="Sub.TLabel").pack(anchor="w", pady=(4, 18))
        top_actions = ttk.Frame(sidebar, style="Panel.TFrame")
        top_actions.pack(fill="x", pady=(0, 16))
        ttk.Button(top_actions, text="設定", command=self.show_settings_dialog).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(top_actions, text="新增直播間", style="Accent.TButton", command=self.show_room_dialog).pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.tree = ttk.Treeview(
            sidebar, columns=columns, displaycolumns=("control",),
            show="tree headings", selectmode="browse",
        )
        self.tree.heading("#0", text="直播間", anchor="w")
        self.tree.heading("control", text="操作", anchor="center")
        self.tree.column("#0", width=180, minwidth=135, stretch=True)
        for col in columns:
            self.tree.column(col, width=0, stretch=False)
        self.tree.column("control", width=66, minwidth=66, stretch=False, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select_room)
        self.tree.bind("<ButtonRelease-1>", self._room_list_click)
        self.tree.bind("<space>", lambda _event: self.toggle_room())
        self.tree.bind("<Return>", lambda _event: self.toggle_room())
        side_footer = ttk.Frame(sidebar, style="Panel.TFrame")
        side_footer.pack(fill="x", pady=(16, 0))
        footer_text = ttk.Frame(side_footer, style="Panel.TFrame")
        footer_text.pack(side="left")
        ttk.Label(footer_text, text="GUI v0.3", style="Sub.TLabel").pack(anchor="w")
        ttk.Label(footer_text, text="Ctrl+N 新增 · Space 切換", style="PanelMeta.TLabel").pack(anchor="w", pady=(2, 0))
        self.theme_btn = ttk.Button(side_footer, text="切換暗色", width=10, command=self.toggle_theme)
        self.theme_btn.pack(side="right")

        self.preview = tk.Canvas(details, width=280, height=204, highlightthickness=1)
        self.preview.pack(fill="x", pady=(0, 20))
        self.preview.create_text(175, 102, text="選擇直播間以載入預覽", justify="center", font=("Microsoft JhengHei UI", 11), fill="#7c8798", tags="preview_text")
        self.detail_name = tk.StringVar(value="請選擇直播間")
        self.detail_state = tk.StringVar(value="—")
        self.detail_url = tk.StringVar(value="—")
        self.detail_quality = tk.StringVar(value="—")
        detail_header = ttk.Frame(details, style="Panel.TFrame")
        detail_header.pack(fill="x")
        ttk.Label(detail_header, textvariable=self.detail_name, style="Panel.TLabel", font=("Microsoft JhengHei UI", 16, "bold"), wraplength=210).pack(side="left", anchor="w")
        self.detail_state_label = ttk.Label(detail_header, textvariable=self.detail_state, style="PausedBadge.TLabel")
        self.detail_state_label.pack(side="right", anchor="e")
        ttk.Label(details, text="直播間資訊與個別錄製控制", style="PanelSub.TLabel").pack(anchor="w", pady=(5, 16))
        ttk.Separator(details).pack(fill="x", pady=(0, 16))
        ttk.Label(details, text="直播間網址", style="PanelSub.TLabel").pack(anchor="w")
        ttk.Label(details, textvariable=self.detail_url, wraplength=280, style="Panel.TLabel").pack(anchor="w", pady=(5, 18))
        ttk.Label(details, text="錄製畫質", style="PanelSub.TLabel").pack(anchor="w")
        ttk.Label(details, textvariable=self.detail_quality, style="Panel.TLabel").pack(anchor="w", pady=(4, 16))
        ttk.Label(details, text="儲存格式", style="PanelSub.TLabel").pack(anchor="w")
        ttk.Label(details, textvariable=self.format_var, style="Panel.TLabel").pack(anchor="w", pady=(4, 22))
        detail_actions = ttk.Frame(details, style="Panel.TFrame")
        detail_actions.pack(fill="x", pady=(4, 0))
        self.toggle_btn = ttk.Button(detail_actions, text="開始錄製", style="Accent.TButton", command=self.toggle_room)
        self.toggle_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(detail_actions, text="編輯", command=lambda: self.show_room_dialog(edit=True)).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(detail_actions, text="刪除", style="Danger.TButton", command=self.delete_room).pack(side="left", fill="x", expand=True, padx=(5, 0))

        console_header = ttk.Frame(console, style="Console.TFrame")
        console_header.pack(fill="x", pady=(0, 12))
        title_block = ttk.Frame(console_header, style="Console.TFrame")
        title_block.pack(anchor="w")
        ttk.Label(title_block, text="執行日誌", style="Console.TLabel", font=("Microsoft JhengHei UI", 13, "bold")).pack(anchor="w")
        ttk.Label(title_block, text="錄製核心的即時輸出", style="ConsoleSub.TLabel").pack(anchor="w")
        header_actions = ttk.Frame(console_header, style="Console.TFrame")
        header_actions.pack(anchor="w", pady=(10, 0))
        self.core_status_var = tk.StringVar(value="未啟動")
        ttk.Label(header_actions, textvariable=self.core_status_var, style="CoreBadge.TLabel").pack(side="left", padx=(0, 12))
        ttk.Button(header_actions, text="錄影資料夾", command=self.open_downloads).pack(side="left")
        self.log = tk.Text(console, width=42, wrap="word", bg="#111827", fg="#d1d5db", insertbackground="white", font=("Consolas", 10), relief="flat", padx=12, pady=12)
        self.log.pack(fill="both", expand=True)
        log_footer = ttk.Frame(console, style="Console.TFrame")
        log_footer.pack(fill="x", pady=(8, 0))
        self.autoscroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(log_footer, text="自動捲動日誌", variable=self.autoscroll_var, style="Console.TCheckbutton").pack(side="left")
        ttk.Label(log_footer, text="F2 編輯 · Delete 刪除", style="ConsoleSub.TLabel").pack(side="left", padx=(18, 0))
        ttk.Button(log_footer, text="清除", command=lambda: self.log.delete("1.0", "end")).pack(side="right")

    def show_room_dialog(self, edit: bool = False) -> None:
        if edit and not self.tree.selection():
            messagebox.showinfo("尚未選取", "請先選擇一個直播間。")
            return
        if not edit:
            self.enabled_var.set(True)
            self.quality_var.set("1080P")
            self.url_var.set("")
            self.name_var.set("")
            self.tree.selection_remove(*self.tree.selection())
        dialog = tk.Toplevel(self)
        dialog.title("編輯直播間" if edit else "新增直播間")
        self._prepare_dialog(dialog, 560, 340)
        body = ttk.Frame(dialog, padding=22)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        ttk.Label(body, text="直播間網址").grid(row=0, column=0, sticky="w", pady=8)
        ttk.Entry(body, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", pady=8)
        ttk.Label(body, text="主播名稱").grid(row=1, column=0, sticky="w", pady=8)
        ttk.Entry(body, textvariable=self.name_var).grid(row=1, column=1, sticky="ew", pady=8)
        ttk.Label(body, text="畫質").grid(row=2, column=0, sticky="w", pady=8)
        ttk.Combobox(body, textvariable=self.quality_var, values=QUALITIES, state="readonly").grid(row=2, column=1, sticky="ew", pady=8)
        ttk.Checkbutton(body, text="啟用監看與錄製", variable=self.enabled_var).grid(row=3, column=1, sticky="w", pady=8)
        actions = ttk.Frame(body)
        actions.grid(row=4, column=0, columnspan=2, sticky="e", pady=(18, 0))
        ttk.Button(actions, text="取消", command=dialog.destroy).pack(side="left", padx=(0, 8))

        def save_room() -> None:
            if self.upsert_room():
                dialog.destroy()

        ttk.Button(actions, text="儲存直播間", style="Accent.TButton", command=save_room).pack(side="left")
        dialog.bind("<Return>", lambda _event: save_room())

    def show_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("錄製設定")
        self._prepare_dialog(dialog, 720, 640)
        body = ttk.Frame(dialog, padding=22)
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        rows = [
            ("儲存路徑", ttk.Entry(body, textvariable=self.output_var)),
            ("影片格式", ttk.Combobox(body, textvariable=self.format_var, values=("ts", "mkv", "flv", "mp4", "mp3音頻", "m4a音頻"), state="readonly")),
            ("檢查間隔（秒）", ttk.Entry(body, textvariable=self.interval_var)),
            ("代理地址", ttk.Entry(body, textvariable=self.proxy_var)),
            ("偏好 FPS", ttk.Combobox(body, textvariable=self.fps_var, values=("自動", "30", "60"), state="readonly")),
        ]
        for row, (label, widget) in enumerate(rows):
            ttk.Label(body, text=label).grid(row=row, column=0, sticky="w", padx=(0, 14), pady=9)
            widget.grid(row=row, column=1, sticky="ew", pady=9)
            if row == 0:
                ttk.Button(body, text="瀏覽…", command=self.choose_output).grid(row=0, column=2, padx=(8, 0))
        ttk.Checkbutton(body, text="啟用代理", variable=self.proxy_enabled_var).grid(row=5, column=1, sticky="w", pady=8)
        ttk.Separator(body).grid(row=6, column=0, columnspan=3, sticky="ew", pady=14)
        ttk.Label(body, text="SOOP 登入（19+ 直播需要）", font=("Microsoft JhengHei UI", 11, "bold")).grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(body, text="SOOP Cookie").grid(row=8, column=0, sticky="nw", padx=(0, 14), pady=8)
        cookie_text = scrolledtext.ScrolledText(body, height=4, wrap="word", font=("Consolas", 9), undo=True)
        cookie_text.grid(row=8, column=1, columnspan=2, sticky="nsew", pady=8)
        cookie_text.insert("1.0", self.soop_cookie_var.get())
        ttk.Label(body, text="SOOP 帳號").grid(row=9, column=0, sticky="w", padx=(0, 14), pady=8)
        ttk.Entry(body, textvariable=self.soop_username_var).grid(row=9, column=1, columnspan=2, sticky="ew", pady=8)
        ttk.Label(body, text="SOOP 密碼").grid(row=10, column=0, sticky="w", padx=(0, 14), pady=8)
        password_entry = ttk.Entry(body, textvariable=self.soop_password_var, show="●")
        password_entry.grid(row=10, column=1, sticky="ew", pady=8)
        show_password = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            body, text="顯示", variable=show_password,
            command=lambda: password_entry.configure(show="" if show_password.get() else "●"),
        ).grid(row=10, column=2, sticky="w", padx=(8, 0))
        ttk.Label(body, text="FPS 僅選擇平台原生串流，不會重複畫格。", style="Sub.TLabel").grid(row=11, column=1, columnspan=2, sticky="w", pady=8)
        def save_and_close() -> None:
            self.soop_cookie_var.set(cookie_text.get("1.0", "end-1c"))
            if self.save_settings():
                dialog.destroy()

        actions = ttk.Frame(body)
        actions.grid(row=12, column=1, columnspan=2, sticky="e", pady=(14, 0))
        ttk.Button(actions, text="取消", command=dialog.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="儲存設定", style="Accent.TButton", command=save_and_close).pack(side="left")

    def load_rooms(self) -> None:
        selected_url = ""
        selection = self.tree.selection()
        if selection:
            values = self.tree.item(selection[0], "values")
            if len(values) >= 3:
                selected_url = values[2]
        self.tree.delete(*self.tree.get_children())
        URL_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        selected_item = None
        for raw in read_text(URL_CONFIG).splitlines():
            line = raw.strip()
            if not line:
                continue
            enabled = not line.startswith("#")
            line = line.lstrip("#").strip()
            parts = [part.strip() for part in re.split("[,，]", line, maxsplit=2)]
            if len(parts) == 1:
                quality, url, name = "1080P", parts[0], ""
            elif parts[0] in QUALITIES:
                quality, url = parts[:2]
                name = parts[2] if len(parts) > 2 else ""
            elif parts[0] in LEGACY_QUALITY:
                quality, url = LEGACY_QUALITY[parts[0]], parts[1]
                name = parts[2] if len(parts) > 2 else ""
            else:
                quality, url, name = "1080P", parts[0], parts[1]
            name = TO_TRADITIONAL.convert(name)
            display_name = name or url.split("/")[-1] or url
            marker = "●" if enabled else "○"
            state = "啟用" if enabled else "暫停"
            control = "停止" if enabled else "開始"
            item = self.tree.insert(
                "", "end", text=f"  {marker}   {display_name}",
                values=(state, quality, url, name, control),
                tags=("enabled" if enabled else "paused",),
            )
            if url == selected_url:
                selected_item = item
        self._update_status()
        children = self.tree.get_children()
        if children:
            selected_item = selected_item or children[0]
            self.tree.selection_set(selected_item)
            self.tree.focus(selected_item)
            self.tree.see(selected_item)
            self.select_room()

    def save_rooms(self) -> None:
        lines = []
        for item in self.tree.get_children():
            enabled, quality, url, name = self.tree.item(item, "values")[:4]
            prefix = "" if enabled == "啟用" else "#"
            lines.append(f"{prefix}{quality},{url}" + (f",{name}" if name else ""))
        URL_CONFIG.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def upsert_room(self) -> bool:
        url = self.url_var.get().strip()
        if not url or "://" not in url:
            messagebox.showwarning("網址不完整", "請輸入包含 http:// 或 https:// 的直播間網址。")
            return False
        state = "啟用" if self.enabled_var.get() else "暫停"
        values = (state, self.quality_var.get(), url, self.name_var.get().strip(), "停止" if state == "啟用" else "開始")
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            self.tree.item(item, values=values)
            marker = "●" if values[0] == "啟用" else "○"
            self.tree.item(
                item, text=f"  {marker}   {values[3] or url.split('/')[-1] or url}",
                tags=("enabled" if values[0] == "啟用" else "paused",),
            )
        else:
            marker = "●" if values[0] == "啟用" else "○"
            item = self.tree.insert(
                "", "end", text=f"  {marker}   {values[3] or url.split('/')[-1] or url}",
                values=values, tags=("enabled" if values[0] == "啟用" else "paused",),
            )
        self.save_rooms()
        self._update_status()
        self.url_var.set("")
        self.name_var.set("")
        self.tree.selection_set(item)
        self.tree.focus(item)
        self.tree.see(item)
        self.select_room()
        return True

    def select_room(self, _event=None) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        enabled, quality, url, name = self.tree.item(selected[0], "values")[:4]
        self.enabled_var.set(enabled == "啟用")
        self.quality_var.set(quality)
        self.url_var.set(url)
        self.name_var.set(name)
        self.detail_name.set(name or url.split("/")[-1] or "未命名直播間")
        self.detail_state.set("已啟用" if enabled == "啟用" else "已暫停")
        self.detail_state_label.configure(style="LiveBadge.TLabel" if enabled == "啟用" else "PausedBadge.TLabel")
        self.detail_url.set(url)
        self.detail_quality.set(quality)
        self.toggle_btn.configure(
            text="停止錄製" if enabled == "啟用" else "開始錄製",
            style="Danger.TButton" if enabled == "啟用" else "Accent.TButton",
        )
        self.load_live_preview(url)

    def _room_list_click(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item and self.tree.identify_column(event.x) == "#1":
            self.tree.selection_set(item)
            self.toggle_room()

    def _enabled_room_count(self) -> int:
        return sum(self.tree.item(item, "values")[0] == "啟用" for item in self.tree.get_children())

    def _update_status(self) -> None:
        count = self._enabled_room_count()
        total = len(self.tree.get_children())
        self.status_var.set(f"已啟用 {count}／{total} 個直播間" if total else "尚未新增直播間")

    def _auto_start_enabled_rooms(self) -> None:
        if self._enabled_room_count() and (not self.process or self.process.poll() is not None):
            self.start_recording()

    def load_live_preview(self, url: str) -> None:
        """Load a SOOP live thumbnail without blocking Tk's event loop."""
        self.preview_request_id += 1
        request_id = self.preview_request_id
        self.preview.delete("preview_image")
        self.preview.itemconfigure("preview_text", text="正在載入直播預覽…")
        match = re.search(r"play\.sooplive\.(?:com|co\.kr)/[^/]+/(\d+)", url)
        if not match:
            self.preview.itemconfigure("preview_text", text="此平台暫不支援縮圖預覽")
            return
        thumbnail_url = f"https://liveimg.sooplive.com/m/{match.group(1)}?t={int(time.time())}"

        def fetch() -> None:
            try:
                request = urllib.request.Request(thumbnail_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(request, timeout=12) as response:
                    data = response.read()
                image = Image.open(io.BytesIO(data)).convert("RGB")
                self.preview_queue.put(("ok", request_id, image))
            except Exception as exc:
                self.preview_queue.put(("error", request_id, str(exc)))

        threading.Thread(target=fetch, daemon=True).start()

    def _show_live_preview(self, request_id: int, image: Image.Image) -> None:
        if request_id != self.preview_request_id:
            return
        width = max(self.preview.winfo_width() - 4, 320)
        height = max(self.preview.winfo_height() - 4, 176)
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.preview.itemconfigure("preview_text", text="")
        self.preview.create_image(width // 2, height // 2, image=self.preview_photo, anchor="center", tags="preview_image")
        self.after(30000, lambda: self.load_live_preview(self.detail_url.get()) if request_id == self.preview_request_id else None)

    def _preview_failed(self, request_id: int, error: str) -> None:
        if request_id != self.preview_request_id:
            return
        label = "目前沒有可用預覽" if "404" in error else "預覽載入失敗，稍後再試"
        self.preview.itemconfigure("preview_text", text=label)

    def toggle_room(self) -> None:
        selected = self.tree.selection()
        if selected:
            values = list(self.tree.item(selected[0], "values")[:4])
            values[0] = "暫停" if values[0] == "啟用" else "啟用"
            values.append("停止" if values[0] == "啟用" else "開始")
            self.tree.item(selected[0], values=values)
            marker = "●" if values[0] == "啟用" else "○"
            self.tree.item(
                selected[0],
                text=f"  {marker}   {values[3] or values[2].split('/')[-1] or values[2]}",
                tags=("enabled" if values[0] == "啟用" else "paused",),
            )
            self.save_rooms()
            self.select_room()
            self._update_status()
            if values[0] == "啟用" and (not self.process or self.process.poll() is not None):
                self.start_recording()
            elif values[0] == "暫停" and self._enabled_room_count() == 0:
                self.stop_recording()

    def delete_room(self) -> None:
        selected = self.tree.selection()
        if selected and messagebox.askyesno("刪除直播間", "確定要刪除選取的直播間嗎？"):
            self.tree.delete(selected[0])
            self.save_rooms()
            self._update_status()
            if self._enabled_room_count() == 0:
                self.stop_recording()
            self.detail_name.set("請選擇直播間")
            self.detail_state.set("—")
            self.detail_state_label.configure(style="PausedBadge.TLabel")
            self.detail_url.set("—")
            self.detail_quality.set("—")
            self.preview.delete("preview_image")
            self.preview.itemconfigure("preview_text", text="選擇直播間以載入預覽")

    def load_settings(self) -> None:
        self.output_var.set(get_ini_value(APP_CONFIG, "錄制設置", "直播保存路徑(不填則默認)", ""))
        # Upstream currently uses simplified Chinese section/key names.
        self.output_var.set(get_ini_value(APP_CONFIG, "录制设置", "直播保存路径(不填则默认)", self.output_var.get()))
        self.format_var.set(get_ini_value(APP_CONFIG, "录制设置", "视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频", "ts"))
        self.interval_var.set(get_ini_value(APP_CONFIG, "录制设置", "循环时间(秒)", "300"))
        self.fps_var.set(get_ini_value(APP_CONFIG, "录制设置", "偏好帧率(自动|30|60)", "自动").replace("自动", "自動"))
        self.proxy_enabled_var.set(get_ini_value(APP_CONFIG, "录制设置", "是否使用代理ip(是/否)", "否") == "是")
        self.proxy_var.set(get_ini_value(APP_CONFIG, "录制设置", "代理地址", ""))
        self.soop_cookie_var.set(get_ini_value(APP_CONFIG, "Cookie", "sooplive_cookie", ""))
        self.soop_username_var.set(get_ini_value(APP_CONFIG, "账号密码", "sooplive账号", ""))
        self.soop_password_var.set(get_ini_value(APP_CONFIG, "账号密码", "sooplive密码", ""))

    def save_settings(self) -> bool:
        try:
            interval = int(self.interval_var.get())
            if interval < 10:
                raise ValueError
            set_ini_value(APP_CONFIG, "录制设置", "直播保存路径(不填则默认)", self.output_var.get().strip())
            set_ini_value(APP_CONFIG, "录制设置", "视频保存格式ts|mkv|flv|mp4|mp3音频|m4a音频", self.format_var.get())
            set_ini_value(APP_CONFIG, "录制设置", "循环时间(秒)", str(interval))
            set_ini_value(APP_CONFIG, "录制设置", "偏好帧率(自动|30|60)", self.fps_var.get().replace("自動", "自动"))
            set_ini_value(APP_CONFIG, "录制设置", "是否使用代理ip(是/否)", "是" if self.proxy_enabled_var.get() else "否")
            set_ini_value(APP_CONFIG, "录制设置", "代理地址", self.proxy_var.get().strip())
            set_ini_value(APP_CONFIG, "Cookie", "sooplive_cookie", self.soop_cookie_var.get().strip())
            set_ini_value(APP_CONFIG, "账号密码", "sooplive账号", self.soop_username_var.get().strip())
            set_ini_value(APP_CONFIG, "账号密码", "sooplive密码", self.soop_password_var.get())
            messagebox.showinfo("已儲存", "錄製設定已更新。")
            return True
        except ValueError:
            messagebox.showwarning("設定錯誤", "檢查間隔請輸入不小於 10 的整數。")
        except Exception as exc:
            messagebox.showerror("無法儲存", str(exc))
        return False

    def choose_output(self) -> None:
        path = filedialog.askdirectory(initialdir=self.output_var.get() or str(CORE))
        if path:
            self.output_var.set(path)

    def start_recording(self) -> None:
        if self.process and self.process.poll() is None:
            return
        # The recorder core may rewrite URL_config.ini while it runs. Refresh
        # before validating so the GUI cannot start with stale room states.
        self.load_rooms()
        if not any(self.tree.item(item, "values")[0] == "啟用" for item in self.tree.get_children()):
            messagebox.showwarning("所有直播間都已停止", "請在左側選擇直播間，按「開始」後再錄製。")
            return
        self.save_rooms()
        flags = 0
        if os.name == "nt":
            flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        command, core_cwd = core_command()
        child_env = os.environ.copy()
        child_env["PYTHONUTF8"] = "1"
        child_env["PYTHONIOENCODING"] = "utf-8"
        try:
            self.process = subprocess.Popen(
                command, cwd=core_cwd, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
                creationflags=flags, env=child_env,
            )
        except Exception as exc:
            messagebox.showerror("啟動失敗", f"無法啟動錄製核心：\n{exc}")
            return
        self._update_status()
        self.core_status_var.set("執行中")
        self.output_queue.put("\n=== 錄製核心已啟動 ===\n")
        threading.Thread(target=self._read_output, daemon=True).start()

    def _read_output(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            self.output_queue.put(line)
        code = self.process.wait()
        self.output_queue.put(f"\n=== 錄製核心已結束（代碼 {code}）===\n")
        self.after(0, self._process_finished)

    def _drain_output(self) -> None:
        try:
            while True:
                text = self.output_queue.get_nowait()
                text = re.sub(r"\x1b\[[0-9;]*m", "", text)
                text = TO_TRADITIONAL.convert(text)
                self.log.insert("end", text)
                if self.autoscroll_var.get():
                    self.log.see("end")
        except queue.Empty:
            pass
        try:
            while True:
                status, request_id, payload = self.preview_queue.get_nowait()
                if status == "ok":
                    self._show_live_preview(request_id, payload)  # type: ignore[arg-type]
                else:
                    self._preview_failed(request_id, str(payload))
        except queue.Empty:
            pass
        self.after(100, self._drain_output)

    def _process_finished(self) -> None:
        self._update_status()
        self.core_status_var.set("未啟動")

    def stop_recording(self) -> None:
        if not self.process or self.process.poll() is not None:
            return
        self.status_var.set("● 正在停止…")
        self.core_status_var.set("停止中")
        try:
            if os.name == "nt":
                self.process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                self.process.send_signal(signal.SIGINT)
        except Exception:
            self.process.terminate()
        # CTRL_BREAK may not reach a hidden Windows child process. Give the
        # recorder a short grace period, then clean up the complete process tree.
        self.after(4000, self._force_stop_if_running)

    def _force_stop_if_running(self) -> None:
        if not self.process or self.process.poll() is not None:
            return
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        else:
            self.process.kill()

    def open_downloads(self) -> None:
        configured = self.output_var.get().strip()
        target = Path(configured) if configured else DOWNLOAD_ROOT
        target.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(target)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(target)])

    def on_close(self) -> None:
        if self.process and self.process.poll() is None:
            if not messagebox.askyesno("仍在錄製", "錄製仍在執行，確定要停止並離開嗎？"):
                return
            # The Tk event loop is about to end, so a delayed cleanup would
            # never run. Terminate the owned process tree immediately.
            if os.name == "nt":
                subprocess.run(
                    ["taskkill", "/PID", str(self.process.pid), "/T", "/F"],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            else:
                self.process.terminate()
        self.destroy()


if __name__ == "__main__":
    if not (CORE / "main.py").exists():
        raise SystemExit("找不到 recorder-core/main.py")
    RecorderGUI().mainloop()
