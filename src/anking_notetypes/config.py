from abc import ABC
from collections import defaultdict
from typing import Callable, Dict, List

from PyQt5.QtCore import *  # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtWidgets import *

from anking_notetypes.ankiaddonconfig.window import ConfigLayout

from .ankiaddonconfig import ConfigManager, ConfigWindow
from .model_settings import setting_configs, settings_by_notetype


class NoteTypeSetting(ABC):
    def __init__(self, config: Dict):
        self.config = config

    def add_widget_to_tab(self, tab: ConfigLayout):
        pass

    def update_notetype(self, notetype_name: str):
        pass

    @staticmethod
    def from_config(config: Dict):
        if config["type"] == "re_checkbox":
            return ReCheckboxSetting(config)
        else:
            raise Exception(
                f"unkown NoteTypeSetting type: {config.get('type', 'None')}"
            )


class ReCheckboxSetting(NoteTypeSetting):

    def add_widget_to_tab(self, tab: ConfigLayout):
        cb = tab.checkbox(
            key=self.config["key"],
            description=self.config["name"],
            tooltip=self.config["tooltip"],
        )
        cb.setChecked(self.config["default"])


    def update_notetype(self, notetype_name: str):
        pass


def notetype_settings_tab(notetype_name: str, setting_names: List[str]) -> Callable:
    def tab(window: ConfigWindow):
        tab = window.add_tab(notetype_name)

        for name in setting_names:
            setting_config = setting_configs[name]
            s = NoteTypeSetting(setting_config)
            s.add_widget_to_tab(tab)

            tab.space(7)

        tab.stretch()

    return tab


def change_window_settings(window: ConfigWindow):
    window.setWindowTitle("AnKing note types")
    window.setMinimumHeight(500)
    window.setMinimumWidth(500)


def open_config_window():
    conf = ConfigManager()
    conf.on_window_open(change_window_settings)

    # construct all NoteTypeSetting objects and store them
    ntss_by_notetype: Dict[str, List[NoteTypeSetting]] = defaultdict(lambda: [])
    for notetype_name, setting_names in settings_by_notetype.items():
        for name in setting_names:
            setting_config = setting_configs[name]
            setting_config["key"] = name
            nts = NoteTypeSetting.from_config(setting_config)
            ntss_by_notetype[notetype_name].append(nts)

    # setup tabs
    for notetype_name, ntss in settings_by_notetype.items():
        conf.add_config_tab(lambda: notetype_settings_tab(notetype_name, ntss))

    # update notetypes on save
    def update_notetypes():
        for notetype_name, ntss in ntss_by_notetype.items():
            for nts in ntss:
                nts.update_notetype(notetype_name)

    conf.config_window.execute_on_save(update_notetypes)

    conf.open_config()
