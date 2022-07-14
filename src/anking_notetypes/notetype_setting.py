import re
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Any, Callable, Dict, OrderedDict, Union

from .ankiaddonconfig import ConfigLayout, ConfigManager
from .notetype_setting_definitions import anking_notetype_names

try:
    from anki.models import NotetypeDict  # type: ignore pylint: disable=unused-import
except:
    pass


class NotetypeSetting(ABC):
    def __init__(self, config: Dict):
        self.config = config
        self.register_general_setting_hook: Union[Callable, None] = None

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
        if config["type"] == "order":
            return ElementOrderSetting(config)
        else:
            raise Exception(
                f"unkown NotetypeSetting type: {config.get('type', 'None')}"
            )

    @abstractmethod
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        pass

    def add_widget_to_general_config_layout(self, layout: ConfigLayout):

        # dummy model
        model = {"name": "general"}
        self.add_widget_to_config_layout(layout, model)

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

        self.register_general_setting_hook = update_all
        conf.on_change(update_all)

    def unregister_general_setting(self, conf: ConfigManager):
        assert (
            self.register_general_setting_hook is not None
        ), "tried unregistering general setting without registering it first"
        conf.remove_on_change_hook(self.register_general_setting_hook)

    def is_present(self, model: "NotetypeDict") -> bool:
        # returns True if the section related to the setting is present on the model
        relevant_template_text = self._relevant_template_text(model)
        return bool(re.search(self.config["regex"], relevant_template_text))

    # can raise NotetypeSettingException
    def setting_value(self, model: "NotetypeDict") -> Any:
        try:
            section = self._relevant_template_section(model)
            result = self._extract_setting_value(section)
        except NotetypeSettingException as e:
            raise e
        except Exception as e:
            raise NotetypeSettingException(e)
        return result

    # can raise NotetypeSettingException
    def updated_model(
        self, model: "NotetypeDict", model_archetype_name: str, conf: ConfigManager
    ) -> "NotetypeDict":
        result = deepcopy(model)
        section = self._relevant_template_section(result)
        key = self.key(model_archetype_name)

        # if the setting is not in the config,
        # use the default value if present else don't change anything
        no_value = object()  # value different from all other values
        setting_value = conf.get(key, self.config.get("default", no_value))
        if setting_value is no_value:
            return result

        try:
            processed_section = self._set_setting_value(section, setting_value)

            updated_text = self._relevant_template_text(result).replace(
                section, processed_section, 1
            )
        except NotetypeSettingException as e:
            raise e
        except Exception as e:
            raise NotetypeSettingException(e)

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
            raise NotetypeSettingException(
                f"could not find '{self.config['text']}' in {self.config['file']}"
                "template of notetype '{model['name']}'"
            )
        result = section_match.group(0)
        return result

    # raises NotetypeSettingException if the current setting value is
    # not of the expected form and has to be changed for the notetype to work
    @abstractmethod
    def _extract_setting_value(self, section: str) -> Any:
        pass

    # is not allowed to raise NotetypeSettingExceptions
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

    def _replace_first_capture_group(self, section: str, new_value_str: Any) -> str:
        m = re.search(self.config["regex"], section)
        start, end = m.span(1)
        result = section[:start] + new_value_str + section[end:]
        return result


class NotetypeSettingException(Exception):
    pass


class ReCheckboxSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.checkbox(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        replacement_pairs = self.config["replacement_pairs"]
        checked = all(y in section for _, y in replacement_pairs)
        unchecked = all(x in section for x, _ in replacement_pairs)
        if not ((checked or unchecked) and not (checked and unchecked)):
            raise NotetypeSettingException(
                f"{self.config['text']}: error involving {replacement_pairs=} and {section=}"
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
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.checkbox(
            key=self.key(model["name"]),
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
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.checkbox(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        value = re.search(self.config["regex"], section).group(1)
        if value not in ["true", "false"]:
            raise NotetypeSettingException(
                f"{self.config['text']}: expected 'true' or 'false' but got '{value}'"
            )
        return value == "true"

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        new_value_str = "true" if setting_value else "false"
        return self._replace_first_capture_group(section, new_value_str)


class LineEditSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.text_input(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        return re.search(self.config["regex"], section).group(1)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        new_value_str = setting_value.replace('"', '\\"')
        return self._replace_first_capture_group(section, new_value_str)


class FontFamilySetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.font_family_combobox(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        # dont need to verify, because used in css and will be ignored if not valid
        return re.search(self.config["regex"], section).group(1)

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        return self._replace_first_capture_group(section, setting_value)


class DropdownSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.dropdown(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
            labels=self.config["options"],
            values=self.config["options"],
        )

    def _extract_setting_value(self, section: str) -> Any:
        result = re.search(self.config["regex"], section).group(1)
        if result not in self.config["options"]:
            raise NotetypeSettingException(
                f"{self.config['text']}: expected one of {self.config['options']} but got {result}"
            )
        return result

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        return self._replace_first_capture_group(section, setting_value)


class ColorSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.color_input(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        # dont need to verify, because used in css and will be ignored if not valid
        color_str = re.search(self.config["regex"], section).group(1)
        return color_str

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        if (
            self.config.get("with_inherit_option", False)
            and setting_value == "transparent"
        ):
            setting_value_str = "inherit"
        else:
            setting_value_str = setting_value
        return self._replace_first_capture_group(section, setting_value_str)


class ShortcutSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.shortcut_edit(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        # dont need to verify, because notetype js will ignore the shortcut if its invalid
        shortcut_str = re.search(self.config["regex"], section).group(1)
        return shortcut_str

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        new_value_str = setting_value.replace('"', '\\"')
        return self._replace_first_capture_group(section, new_value_str)


class NumberEditSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.number_input(
            key=self.key(model["name"]),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
            minimum=self.config.get("min", 0),
            maximum=self.config.get("max", 1000),
            decimal=self.config.get("decimal", False),
            step=self.config.get("step", 1),
        )

    def _extract_setting_value(self, section: str) -> Any:
        value_str = re.search(self.config["regex"], section).group(1)
        try:
            if self.config.get("decimal", False):
                result = float(value_str)
            else:
                result = int(value_str)
            return result
        except:
            raise NotetypeSettingException(
                f"{self.config['text']}: expected {'decimal' if self.config.get('decimal', False) else 'integer'} "
                f"but found {value_str}"
            )

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        new_value_str = str(setting_value)
        return self._replace_first_capture_group(section, new_value_str)


class ElementOrderSetting(NotetypeSetting):
    def add_widget_to_config_layout(self, layout: ConfigLayout, model: "NotetypeDict"):
        layout.order_widget(
            key=self.key(model["name"]),
            items=list(
                self._name_to_match_odict(self._relevant_template_section(model)).keys()
            ),
            description=self.config["text"],
            tooltip=self.config.get("tooltip", None),
        )

    def _extract_setting_value(self, section: str) -> Any:
        return list(self._name_to_match_odict(section).keys())

    def _set_setting_value(self, section: str, setting_value: Any) -> str:
        result = section[:]
        offset = 0
        name_to_match = self._name_to_match_odict(section)
        if set(setting_value) != set(name_to_match.keys()):
            raise NotetypeSettingException(
                f"invalid value: {setting_value}\nexpected elements: {list(name_to_match.keys())}"
            )

        for i, name in enumerate(setting_value):
            old: re.Match = name_to_match[list(name_to_match.keys())[i]]
            new: re.Match = name_to_match[name]
            start, end = old.span()
            result = result[: start + offset] + new.group(0) + result[end + offset :]
            offset += len(new.group(0)) - len(old.group(0))
        return result

    def _name_to_match_odict(self, section_text: str) -> OrderedDict[str, re.Match]:
        matches = [
            m
            for m in re.finditer(self.config["elem_re"], str(section_text))
            if re.search(self.config["has_to_contain"], m.group(0))
        ]
        result = OrderedDict(
            [
                (re.search(self.config["name_re"], m.group(0)).group(1), m)
                for m in matches
            ]
        )
        return result
