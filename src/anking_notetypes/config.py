import re
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Callable, Dict, List

from aqt import mw
from PyQt5.QtCore import *  # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtWidgets import *

from .ankiaddonconfig.window import ConfigLayout

from .ankiaddonconfig import ConfigManager, ConfigWindow
from .model_settings import setting_configs, settings_by_notetype


class NoteTypeSetting(ABC):
    def __init__(self, config: Dict):
        self.config = config

    def add_widget_to_tab(self, tab: ConfigLayout, notetype_name: str):
        pass

    @staticmethod
    def from_config(config: Dict):
        if config["type"] == "re_checkbox":
            return ReCheckboxSetting(config)
        else:
            raise Exception(
                f"unkown NoteTypeSetting type: {config.get('type', 'None')}"
            )

    def update_notetype(self, notetype_name: str, conf: ConfigManager):
        col = mw.col
        model = col.models.by_name(notetype_name)
        templates = model["tmpls"]
        assert len(templates) == 1
        template = templates[0]

        if self.config["file"] == "front":
            text = template["qfmt"]
        elif self.config["file"] == "back":
            text = template["afmt"]
        else:
            text = model["css"]

        setting_value = conf[self._key(notetype_name)]
        updated_text = self._process_text(text, setting_value)

        if self.config["file"] == "front":
            template["qfmt"] = updated_text
        elif self.config["file"] == "back":
            template["afmt"] = updated_text
        else:
            model["css"] = updated_text

        col.models.update_dict(model)

    @abstractmethod
    def _process_text(self, text: str, setting_value: Any) -> str:
        pass

    def _key(self, notetype_name: str):
        return f'{notetype_name}.{self.config["setting_name"]}'


class ReCheckboxSetting(NoteTypeSetting):
    def add_widget_to_tab(self, tab: ConfigLayout, notetype_name: str):
        cb = tab.checkbox(
            key=self._key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
        )
        cb.setChecked(self.config["default"])

    def _process_text(self, text: str, setting_value: Any) -> str:
        section_match = re.search(self.config["regex"], text)
        assert section_match
        section = section_match.group(0)

        if setting_value:
            processed_section = re.sub(
                self.config["unchecked_value"], self.config["checked_value"], section
            )
        else:
            processed_section = re.sub(
                self.config["checked_value"], self.config["unchecked_value"], section
            )

        result = text.replace(section, processed_section)
        return result


def notetype_settings_tab(notetype_name: str, ntss: List[NoteTypeSetting]) -> Callable:
    def tab(window: ConfigWindow):
        tab = window.add_tab(notetype_name)

        for nts in ntss:
            nts.add_widget_to_tab(tab, notetype_name)
            tab.space(7)

        tab.stretch()

    return tab


def change_window_settings(window: ConfigWindow, on_save):
    window.setWindowTitle("AnKing note types")
    window.setMinimumHeight(500)
    window.setMinimumWidth(500)

    window.execute_on_save(on_save)


def open_config_window():
    conf = ConfigManager()

    # construct all NoteTypeSetting objects and store them
    ntss_by_notetype: Dict[str, List[NoteTypeSetting]] = defaultdict(lambda: [])
    for notetype_name, setting_names in settings_by_notetype.items():
        for name in setting_names:
            setting_config = setting_configs[name]
            setting_config["setting_name"] = name
            nts = NoteTypeSetting.from_config(setting_config)
            ntss_by_notetype[notetype_name].append(nts)

    # setup tabs for all notetypes
    for notetype_name, ntss in ntss_by_notetype.items():
        conf.add_config_tab(notetype_settings_tab(notetype_name, ntss))

    # setup update of notetypes on save
    def update_notetypes():
        for notetype_name, ntss in ntss_by_notetype.items():
            for nts in ntss:
                nts.update_notetype(notetype_name, conf)

    conf.on_window_open(
        lambda window: change_window_settings(window, on_save=update_notetypes)
    )

    # open the config window
    conf.open_config()
