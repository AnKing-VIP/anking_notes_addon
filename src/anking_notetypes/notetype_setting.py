import re
from abc import ABC, abstractmethod
from typing import Any, Dict

from anki.models import NotetypeDict

from .ankiaddonconfig import ConfigLayout, ConfigManager
from .notetype_setting_definitions import anking_notetype_names


class NotetypeSetting(ABC):
    def __init__(self, config: Dict):
        self.config = config

    @staticmethod
    def from_config(config: Dict) -> "NotetypeSetting":
        if config["type"] == "checkbox":
            return CheckboxSetting(config)
        if config["type"] == "re_checkbox":
            return ReCheckboxSetting(config)
        if config["type"] == "wrap_checkbox":
            return WrapCheckboxSetting(config)
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
        if config["type"] == "font_family":
            return FontFamilySetting(config)
        else:
            raise Exception(
                f"unkown NoteTypeSetting type: {config.get('type', 'None')}"
            )

    @abstractmethod
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        pass

    def add_widget_to_general_config_layout(self, layout: ConfigLayout):
        self.add_widget_to_config_layout(layout, "general")

    def register_general_setting(self, conf: ConfigManager):
        def update_all(key, value):
            if self.key("general") != key:
                return

            # sets the config value for all anking notetypes
            # even if they dont have this setting available
            # (in this case it will be ignored)
            for notetype_name in anking_notetype_names():
                conf.set(self.key(notetype_name), value)
            conf.config_window.update_widgets()

        conf.on_change(update_all)

    def is_present(self, model: "NotetypeDict") -> bool:
        # returns True if the section related to the setting is present on the model
        relevant_template_text = self._relevant_template_text(model)
        return bool(re.search(self.config["regex"], relevant_template_text))

    def setting_value(self, model: "NotetypeDict") -> Any:
        section = self._relevant_template_section(model)
        result = self._extract_setting_value(section)
        return result

    def updated_model(
        self, model: "NotetypeDict", notetype_name: str, conf: ConfigManager
    ) -> "NotetypeDict":
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

    def name(self):
        return self.config["name"]

    def key(self, notetype_name: str) -> str:
        # returns the config key of this setting for the notetype in the config
        return f"{notetype_name}.{self.name()}"

    def _relevant_template_section(self, model: "NotetypeDict"):
        template_text = self._relevant_template_text(model)
        section_match = re.search(self.config["regex"], template_text)
        if not section_match:
            raise NotetypeParseException(
                f"could not find '{self.config['name']}' in {self.config['file']} template of notetype '{model['name']}'"
            )
        result = section_match.group(0)
        return result

    @abstractmethod
    def _extract_setting_value(self, section: str) -> Any:
        pass

    @abstractmethod
    def _set_setting_value(self, section: str, setting_value: Any):
        pass

    def _relevant_template_text(self, model: "NotetypeDict") -> str:
        templates = model["tmpls"]

        # all the AnKing notetypes have one template each
        assert len(templates) == 1
        template = templates[0]

        if self.config["file"] == "front":
            result = template["qfmt"]
        elif self.config["file"] == "back":
            result = template["afmt"]
        else:
            result = model["css"]
        return result


class NotetypeParseException(Exception):
    pass


class ReCheckboxSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.checkbox(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        replacement_pairs = self.config["replacement_pairs"]
        checked = all(y in section for _, y in replacement_pairs)
        unchecked = all(x in section for x, _ in replacement_pairs)
        if not ((checked or unchecked) and not (checked and unchecked)):
            raise NotetypeParseException(
                f"error involving {replacement_pairs=} and {section=}"
            )
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


class WrapCheckboxSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.checkbox(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        start_str, end_str = self.config["wrap_into"]
        return section.startswith(start_str) and section.endswith(end_str)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        result = section
        start_str, end_str = self.config["wrap_into"]
        cur_setting = section.startswith(start_str) and section.endswith(end_str)
        if setting_value:
            if not cur_setting:
                result = start_str + result + end_str
        else:
            if cur_setting:
                result = result[len(start_str) : -len(end_str)]
        return result


class CheckboxSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.checkbox(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
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


class LineEditSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.text_input(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        return re.search(self.config["regex"], section).group(1)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        m = re.search(self.config["regex"], section)
        start, end = m.span(1)
        result = section[:start] + setting_value + section[end:]
        return result


class FontFamilySetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.font_family_combobox(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        return re.search(self.config["regex"], section).group(1)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        m = re.search(self.config["regex"], section)
        start, end = m.span(1)
        result = section[:start] + setting_value + section[end:]
        return result


class DropdownSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.dropdown(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
            labels=self.config["options"],
            values=self.config["options"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        return re.search(self.config["regex"], section).group(1)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        current_value = self._extract_setting_value(section)
        result = section.replace(current_value, setting_value, 1)
        return result


class ColorSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.color_input(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        color_str = re.search(self.config["regex"], section).group(1)
        return color_str

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        current_value = self._extract_setting_value(section)
        if (
            self.config.get("with_inherit_option", False)
            and setting_value == "transparent"
        ):
            result = section.replace(current_value, "inherit", 1)
        else:
            result = section.replace(current_value, setting_value, 1)
        return result


class ShortcutSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.shortcut_edit(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        shortcut_str = re.search(self.config["regex"], section).group(1)
        return shortcut_str

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        m = re.search(self.config["regex"], section)
        start, end = m.span(1)
        result = section[:start] + setting_value + section[end:]
        return result


class NumberEditSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, notetype_name: str):
        layout.number_input(
            key=self.key(notetype_name),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
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
