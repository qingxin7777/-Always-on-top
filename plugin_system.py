import importlib.util
import os
import sys
import traceback


class PluginManager:

    REQUIRED_ATTRS = ["PLUGIN_NAME", "callback"]

    def __init__(self, plugin_dir):
        self.plugin_dir = plugin_dir
        self.loaded_plugins = []

    def discover_plugins(self):
        if not os.path.isdir(self.plugin_dir):
            return []

        results = []
        for filename in sorted(os.listdir(self.plugin_dir)):
            if filename.startswith("_") or not filename.endswith(".py"):
                continue

            module_name = filename[:-3]
            module_path = os.path.join(self.plugin_dir, filename)

            try:
                module = self._import_module(module_name, module_path)
            except Exception:
                traceback.print_exc()
                continue

            if not self._is_valid_plugin(module):
                continue

            default_hotkey = getattr(module, "PLUGIN_HOTKEY", None)
            self.loaded_plugins.append(module)

            results.append({
                "name": module.PLUGIN_NAME,
                "callback": module.callback,
                "default_hotkey": default_hotkey,
                "module": module,
            })

        return results

    def _import_module(self, module_name, filepath):
        spec = importlib.util.spec_from_file_location(
            f"plugins.{module_name}", filepath
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def _is_valid_plugin(self, module):
        name = getattr(module, "PLUGIN_NAME", None)
        cb = getattr(module, "callback", None)
        if not isinstance(name, str) or name == "":
            return False
        if not callable(cb):
            return False
        return True
