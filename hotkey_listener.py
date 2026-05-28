import re
import threading
from pynput import keyboard


class HotkeyManager:

    _MODIFIER_MAP = {
        "ctrl": "ctrl", "shift": "shift", "alt": "alt",
        "win": "cmd", "cmd": "cmd", "super": "cmd",
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._entries = []
        self._listener = None
        self._running = False

    def register(self, hotkey_str, callback, name):
        with self._lock:
            self._entries.append({
                "hotkey": hotkey_str,
                "callback": callback,
                "name": name
            })

    def clear_all(self):
        with self._lock:
            self._entries.clear()

    def start(self):
        with self._lock:
            if self._running:
                return
            mappings = self._build_pynput_mappings()
            self._listener = keyboard.GlobalHotKeys(mappings)
            self._listener.start()
            self._running = True

    def stop(self):
        with self._lock:
            if self._listener and self._running:
                self._listener.stop()
                try:
                    self._listener.join(timeout=1.0)
                except RuntimeError:
                    pass
                self._listener = None
                self._running = False

    def _build_pynput_mappings(self):
        result = {}
        for entry in self._entries:
            pynput_str = HotkeyManager.config_to_pynput(entry["hotkey"])
            result[pynput_str] = self._wrap_callback(entry)
        if not result:
            result["<ctrl>+<shift>+<f99>"] = lambda: None
        return result

    @staticmethod
    def _wrap_callback(entry):
        def wrapper():
            try:
                entry["callback"]()
            except Exception:
                import traceback
                traceback.print_exc()
        return wrapper

    @staticmethod
    def config_to_pynput(hotkey_str):
        parts = hotkey_str.lower().strip().split("+")
        converted = []
        modifier_set = {"ctrl", "shift", "alt", "cmd", "win", "super"}
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part in modifier_set:
                pynput_name = HotkeyManager._MODIFIER_MAP.get(part, part)
                converted.append(f"<{pynput_name}>")
            else:
                converted.append(part)
        return "+".join(converted)

    @staticmethod
    def pynput_to_config(hotkey_str):
        tokens = re.findall(r"<(\w+)>|([^<+]+)", hotkey_str)
        parts = []
        for modifier, key in tokens:
            if modifier:
                if modifier == "cmd":
                    modifier = "win"
                parts.append(modifier)
            elif key:
                parts.append(key.strip().lower())
        seen = set()
        deduped = []
        for p in parts:
            if p not in seen:
                deduped.append(p)
                seen.add(p)
        modifiers = {"ctrl", "shift", "alt", "win", "cmd", "super"}
        mod_parts = [p for p in deduped if p in modifiers]
        key_parts = [p for p in deduped if p not in modifiers]
        return "+".join(mod_parts + key_parts)
