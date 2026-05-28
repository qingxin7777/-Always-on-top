import os
import sys
import threading
from config import Config
from window_manager import WindowManager
from hotkey_listener import HotkeyManager
from plugin_system import PluginManager
from tray_icon import TrayApp


class App:

    def __init__(self):
        if getattr(sys, "frozen", False):
            self._base_dir = os.path.dirname(sys.executable)
        else:
            self._base_dir = os.path.dirname(os.path.abspath(__file__))

        self.config_path = os.path.join(self._base_dir, "config.json")
        self.plugin_dir = os.path.join(self._base_dir, "plugins")
        self.icon_path = os.path.join(self._base_dir, "resources", "icon.png")

        self.config = Config(self.config_path)
        self.hotkey_manager = HotkeyManager()
        self.plugin_manager = PluginManager(self.plugin_dir)
        self.tray_app = None

        self._register_core_hotkeys()
        self._load_plugins()

    def _register_core_hotkeys(self):
        hotkey_str = self.config.get_hotkey("toggle_always_on_top")
        self.hotkey_manager.register(
            hotkey_str,
            self._toggle_always_on_top_callback,
            "切换窗口置顶"
        )

    def _load_plugins(self):
        entries = self.plugin_manager.discover_plugins()
        for entry in entries:
            plugin_hotkey = self.config.get_plugin_hotkey(
                entry["name"],
                entry.get("default_hotkey")
            )
            if plugin_hotkey:
                self.hotkey_manager.register(
                    plugin_hotkey,
                    entry["callback"],
                    entry["name"]
                )

    def _toggle_always_on_top_callback(self):
        hwnd = WindowManager.get_active_window_handle()
        if not WindowManager.is_valid_window(hwnd):
            return
        title = WindowManager.get_window_title(hwnd)
        new_state = WindowManager.toggle_always_on_top(hwnd)
        if self.tray_app:
            if new_state:
                self.tray_app.show_notification(f"已置顶: {title}")
            else:
                self.tray_app.show_notification(f"已取消置顶: {title}")

    def reload_hotkeys(self):
        def _do_reload():
            self.hotkey_manager.stop()
            self.hotkey_manager.clear_all()
            self._register_core_hotkeys()
            self._load_plugins()
            self.hotkey_manager.start()
            if self.tray_app:
                self.tray_app.show_notification("快捷键已重新加载")

        threading.Thread(target=_do_reload, daemon=True).start()

    def on_settings_closed(self):
        signal_path = os.path.join(self._base_dir, ".reload_signal")
        if os.path.exists(signal_path):
            try:
                os.remove(signal_path)
            except OSError:
                pass
            self.reload_hotkeys()

    def run(self):
        self.hotkey_manager.start()
        self.tray_app = TrayApp(self, self.config, self.icon_path)
        # 托盘在主线程跑（阻塞），设置窗口作为子进程独立运行
        self.tray_app.run()

    def shutdown(self):
        if self.tray_app:
            self.tray_app.stop()
        self.hotkey_manager.stop()
