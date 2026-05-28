import json
import os


class Config:
    DEFAULTS = {
        "hotkeys": {
            "toggle_always_on_top": "ctrl+alt+t"
        },
        "plugins": {},
        "autostart": True
    }

    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self._load()

    def _load(self):
        if not os.path.exists(self.filepath):
            return dict(self.DEFAULTS)
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            merged = dict(self.DEFAULTS)
            self._deep_merge(merged, loaded)
            return merged
        except (json.JSONDecodeError, IOError):
            return dict(self.DEFAULTS)

    def _deep_merge(self, base, override):
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_hotkey(self, action_name):
        return self.data["hotkeys"].get(action_name)

    def set_hotkey(self, action_name, hotkey_string):
        self.data["hotkeys"][action_name] = hotkey_string
        self.save()

    def get_plugin_hotkey(self, plugin_name, default_hotkey=None):
        plugin_cfg = self.data.get("plugins", {}).get(plugin_name, {})
        return plugin_cfg.get("hotkey", default_hotkey)

    def set_plugin_hotkey(self, plugin_name, hotkey_string):
        self.data.setdefault("plugins", {})
        self.data["plugins"].setdefault(plugin_name, {})
        self.data["plugins"][plugin_name]["hotkey"] = hotkey_string
        self.save()

    def set_autostart(self, enabled):
        self.data["autostart"] = enabled
        self.save()

    def is_autostart_enabled(self):
        return self.data.get("autostart", True)
