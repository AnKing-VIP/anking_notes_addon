import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, OrderedDict, Tuple

setting_configs: Dict[str, Any] = {
    "toggle_all_buttons": {
        "name": "Toggle all buttons shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +ToggleAllButtonsShortcut += +"([^"]*?)"',
        "section": "Hint Buttons",
        "default": "'",
    },
    "autoscroll_to_button": {
        "name": "scroll to button when toggled",
        "tooltip": "",
        "type": "checkbox",
        "file": "back",
        "regex": "var +ScrollToButton += +(false|true)",
        "section": "Hint Buttons",
        "default": True,
    },
    "io_reveal_next_shortcut": {
        "name": "Image Occlusion Reveal Next",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +RevealIncrementalShortcut += +"(.*?)"',
        "section": "Image Occlusion",
        "default": "N",
    },
    "io_toggle_all_shortcut": {
        "name": "Image Occlusion Toggle All",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +ToggleAllOcclusionsShortcut += +"(.*?)"',
        "section": "Image Occlusion",
        "default": ",",
    },
    "reveal_cloze_shortcut": {
        "name": "Reveal Cloze Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +revealNextShortcut += +"(.*?)"',
        "section": "Clozes",
        "default": "N",
    },
    "reveal_cloze_word_shortcut": {
        "name": "Reveal Cloze Word Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +revealNextWordShortcut += +"(.*?)"',
        "section": "Clozes",
        "default": "Shift+N",
    },
    "toggle_all_clozes_shortcut": {
        "name": "Toggle all clozes shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +toggleAllShortcut += +"(.*?)"',
        "section": "Clozes",
        "default": ",",
    },
    "reveal_next_cloze_mode": {
        "name": "Reveal Next Cloze Mode",
        "tooltip": "cloze: clozes are revealed normally\nword: clozes are revealed word by word",
        "type": "dropdown",
        "file": "back",
        "regex": 'var +revealNextClozeMode += +"([^"]*?)"',
        "options": ["cloze", "word"],
        "section": "Clozes",
        "default": "cloze",
    },
    "cloze_hider": {
        "name": "Cloze Hider",
        "tooltip": "Text that will displayed instead of the clozed text",
        "type": "text",
        "file": "back",
        "regex": 'var +clozeHider +=[^"]+"([^"]*?)"',
        "section": "Clozes",
        "default": "👑",
    },
    "timer": {
        "name": "Timer",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".timer *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "section": "Timer",
        "default": True,
    },
    "timer_secs": {
        "name": "timer duration (seconds)",
        "tooltip": "",
        "type": "number",
        "file": "front",
        "regex": "var +seconds += +([^ /\n]*)",
        "min": 0,
        "section": "Timer",
        "default": 9,
    },
    "timer_minutes": {
        "name": "timer duration (minutes)",
        "tooltip": "",
        "type": "number",
        "file": "front",
        "regex": "var +minutes += +([^ /\n]*)",
        "min": 0,
        "section": "Timer",
        "default": 0,
    },
    "autoflip": {
        "name": "flip to back of card automatically\n(doesn't work on AnkiMobile)",
        "tooltip": "",
        "type": "checkbox",
        "file": "front",
        "regex": "var +autoflip += +(false|true)",
        "default": True,
    },
    "front_tts": {
        "name": "Front TTS",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "front",
        "regex": "(<!--|{{)tts.+?(-->|}})",
        "replacement_pairs": [("<!--", "{{"), ("-->", "}}")],
        "section": "Text to Speech",
        "default": False,
    },
    "back_tts": {
        "name": "Back TTS",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "back",
        "regex": "(<!--|{{)tts.+?(-->|}})",
        "replacement_pairs": [("<!--", "{{"), ("-->", "}}")],
        "section": "Text to Speech",
        "default": False,
    },
    "front_signal_tag": {
        "name": "tag that will trigger red background for the front",
        "tooltip": "",
        "type": "text",
        "file": "front",
        "regex": 'var +tagID += +"([^"]*?)"',
        "section": "Tags",
        "default": "XXXYYYZZZ",
    },
    "back_signal_tag": {
        "name": "tag that will trigger red background for the back",
        "tooltip": "",
        "type": "text",
        "file": "back",
        "regex": 'var +tagID += +"([^"]*?)"',
        "section": "Tags",
        "default": "XXXYYYZZZ",
    },
    "tags_container": {
        "name": "Tags container",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".#tags-container *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "section": "Tags",
        "default": True,
    },
    "tags_container_mobile": {
        "name": "Tags container (mobile)",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".mobile +#tags-container *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "section": "Tags",
        "default": False,
    },
    "tags_toggle_shortcut": {
        "name": "Toggle Tags Shorcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +toggleTagsShortcut += +"(.*?)"',
        "section": "Tags",
        "default": "C",
    },
    "font_size": {
        "name": "Font Size",
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
        "name": "Font Size (mobile)",
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
        "name": "Font Family",
        "tooltip": "",
        "type": "font_family",
        "file": "style",
        "regex": ".card.*\n*kbd *{[^}]*?font-family: (.+);",
        "section": "Font",
        "default": "Arial Greek, Arial",
    },
    "image_height": {
        "name": "Max Image Height",
        "tooltip": "a css value is needed for this field",
        "type": "text",
        "file": "style",
        "regex": "img *{[^}]*?max-height: (.+);",
        "section": "Image Styling",
        "default": "none",
    },
    "image_width": {
        "name": "Max Image Width",
        "tooltip": "a css value is needed for this field",
        "type": "text",
        "file": "style",
        "regex": "img *{[^}]*?max-width: (.+);",
        "section": "Image Styling",
        "default": "85%",
    },
    "text_color": {
        "name": "Default Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".card *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "black",
    },
    "background_color": {
        "name": "Background color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".card *{[^}]*?background-color: (.+?);",
        "section": "Colors",
        "default": "#D1CFCE",
    },
    "cloze_color": {
        "name": "Cloze Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".cloze *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "blue",
    },
    "extra_text_color": {
        "name": "Extra Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": "#extra *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "navy",
    },
    "hint_text_color": {
        "name": "Hint Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".hints *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "#4297F9",
    },
    "missed_text_color": {
        "name": "Missed Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": "#missed *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "red",
    },
    "timer_text_color": {
        "name": "Timer Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".timer *{[^}]*?color: (.+?);",
        "section": "Colors",
        "default": "transparent",
    },
    "nm_text_color": {
        "name": "Night Mode Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .card *{[^}]*?color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "#FFFAFA",
    },
    "nm_background_color": {
        "name": "Night Mode Background color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .card *{[^}]*?background-color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "#272828",
    },
    "nm_cloze_color": {
        "name": "Night Mode Cloze color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .cloze *{[^}]*?color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "#4297F9",
    },
    "nm_extra_color": {
        "name": "Night Mode Extra color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode #extra *{[^}]*?color: (.+?) +(!important)?;",
        "section": "Colors",
        "default": "magenta",
    },
    "nm_hint_color": {
        "name": "Night Mode Hint Reveal color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .hints *{[^}]*?color: (.+?) *(!important)?;",
        "section": "Colors",
        "default": "cyan",
    },
    "bold_text_color": {
        "name": "Bold Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "b *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "section": "Colors",
        "default": "inherit",
    },
    "underlined_text_color": {
        "name": "Underlined Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "u *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "section": "Colors",
        "default": "inherit",
    },
    "italic_text_color": {
        "name": "Italic Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "i *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "section": "Colors",
        "default": "inherit",
    },
}


def anking_notetype_templates() -> Dict[str, Tuple[str, str, str]]:
    result = dict()
    for x in (Path(__file__).parent / "note_types").iterdir():
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


def settings_by_notetype_dict() -> Dict[str, List[str]]:
    result = defaultdict(lambda: [])
    for notetype_name, templates in anking_notetype_templates().items():
        front_template, back_template, styling = templates
        for setting_name, config in setting_configs.items():
            if config["file"] == "front":
                relevant_template = front_template
            elif config["file"] == "back":
                relevant_template = back_template
            else:
                relevant_template = styling

            if re.search(config["regex"], relevant_template):
                result[notetype_name].append(setting_name)
    return result


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
    }


def button_shortcut_setting_config(button_name, default):
    return {
        "name": f"{button_name} Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var+ ButtonShortcuts *= *{{[^}}]*?"{button_name}" *: *"([^"]*)"',
        "hint_button_setting": button_name,
        "section": "Hint Buttons",
        "default": default,
    }


def auto_reveal_setting_config(button_name, default):
    return {
        "name": f"Auto Reveal {button_name}",
        "tooltip": "",
        "type": "checkbox",
        "file": "back",
        "regex": f'var+ ButtonAutoReveal *= *{{[^}}]*?"{button_name}" *: *(true|false)',
        "hint_button_setting": button_name,
        "section": "Hint Buttons",
        "default": default,
    }


setting_configs = {**all_btns_setting_configs(), **setting_configs}


settings_by_notetype = settings_by_notetype_dict()

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

if __name__ == "__main__":
    from pprint import pprint

    pprint(settings_by_notetype)
