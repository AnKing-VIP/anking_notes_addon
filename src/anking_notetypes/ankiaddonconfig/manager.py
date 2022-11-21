import copy
import json
from sys import platform
from typing import Any, Callable, Dict, Iterator, List, Optional

from aqt import mw
from aqt.qt import Qt

from .window import ConfigWindow


class ConfigManager:
    def __init__(self) -> None:
        self.config_window: Optional[ConfigWindow] = None
        self.window_open_hooks: List[Callable[[ConfigWindow], None]] = []
        self.change_hooks: List[Callable] = []
        self._config: Dict
        addon_dir = __name__.split(".", maxsplit=1)[0]
        self.addon_dir = addon_dir
        try:
            self.addon_name = mw.addonManager.addon_meta(addon_dir).human_name()
        except:
            self.addon_name = mw.addonManager.addonName(addon_dir)
        self.load()

    def load(self) -> None:
        "Loads config from disk"
        self._config = mw.addonManager.getConfig(self.addon_dir)

    def save(self) -> None:
        "Writes its config data to disk."
        mw.addonManager.writeConfig(self.addon_dir, self._config)

    def to_json(self) -> str:
        return json.dumps(self._config)

    def get_from_dict(self, dict_obj: dict, key: str) -> Any:
        "Raises KeyError if config doesn't exist"
        levels = key.split(".")
        return_val = dict_obj
        for level in levels:
            if isinstance(return_val, list):
                level = int(level)
            return_val = return_val[level]
        return return_val

    def copy(self) -> Dict:
        return copy.deepcopy(self._config)

    def get(self, key: str, default: Any = None) -> Any:
        "Returns default or None if config doesn't exist"
        try:
            return self.get_from_dict(self._config, key)
        except KeyError:
            return default

    def set(self, key: str, value: Any, on_change_trigger: bool = True) -> None:
        levels = key.split(".")
        conf_obj = self._config
        for i in range(len(levels) - 1):
            level = levels[i]
            if isinstance(conf_obj, list):
                level = int(level)
            try:
                conf_obj = conf_obj[level]
            except KeyError:
                conf_obj[level] = {}
                conf_obj = conf_obj[level]
        level = levels[-1]
        if isinstance(conf_obj, list):
            level = int(level)

        old_value = conf_obj.get(level, None)
        conf_obj[level] = value

        if on_change_trigger and value != old_value:
            for hook in self.change_hooks:
                hook(key, value)

    def pop(self, key: str) -> Any:
        levels = key.split(".")
        conf_obj = self._config
        for i in range(len(levels) - 1):
            level = levels[i]
            if isinstance(conf_obj, list):
                level = int(level)
            try:
                conf_obj = conf_obj[level]
            except KeyError:
                return None
        level = levels[-1]
        if isinstance(conf_obj, list):
            level = int(level)
        return conf_obj.pop(level)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        "This function only modifies the internal config data. Call conf.save() to actually write to disk"
        self.set(key, value)

    def __iter__(self) -> Iterator:
        return iter(self._config)

    def __delitem__(self, key: str) -> Any:
        self.pop(key)

    def __contains__(self, key: str) -> bool:
        try:
            self.get_from_dict(self._config, key)
            return True
        except KeyError:
            return False

    # Config Window

    def open_config(self, parent=mw) -> ConfigWindow:
        config_window = ConfigWindow(self, parent)
        self.config_window = config_window
        for fn in self.window_open_hooks:
            fn(config_window)
        config_window.on_open()

        # the second method of opening the window doesn't work on MacOs
        # (the window is in the back, can't be brought to the front and
        # is not interactive)
        if parent == mw or platform == "darwin":
            config_window.exec()
        else:
            config_window.setWindowModality(Qt.WindowModality.NonModal)
            config_window.show()
            config_window.activateWindow()
            config_window.raise_()

        return config_window

    def on_window_open(self, fn: Callable[["ConfigWindow"], None]) -> None:
        self.window_open_hooks.append(fn)

    add_config_tab = on_window_open

    def on_change(self, fn: Callable[[str, Any], None]) -> None:
        self.change_hooks.append(fn)

    def remove_on_change_hook(self, fn: Callable[[str, Any], None]) -> None:
        self.change_hooks.remove(fn)
