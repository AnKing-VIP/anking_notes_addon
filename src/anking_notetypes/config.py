import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

from anki.models import NotetypeDict
from aqt import mw
from aqt.clayout import CardLayout
from PyQt5.QtCore import *  # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtWidgets import *

from .ankiaddonconfig import ConfigManager, ConfigWindow
from .ankiaddonconfig.window import ConfigLayout
from .model_settings import general_settings, setting_configs, settings_by_notetype


class NoteTypeSetting(ABC):
    def __init__(self, config: Dict):
        self.config = config

    @abstractmethod
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        pass

    def add_widget_to_general_config_layout(self, tab: ConfigLayout):
        self.add_widget_to_config_layout(tab, "general")

    def register_general_setting(self, conf: ConfigManager):
        def update_all(key, value):
            if self.key("general") != key:
                return
            for notetype_name in settings_by_notetype.keys():
                if (
                    not self.config["setting_name"]
                    in settings_by_notetype[notetype_name]
                ):
                    continue
                conf.set(self.key(notetype_name), value, trigger_change_hook=False)
            conf.config_window.update_widgets()

        conf.on_change(update_all)

    @staticmethod
    def from_config(config: Dict) -> "NoteTypeSetting":
        if config["type"] == "checkbox":
            return CheckboxSetting(config)
        if config["type"] == "re_checkbox":
            return ReCheckboxSetting(config)
        if config["type"] == "text":
            return LineEditSetting(config)
        if config["type"] == "number":
            return NumberEditSetting(config)
        if config["type"] == "shortcut":
            return ShortcutSetting(config)
        if config["type"] == "dropdown":
            return DropdownSetting(config)
        if config["type"] == "color":
            return ColorSetting(config)
        else:
            raise Exception(
                f"unkown NoteTypeSetting type: {config.get('type', 'None')}"
            )

    def setting_value(self, model: NotetypeDict) -> Any:
        section = self._relevant_template_section(model)
        result = self._extract_setting_value(section)
        return result

    def _relevant_template_section(self, model: NotetypeDict):
        template_text = self._relevant_template_text(model)
        section_match = re.search(self.config["regex"], template_text)
        if not section_match:
            raise Exception(
                f"could not find '{self.config['regex']}' in relevant template"
            )
        result = section_match.group(0)
        return result

    @abstractmethod
    def _extract_setting_value(self, section: str) -> Any:
        pass

    def updated_model(
        self, model: NotetypeDict, notetype_name: str, conf: ConfigManager
    ) -> NotetypeDict:
        result = model.copy()
        section = self._relevant_template_section(result)
        setting_value = conf[self.key(notetype_name)]
        processed_section = self._set_setting_value(section, setting_value)
        updated_text = self._relevant_template_text(result).replace(
            section, processed_section, 1
        )

        templates = result["tmpls"]
        assert len(templates) == 1
        template = templates[0]

        if self.config["file"] == "front":
            template["qfmt"] = updated_text
        elif self.config["file"] == "back":
            template["afmt"] = updated_text
        else:
            result["css"] = updated_text

        return result

    @abstractmethod
    def _set_setting_value(self, section: str, setting_value: Any):
        pass

    def key(self, notetype_name: str) -> str:
        return f'{notetype_name}.{self.config["setting_name"]}'

    def _relevant_template_text(self, model: NotetypeDict) -> str:
        templates = model["tmpls"]
        assert len(templates) == 1
        template = templates[0]

        if self.config["file"] == "front":
            result = template["qfmt"]
        elif self.config["file"] == "back":
            result = template["afmt"]
        else:
            result = model["css"]
        return result


class ReCheckboxSetting(NoteTypeSetting):
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        tab.checkbox(
            key=self.key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        replacement_pairs = self.config["replacement_pairs"]
        checked = all(y in section for _, y in replacement_pairs)
        unchecked = all(x in section for x, _ in replacement_pairs)
        if not ((checked or unchecked) and not (checked and unchecked)):
            raise Exception(f"error involving {replacement_pairs=} and {section=}")
        return checked

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        result = section
        replacement_pairs = self.config["replacement_pairs"]
        for x, y in replacement_pairs:
            if setting_value:
                result = result.replace(x, y)
            else:
                result = result.replace(y, x)

        return result


class CheckboxSetting(NoteTypeSetting):
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        tab.checkbox(
            key=self.key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        value = re.search(self.config["regex"], section).group(1)
        assert value in ["true", "false"]
        return value == "true"

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        current_value = self._extract_setting_value(section)
        current_value_str = "true" if current_value else "false"
        new_value_str = "true" if setting_value else "false"
        result = section.replace(current_value_str, new_value_str, 1)
        return result


class LineEditSetting(NoteTypeSetting):
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        tab.text_input(
            key=self.key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        return re.search(self.config["regex"], section).group(1)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        m = re.search(self.config["regex"], section)
        start, end = m.span(1)
        result = section[:start] + setting_value + section[end:]
        return result


class DropdownSetting(NoteTypeSetting):
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        tab.dropdown(
            key=self.key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
            labels=self.config["options"],
            values=self.config["options"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        return re.search(self.config["regex"], section).group(1)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        current_value = self._extract_setting_value(section)
        result = section.replace(current_value, setting_value, 1)
        return result


class ColorSetting(NoteTypeSetting):
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        tab.color_input(
            key=self.key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        color_str = re.search(self.config["regex"], section).group(1)
        if self.config.get("with_inherit_option", False) and str(color_str) in [
            "transparent",
            " #00000000",
        ]:
            return "inherit"
        return color_str

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        current_value = self._extract_setting_value(section)
        if self.config.get("with_inherit_option", False) and setting_value in [
            "transparent",
            "#00000000",
        ]:
            result = section.replace(current_value, "inherit", 1)
        else:
            result = section.replace(current_value, setting_value, 1)
        return result


class ShortcutSetting(NoteTypeSetting):
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        tab.shortcut_edit(
            key=self.key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        shortcut_str = re.search(self.config["regex"], section).group(1)
        return shortcut_str

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        m = re.search(self.config["regex"], section)
        start, end = m.span(1)
        result = section[:start] + setting_value + section[end:]
        return result


class NumberEditSetting(NoteTypeSetting):
    def add_widget_to_config_layout(self, tab: ConfigLayout, notetype_name: str):
        tab.number_input(
            key=self.key(notetype_name),
            description=self.config["name"],
            tooltip=self.config["tooltip"],
            minimum=self.config.get("min", None),
            maximum=self.config.get("max", 99999),
        )

    def _extract_setting_value(self, section: str) -> Any:
        value_str = re.search(self.config["regex"], section).group(1)
        return int(value_str)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        current_value = self._extract_setting_value(section)
        result = section.replace(str(current_value), str(setting_value), 1)
        return result


def notetype_settings_tab(notetype_name: str, ntss: List[NoteTypeSetting]) -> Callable:
    def tab(window: ConfigWindow):
        tab = window.add_tab(notetype_name)
        scroll = tab.scroll_layout()
        for nts in ntss:
            nts.add_widget_to_config_layout(scroll, notetype_name)
            scroll.space(7)

        scroll.stretch()

    return tab


def general_tab(ntss: List[NoteTypeSetting]) -> Callable:
    def tab(window: ConfigWindow):
        tab = window.add_tab("General")
        scroll = tab.scroll_layout()
        for nts in ntss:
            nts.add_widget_to_general_config_layout(scroll)
            nts.register_general_setting(tab.conf)
            scroll.space(7)

        scroll.stretch()

    return tab


def change_window_settings(window: ConfigWindow, on_save):
    window.setWindowTitle("AnKing note types")
    window.setMinimumHeight(500)
    window.setMinimumWidth(500)

    window.execute_on_save(on_save)


def ntss_for_notetype(notetype_name) -> List[NoteTypeSetting]:
    result = []
    for name in settings_by_notetype[notetype_name]:
        setting_config = setting_configs[name]
        setting_config["setting_name"] = name
        result.append(NoteTypeSetting.from_config(setting_config))
    return result


def general_ntss():
    result = []
    for name in general_settings:
        setting_config = setting_configs[name]
        setting_config["setting_name"] = name
        result.append(NoteTypeSetting.from_config(setting_config))
    return result


def open_config_window(clayout: CardLayout = None):
    conf = ConfigManager()

    # read in settings from notetypes and update config and save
    for notetype_name in settings_by_notetype.keys():
        model = mw.col.models.by_name(notetype_name)
        for nts in ntss_for_notetype(notetype_name):
            conf[nts.key(notetype_name)] = nts.setting_value(model)
    conf.save()

    # if in live preview mode read in current not confirmed settings
    if clayout:
        model = clayout.model
        notetype_name = clayout.model["name"]
        for nts in ntss_for_notetype(notetype_name):
            conf[nts.key(notetype_name)] = nts.setting_value(model)

    # add general tab
    conf.add_config_tab(general_tab(general_ntss()))

    # setup tabs for all notetypes
    for notetype_name in settings_by_notetype.keys():
        conf.add_config_tab(
            notetype_settings_tab(notetype_name, ntss_for_notetype(notetype_name))
        )

    # setup live update of clayout model on changes
    def update_clayout_model(key: str, _: Any):
        model = clayout.model
        notetype_name, setting_name = key.split(".")
        if notetype_name != clayout.model["name"]:
            return

        nts = NoteTypeSetting.from_config(setting_configs[setting_name])
        model = nts.updated_model(model, notetype_name, conf)

        clayout.model = model
        clayout.change_tracker.mark_basic()
        clayout.update_current_ordinal_and_redraw(clayout.ord)

    if clayout:
        conf.on_change(update_clayout_model)

    # setup update of notetypes on save
    def update_notetypes():
        for notetype_name in settings_by_notetype.keys():
            model = mw.col.models.by_name(notetype_name)
            for nts in ntss_for_notetype(notetype_name):
                model = nts.updated_model(model, notetype_name, conf)
            mw.col.models.update_dict(model)

    conf.on_window_open(
        lambda window: change_window_settings(window, on_save=update_notetypes)
    )

    # open the config window
    conf.open_config()
