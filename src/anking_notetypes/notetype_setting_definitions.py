import json
import re
from pathlib import Path
from typing import Any, Dict, OrderedDict, Tuple

from anki.models import NotetypeDict

ANKING_NOTETYPES_PATH = Path(__file__).parent / "note_types"

# for matching text between double quotes which can contain
# escaped quotes
QUOT_STR_RE = r'(?:\\.|[^"\\])'


setting_configs: Dict[str, Any] = {
    "toggle_all_buttons": {
        "text": "Toggle all buttons shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var +ToggleAllButtonsShortcut += +"({QUOT_STR_RE}*?)"',
        "section": "Hint Buttons",
        "default": "'",
    },
    "autoscroll_to_button": {
        "text": "scroll to button when toggled",
        "tooltip": "",
        "type": "checkbox",
        "file": "back",
        "regex": "var +ScrollToButton += +(false|true)",
        "section": "Hint Buttons",
        "default": True,
    },
    "io_reveal_next_shortcut": {
        "text": "Image Occlusion Reveal Next",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var +RevealIncrementalShortcut += +"({QUOT_STR_RE}*?)"',
        "section": "Image Occlusion",
        "default": "N",
    },
    "io_toggle_all_shortcut": {
        "text": "Image Occlusion Toggle All",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var +ToggleAllOcclusionsShortcut += +"({QUOT_STR_RE}*?)"',
        "section": "Image Occlusion",
        "default": ",",
    },
    "reveal_cloze_shortcut": {
        "text": "Reveal Cloze Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var +revealNextShortcut += +"({QUOT_STR_RE}*?)"',
        "section": "Clozes",
        "default": "N",
    },
    "reveal_cloze_word_shortcut": {
        "text": "Reveal Cloze Word Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var +revealNextWordShortcut += +"({QUOT_STR_RE}*?)"',
        "section": "Clozes",
        "default": "Shift+N",
    },
    "toggle_all_clozes_shortcut": {
        "text": "Toggle all clozes shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var +toggleAllShortcut += +"({QUOT_STR_RE}*?)"',
        "section": "Clozes",
        "default": ",",
    },
    "reveal_next_cloze_mode": {
        "text": "Reveal Next Cloze Mode",
        "tooltip": "cloze: clozes are revealed normally\nword: clozes are revealed word by word",
        "type": "dropdown",
        "file": "back",
        "regex": 'var +revealNextClozeMode += +"([^"]*?)"',
        "options": ["cloze", "word"],
        "section": "Clozes",
        "default": "cloze",
    },
    "cloze_hider": {
        "text": "Cloze Hider",
        "tooltip": "Text that will displayed instead of the clozed text",
        "type": "text",
        "file": "back",
        "regex": f'var +clozeHider +=[^"]+"({QUOT_STR_RE}*?)"',
        "section": "Clozes",
        "default": "👑",
    },
    "timer": {
        "text": "Timer",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".timer *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "section": "Timer",
        "default": True,
    },
    "timer_secs": {
        "text": "timer duration (seconds)",
        "tooltip": "",
        "type": "number",
        "file": "front",
        "regex": "var +seconds += +([^ /\n]*)",
        "min": 0,
        "section": "Timer",
        "default": 9,
    },
    "timer_minutes": {
        "text": "timer duration (minutes)",
        "tooltip": "",
        "type": "number",
        "file": "front",
        "regex": "var +minutes += +([^ /\n]*)",
        "min": 0,
        "section": "Timer",
        "default": 0,
    },
    "autoflip": {
        "text": "flip to back of card automatically\n(doesn't work on AnkiMobile)",
        "tooltip": "",
        "type": "checkbox",
        "file": "front",
        "regex": "var +autoflip += +(false|true)",
        "default": True,
    },
    "front_tts": {
        "text": "Front TTS",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "front",
        "regex": "(<!--|{{)tts.+?(-->|}})",
        "replacement_pairs": [("<!--", "{{"), ("-->", "}}")],
        "section": "Text to Speech",
        "default": False,
    },
    "back_tts": {
        "text": "Back TTS",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "back",
        "regex": "(<!--|{{)tts.+?(-->|}})",
        "replacement_pairs": [("<!--", "{{"), ("-->", "}}")],
        "section": "Text to Speech",
        "default": False,
    },
    "front_signal_tag": {
        "text": "tag that will trigger red background for the front",
        "tooltip": "",
        "type": "text",
        "file": "front",
        "regex": f'var +tagID += +"({QUOT_STR_RE}*?)"',
        "section": "Tags",
        "default": "XXXYYYZZZ",
    },
    "back_signal_tag": {
        "text": "tag that will trigger red background for the back",
        "tooltip": "",
        "type": "text",
        "file": "back",
        "regex": f'var +tagID += +"({QUOT_STR_RE}*?)"',
        "section": "Tags",
        "default": "XXXYYYZZZ",
    },
    "tags_container": {
        "text": "Tags container",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".#tags-container *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "section": "Tags",
        "default": True,
    },
    "tags_container_mobile": {
        "text": "Tags container (mobile)",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".mobile +#tags-container *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "section": "Tags",
        "default": False,
    },
    "tags_toggle_shortcut": {
        "text": "Toggle Tags Shorcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var +toggleTagsShortcut += +"({QUOT_STR_RE}*?)"',
        "section": "Tags",
        "default": "C",
    },
    "font_size": {
        "text": "Font Size",
        "tooltip": "",
        "type": "number",
        "file": "style",
        "regex": "html *{[^}]*?font-size: ([\d]+)px;",
        "min": 1,
        "max": 50,
        "section": "Font",
        "default": 28,
    },
    "font_size_mobile": {
        "text": "Font Size (mobile)",
        "tooltip": "",
        "type": "number",
        "file": "style",
        "regex": ".mobile *{[^}]*?font-size: ([\d]+)px;",
        "min": 1,
        "max": 50,
        "section": "Font",
        "default": 28,
    },
    "font_family": {
        "text": "Font Family",
        "tooltip": "",
        "type": "font_family",
        "file": "style",
        "regex": ".card.*\n*kbd *{[^}]*?font-family: (.+);",
        "section": "Font",
        "default": "Arial Greek, Arial",
    },
    "image_height": {
        "text": "Max Image Height",
        "tooltip": "a css value is needed for this field",
        "type": "text",
        "file": "style",
        "regex": "img *{[^}]*?max-height: (.+);",
        "section": "Image Styling",
        "default": "none",
    },
    "image_width": {
        "text": "Max Image Width",
        "tooltip": "a css value is needed for this field",
        "type": "text",
        "file": "style",
        "regex": "img *{[^}]*?max-width: (.+);",
        "section": "Image Styling",
        "default": "85%",
    },
    "text_color": {
        "text": "Default Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".card *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "black",
    },
    "background_color": {
        "text": "Background color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".card *{[^}]*?background-color: (.+?);",
        "section": "Colors",
        "default": "#D1CFCE",
    },
    "cloze_color": {
        "text": "Cloze Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".cloze *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "blue",
    },
    "extra_text_color": {
        "text": "Extra Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": "#extra *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "navy",
    },
    "hint_text_color": {
        "text": "Hint Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".hints *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "#4297F9",
    },
    "missed_text_color": {
        "text": "Missed Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": "#missed *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "red",
    },
    "timer_text_color": {
        "text": "Timer Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".timer *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "transparent",
    },
    "nm_text_color": {
        "text": "Night Mode Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .card *{[^}]*?color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "#FFFAFA",
    },
    "nm_background_color": {
        "text": "Night Mode Background color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .card *{[^}]*?background-color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "#272828",
    },
    "nm_cloze_color": {
        "text": "Night Mode Cloze color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .cloze *{[^}]*?color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "#4297F9",
    },
    "nm_extra_color": {
        "text": "Night Mode Extra color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode #extra *{[^}]*?color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "magenta",
    },
    "nm_hint_color": {
        "text": "Night Mode Hint Reveal color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .hints *{[^}]*?color: (.+?) *(!important)?;",
        "section": "Colors",
        "default": "cyan",
    },
    "bold_text_color": {
        "text": "Bold Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "b *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "section": "Colors",
        "default": "inherit",
    },
    "underlined_text_color": {
        "text": "Underlined Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "u *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "section": "Colors",
        "default": "inherit",
    },
    "italic_text_color": {
        "text": "Italic Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "i *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "section": "Colors",
        "default": "inherit",
    },
}


def anking_notetype_names():
    return [name for name, _ in anking_notetype_templates().items()]


def anking_notetype_templates() -> Dict[str, Tuple[str, str, str]]:
    result = dict()
    for x in ANKING_NOTETYPES_PATH.iterdir():
        if not x.is_dir():
            continue
        notetype_name = x.name

        front_template = (x / "Front Template.html").read_text(
            encoding="utf-8", errors="ignore"
        )
        back_template = (x / ("Back Template.html")).read_text(
            encoding="utf-8", errors="ignore"
        )
        styling = (x / ("Styling.css")).read_text(encoding="utf-8", errors="ignore")
        result[notetype_name] = (front_template, back_template, styling)

    return result


def anking_notetype_model(notetype_name: str) -> "NotetypeDict":
    return json.loads(
        (ANKING_NOTETYPES_PATH / notetype_name / f"{notetype_name}.json").read_text()
    )


def all_btns_setting_configs():
    result = dict()
    for notetype_name in anking_notetype_templates().keys():
        for btn_name, shortcut in btn_name_to_shortcut_odict(notetype_name).items():
            result.update(btn_setting_config(btn_name, shortcut))
    return result


def btn_name_to_shortcut_odict(notetype_name):
    _, back, _ = anking_notetype_templates()[notetype_name]

    button_shortcuts_dict_pattern = "var+ ButtonShortcuts *= *{([^}]*)}"
    m = re.search(button_shortcuts_dict_pattern, back)
    if not m:
        return dict()

    result = OrderedDict()
    dict_key_value_pattern = '"([^"]+)" *: *"([^"]+)"'
    button_shorcut_pairs = re.findall(dict_key_value_pattern, m.group(1))
    for btn_name, shortcut in button_shorcut_pairs:
        result[btn_name] = shortcut
    return result


def btn_setting_config(name, default_shortcut):
    name_in_snake_case = name.lower().replace(" ", "_")
    return {
        f"btn_shortcut_{name_in_snake_case}": button_shortcut_setting_config(
            name, default_shortcut
        ),
        f"autoreveal_{name_in_snake_case}": auto_reveal_setting_config(name, False),
        f"disable_{name_in_snake_case}": disable_field_setting_config(name, False),
    }


def button_shortcut_setting_config(button_name, default):
    return {
        "text": f"{button_name} Shortcut",
        "type": "shortcut",
        "file": "back",
        "regex": f'var+ ButtonShortcuts *= *{{[^}}]*?"{button_name}" *: *"({QUOT_STR_RE}*?)"',
        "hint_button_setting": button_name,
        "section": "Hint Buttons",
        "default": default,
    }


def auto_reveal_setting_config(button_name, default):
    return {
        "text": f"Auto Reveal {button_name}",
        "type": "checkbox",
        "file": "back",
        "regex": f'var+ ButtonAutoReveal *= *{{[^}}]*?"{button_name}" *: *(.+),\n',
        "hint_button_setting": button_name,
        "section": "Hint Buttons",
        "default": default,
    }


def disable_field_setting_config(button_name, default):
    return {
        "text": f"Disable {button_name} Field",
        "tooltip": "",
        "type": "wrap_checkbox",
        "file": "back",
        "regex": f"(<!--)?{{{{#{button_name}}}}}[\w\W]+?{{{{/{button_name}}}}}(-->)?",
        "wrap_into": ("<!--", "-->"),
        "section": "Fields",
        "default": default,
    }


setting_configs = {**all_btns_setting_configs(), **setting_configs}

for setting_name, setting_config in setting_configs.items():
    setting_config["name"] = setting_name

# settings that apply to multiple note types
# (the ones that have this setting listed in
# settings_by_notetype)
# they can be overwritten in the note types settings
general_settings = [
    "toggle_all_buttons",
    "autoscroll_to_button",
    "tags_toggle_shortcut",
    "reveal_cloze_shortcut",
    "toggle_all_clozes_shortcut",
    "reveal_next_cloze_mode",
    "cloze_hider",
    "timer",
    "timer_secs",
    "timer_minutes",
    "autoflip",
    "front_tts",
    "back_tts",
    "front_signal_tag",
    "back_signal_tag",
    "tags_container",
    "tags_container_mobile",
    "font_size",
    "font_size_mobile",
    "font_family",
    "image_height",
    "image_width",
    "text_color",
    "background_color",
    "cloze_color",
    "extra_text_color",
    "hint_text_color",
    "missed_text_color",
    "timer_text_color",
    "nm_text_color",
    "nm_background_color",
    "nm_cloze_color",
    "nm_extra_color",
    "nm_hint_color",
    "bold_text_color",
    "underlined_text_color",
    "italic_text_color",
]


def general_settings_defaults_dict():
    result = dict()
    for setting_name in general_settings:
        result[setting_name] = setting_configs[setting_name]["default"]
    return result
