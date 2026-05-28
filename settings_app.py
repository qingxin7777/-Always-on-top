"""独立的设置窗口进程。由主进程通过 subprocess 启动。"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import winreg

from config import Config
from plugin_system import PluginManager


# ── 配色 ──────────────────────────────────────────────
MAC_BG       = "#f5f5f7"   # macOS 窗口底色
MAC_WHITE    = "#ffffff"
MAC_BLUE     = "#007aff"   # macOS 强调蓝
MAC_BLUE_LO  = "#409cff"   # hover
MAC_TEXT      = "#1d1d1f"   # 主文字
MAC_SUBTEXT   = "#86868b"   # 次要文字
MAC_SEP       = "#e5e5ea"   # 分割线
MAC_RED       = "#ff3b30"


class SettingsWindowProcess:

    def __init__(self, config_path, plugin_dir):
        self.config = Config(config_path)
        self.plugin_manager = PluginManager(plugin_dir)
        self.plugin_manager.discover_plugins()

        self.root = tk.Tk()
        self.root.title("Always-On-Top 设置")
        self.root.resizable(False, False)
        self.root.configure(bg=MAC_BG)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self._hotkey_entries = {}
        self._plugin_entries = {}
        self._row_frames = {}     # action_key → row frame (for recording lookup)
        self._record_target = None
        self._record_buttons = []

        self._setup_styles()
        self._build_ui()
        self._populate_from_config()
        self._center_window(540, 400)

    # ── 样式 ──────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")

        FONT = ("Microsoft YaHei UI", 9)
        FONT_BOLD = ("Microsoft YaHei UI", 9, "bold")
        FONT_TITLE = ("Microsoft YaHei UI", 14, "bold")
        FONT_SECTION = ("Microsoft YaHei UI", 10, "bold")
        FONT_CAPTION = ("Microsoft YaHei UI", 8)

        style.configure(".", font=FONT, background=MAC_BG)

        # 主按钮 (蓝底白字)
        style.configure("Primary.TButton", font=FONT_BOLD,
                        background=MAC_BLUE, foreground="white",
                        borderwidth=0, padding=(24, 8),
                        relief="flat")
        style.map("Primary.TButton",
                  background=[("active", MAC_BLUE_LO), ("pressed", MAC_BLUE)])

        # 次按钮
        style.configure("Secondary.TButton", font=FONT,
                        background=MAC_WHITE, foreground=MAC_TEXT,
                        borderwidth=0, padding=(24, 8),
                        relief="flat")
        style.map("Secondary.TButton",
                  background=[("active", "#e8e8ed"), ("pressed", "#dcdce0")])

        # 录制小按钮
        style.configure("Record.TButton", font=FONT,
                        background=MAC_WHITE, foreground=MAC_BLUE,
                        borderwidth=1, padding=(10, 4),
                        relief="solid", bordercolor=MAC_SEP)
        style.map("Record.TButton",
                  background=[("active", "#e8f2fd"), ("pressed", "#d0e4fc")])

        # Label
        style.configure("TLabel", font=FONT, background=MAC_BG, foreground=MAC_TEXT)
        style.configure("Section.TLabel", font=FONT_SECTION, background=MAC_BG,
                        foreground=MAC_TEXT)
        style.configure("Caption.TLabel", font=FONT_CAPTION, background=MAC_BG,
                        foreground=MAC_SUBTEXT)
        style.configure("Title.TLabel", font=FONT_TITLE, background=MAC_BG,
                        foreground=MAC_TEXT)

        # Checkbutton
        style.configure("Switch.TCheckbutton", font=FONT,
                        background=MAC_BG, foreground=MAC_TEXT)

        # Entry
        self.root.option_add("*Entry.font", FONT)
        self.root.option_add("*Entry.relief", "flat")
        self.root.option_add("*Entry.borderWidth", 0)
        self.root.option_add("*Entry.highlightthickness", 0)

    def run(self):
        self.root.mainloop()

    def _center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI 构建 ───────────────────────────────────────
    def _build_ui(self):
        # 内容容器（统一内边距）
        content = tk.Frame(self.root, bg=MAC_BG)
        content.pack(fill="both", expand=True, padx=24, pady=(20, 16))

        # 标题
        ttk.Label(content, text="Always-On-Top", style="Title.TLabel").pack(
            anchor="w")
        ttk.Label(content, text="窗口置顶工具 · 快捷键设置",
                  style="Caption.TLabel").pack(anchor="w", pady=(2, 18))

        # ── 节：快捷键 ──
        ttk.Label(content, text="快捷键", style="Section.TLabel").pack(anchor="w")

        sep1 = tk.Frame(content, bg=MAC_SEP, height=1)
        sep1.pack(fill="x", pady=(6, 10))

        self._build_key_row(content, "切换窗口置顶", "toggle_always_on_top")

        # 提示
        ttk.Label(content, text="按下快捷键后，切换当前激活窗口的置顶 / 取消置顶状态。",
                  style="Caption.TLabel").pack(anchor="w", pady=(6, 20))

        # ── 节：启动 ──
        ttk.Label(content, text="启动", style="Section.TLabel").pack(anchor="w")

        sep2 = tk.Frame(content, bg=MAC_SEP, height=1)
        sep2.pack(fill="x", pady=(6, 10))

        self.autostart_var = tk.BooleanVar()
        auto_frame = tk.Frame(content, bg=MAC_BG)
        auto_frame.pack(fill="x")
        cb = ttk.Checkbutton(auto_frame, text="开机时自动启动",
                             variable=self.autostart_var,
                             style="Switch.TCheckbutton")
        cb.pack(side="left")
        ttk.Label(auto_frame, text="（写入注册表 Run 键）",
                  style="Caption.TLabel").pack(side="left", padx=8)

        # ── 节：插件（如果有）──
        plugins = self.plugin_manager.loaded_plugins
        if plugins:
            ttk.Label(content, text="插件", style="Section.TLabel").pack(
                anchor="w", pady=(20, 0))
            sep3 = tk.Frame(content, bg=MAC_SEP, height=1)
            sep3.pack(fill="x", pady=(6, 10))
            self._build_plugin_rows(content, plugins)

        # ── 底部按钮 ──
        btn_bar = tk.Frame(self.root, bg=MAC_WHITE, height=48)
        btn_bar.pack(fill="x", side="bottom")
        btn_bar.pack_propagate(False)

        # 分割线
        tk.Frame(self.root, bg=MAC_SEP, height=1).pack(fill="x", side="bottom")

        ttk.Button(btn_bar, text="取消", style="Secondary.TButton",
                   command=self._on_close).pack(side="right", padx=(0, 12),
                                                pady=8)
        ttk.Button(btn_bar, text="保存", style="Primary.TButton",
                   command=self._on_save).pack(side="right", padx=4, pady=8)

    def _build_key_row(self, parent, label_text, action_key, label_width=14):
        """Mac 风格的快捷键行：标签 + 输入框 + 录制按钮"""
        row = tk.Frame(parent, bg=MAC_BG)
        row.pack(fill="x", pady=3)

        ttk.Label(row, text=label_text, width=label_width, anchor="w").pack(
            side="left", padx=(0, 12))

        entry_frame = tk.Frame(row, bg=MAC_WHITE, highlightbackground=MAC_SEP,
                               highlightthickness=1)
        entry_frame.pack(side="left")

        entry = tk.Entry(entry_frame, width=22, bg=MAC_WHITE, fg=MAC_TEXT,
                         insertbackground=MAC_BLUE, relief="flat",
                         highlightthickness=0, bd=0,
                         insertwidth=1, insertofftime=300, insertontime=600)
        entry.pack(padx=10, pady=5, ipady=2)

        btn = ttk.Button(row, text="录制", style="Record.TButton",
                         command=lambda e=entry, r=row: self._start_recording(e, r))
        btn.pack(side="left", padx=8)

        self._hotkey_entries[action_key] = entry
        self._row_frames[action_key] = row

    def _build_plugin_rows(self, parent, plugins, label_width=14):
        for plugin_module in plugins:
            name = plugin_module.PLUGIN_NAME
            plugin_id = f"plugin_{name}"

            row = tk.Frame(parent, bg=MAC_BG)
            row.pack(fill="x", pady=3)

            ttk.Label(row, text=name, width=label_width, anchor="w").pack(
                side="left", padx=(0, 12))

            entry_frame = tk.Frame(row, bg=MAC_WHITE,
                                   highlightbackground=MAC_SEP,
                                   highlightthickness=1)
            entry_frame.pack(side="left")

            entry = tk.Entry(entry_frame, width=22, bg=MAC_WHITE, fg=MAC_TEXT,
                             insertbackground=MAC_BLUE, relief="flat",
                             highlightthickness=0, bd=0,
                             insertwidth=1, insertofftime=300, insertontime=600)
            entry.pack(padx=10, pady=5, ipady=2)

            btn = ttk.Button(row, text="录制", style="Record.TButton",
                             command=lambda e=entry, r=row: self._start_recording(e, r))
            btn.pack(side="left", padx=8)

            self._plugin_entries[plugin_id] = entry

    # ── 数据填充 ──────────────────────────────────────
    def _populate_from_config(self):
        hotkey = self.config.get_hotkey("toggle_always_on_top")
        if "toggle_always_on_top" in self._hotkey_entries:
            self._hotkey_entries["toggle_always_on_top"].delete(0, tk.END)
            self._hotkey_entries["toggle_always_on_top"].insert(0, hotkey)
        self.autostart_var.set(self.config.is_autostart_enabled())
        for plugin_module in self.plugin_manager.loaded_plugins:
            name = plugin_module.PLUGIN_NAME
            plugin_id = f"plugin_{name}"
            if plugin_id in self._plugin_entries:
                hotkey = self.config.get_plugin_hotkey(
                    name, getattr(plugin_module, "PLUGIN_HOTKEY", None))
                self._plugin_entries[plugin_id].delete(0, tk.END)
                if hotkey:
                    self._plugin_entries[plugin_id].insert(0, hotkey)

    # ── 快捷键录制 ────────────────────────────────────
    def _start_recording(self, target_entry, row_frame):
        # 禁用该行的录制按钮
        for child in row_frame.pack_slaves():
            if isinstance(child, ttk.Button):
                child.config(text="按键中...", state="disabled")
                self._record_buttons.append(child)

        self._record_target = target_entry
        self._do_record()

    def _reset_record_buttons(self):
        for btn in getattr(self, "_record_buttons", []):
            try:
                btn.config(text="录制", state="normal")
            except Exception:
                pass
        self._record_target = None
        self._record_buttons = []

    def _do_record(self):
        from pynput import keyboard as kb
        modifiers_held = set()
        MOD_MAP = {
            kb.Key.ctrl: "ctrl", kb.Key.ctrl_l: "ctrl", kb.Key.ctrl_r: "ctrl",
            kb.Key.shift: "shift", kb.Key.shift_l: "shift", kb.Key.shift_r: "shift",
            kb.Key.alt: "alt", kb.Key.alt_l: "alt", kb.Key.alt_r: "alt",
            kb.Key.cmd: "win", kb.Key.cmd_l: "win", kb.Key.cmd_r: "win",
        }
        result = {"combo": None}

        def on_press(key):
            if key in MOD_MAP:
                modifiers_held.add(MOD_MAP[key])
            else:
                parts = sorted(modifiers_held)
                if hasattr(key, "char") and key.char:
                    parts.append(key.char.lower())
                elif hasattr(key, "name"):
                    parts.append(key.name)
                else:
                    parts.append(str(key).lower())
                result["combo"] = "+".join(parts)
                listener.stop()

        def on_release(key):
            if key in MOD_MAP:
                modifiers_held.discard(MOD_MAP[key])

        listener = kb.Listener(on_press=on_press, on_release=on_release)
        listener.start()

        def wait_and_finish():
            listener.join()
            combo = result["combo"]
            if self._record_target and combo:
                self.root.after(0, lambda: self._apply_recorded(combo))
            else:
                self.root.after(0, self._reset_record_buttons)

        threading.Thread(target=wait_and_finish, daemon=True).start()

    def _apply_recorded(self, combo):
        if self._record_target:
            self._record_target.delete(0, tk.END)
            self._record_target.insert(0, combo)
        self._reset_record_buttons()

    # ── 保存 & 关闭 ───────────────────────────────────
    def _on_save(self):
        if "toggle_always_on_top" in self._hotkey_entries:
            hotkey = self._hotkey_entries["toggle_always_on_top"].get().strip()
            if hotkey:
                self.config.set_hotkey("toggle_always_on_top", hotkey)
        for plugin_id, entry in self._plugin_entries.items():
            plugin_name = plugin_id[len("plugin_"):]
            hotkey = entry.get().strip()
            if hotkey:
                self.config.set_plugin_hotkey(plugin_name, hotkey)
        self.config.set_autostart(self.autostart_var.get())
        self._apply_autostart()

        signal_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), ".reload_signal")
        with open(signal_path, "w") as f:
            f.write(json.dumps({"reload": True}))
        self._on_close()

    def _apply_autostart(self):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "AlwaysOnTop"
        if getattr(sys, "frozen", False):
            app_path = f'"{sys.executable}"'
        else:
            script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "main.py"
            )
            pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            app_path = f'"{pythonw}" "{script_path}"'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0,
                                 winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            if self.autostart_var.get():
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, app_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            messagebox.showwarning("开机自启", f"无法更新注册表: {e}")

    def _on_close(self):
        self._reset_record_buttons()
        self.root.destroy()


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_dir, "config.json")
    plugin_dir = os.path.join(base_dir, "plugins")

    app = SettingsWindowProcess(config_path, plugin_dir)
    app.run()


if __name__ == "__main__":
    main()
