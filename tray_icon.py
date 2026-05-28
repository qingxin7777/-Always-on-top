import os
import sys
import threading
import subprocess
import pystray
from PIL import Image, ImageDraw


class TrayApp:

    TOOLTIP = "Always-On-Top"

    def __init__(self, app, config, icon_path):
        self.app = app
        self.config = config
        self.icon_path = icon_path
        self.icon = None
        self._settings_proc = None

    def _load_image(self):
        try:
            return Image.open(self.icon_path)
        except (IOError, FileNotFoundError):
            return self._generate_default_icon()

    def _generate_default_icon(self):
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([4, 4, 60, 60], fill=(70, 130, 180, 255),
                     outline=(255, 255, 255, 255), width=2)
        draw.rectangle([26, 14, 38, 36], fill=(255, 255, 255, 255))
        draw.polygon([(26, 36), (32, 50), (38, 36)], fill=(255, 255, 255, 255))
        return img

    def _create_icon(self):
        image = self._load_image()
        menu = self._build_menu()
        self.icon = pystray.Icon("always-on-top", image, self.TOOLTIP, menu)

    def _build_menu(self):
        toggle_item = pystray.MenuItem(
            "切换置顶",
            self._toggle_active_window,
            default=True
        )
        settings_item = pystray.MenuItem(
            "设置...",
            self._open_settings
        )
        exit_item = pystray.MenuItem(
            "退出",
            self._exit_app
        )
        return pystray.Menu(toggle_item, pystray.Menu.SEPARATOR,
                            settings_item, exit_item)

    def _toggle_active_window(self, icon, item):
        self.app._toggle_always_on_top_callback()

    def _open_settings(self, icon, item):
        # 防止重复打开设置窗口
        if self._settings_proc is not None:
            if self._settings_proc.poll() is None:
                return  # 设置窗口还在运行
            self._settings_proc = None

        base_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(base_dir, "settings_app.py")
        try:
            self._settings_proc = subprocess.Popen(
                [sys.executable, script],
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
        except Exception as e:
            self.show_notification(f"无法打开设置: {e}")
            return

        def _watch():
            self._settings_proc.wait()
            self._settings_proc = None
            self.app.on_settings_closed()

        threading.Thread(target=_watch, daemon=True).start()

    def _exit_app(self, icon, item):
        self.app.shutdown()

    def run(self):
        self._create_icon()
        self.icon.run()

    def stop(self):
        if self.icon:
            self.icon.stop()

    def show_notification(self, message, title="Always-On-Top"):
        if self.icon:
            try:
                self.icon.notify(message, title=title)
            except Exception:
                pass
