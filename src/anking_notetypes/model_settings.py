# mapping between notetypes and setting names

# mapping between setting name (in config) to tuples of the form
# (
# setting name in ui
# (tooltip)
# setting/widget type (checkbox, number, text, shortcut, color_picker, dropdown (?))
#   for dropdown: option names and values
#   for number: min, max
# which file it is in (front, back, style, color-picker)
# name of setting in file / regex for substituting relevant part in template
#   (could group variables in js and css files - css variables)
#   if everything was grouped regex wouldnt be needed
# default value
# )

# {
# tagId = "asdf" // #s "id of the tag" text
# mode = "foo" // #s dropdown ["baba", "yaga", "nada"]
# timerS =  // #s number
# }

# I maybe need a script to generate the config.json file from the data in the current file

import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def button_shortcut_setting_config(button_name, default):
    return {
        "name": f"{button_name} Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'var+ ButtonShortcuts *= *{{[\w\W]*?"{button_name}" *: *"([^"]*)"[\w\W]*?}}"',
        "default": default,
    }


def auto_reveal_setting_config(button_name, default):
    return {
        "name": f"Auto Reveal {button_name}",
        "tooltip": "",
        "type": "checkbox",
        "file": "back",
        "regex": f'var+ ButtonAutoReveal *= *{{[\w\W]*?"{button_name}" *: *(true|false)[\w\W]*?}}"',
        "default": default,
    }


setting_configs: Dict[str, Any] = {
    "lecture_notes_button": button_shortcut_setting_config("Lecture Notes", "Alt+1"),
    "lecture_notes_autoreveal": auto_reveal_setting_config("Lecture Notes", False),
    "personal_notes_button": button_shortcut_setting_config("Personal Notes", "Alt+1"),
    "personal_notes_autoreveal": auto_reveal_setting_config("Personal Notes", False),
    "missed_questions_button": button_shortcut_setting_config(
        "Missed Questions", "Alt+2"
    ),
    "missed_questions_autoreveal": auto_reveal_setting_config(
        "Missed Questions", False
    ),
    "pixorize_button": button_shortcut_setting_config("Pixorize", "Alt+3"),
    "pixorize_autoreveal": auto_reveal_setting_config("Pixorize", False),
    "textbook_button": button_shortcut_setting_config("Textbook", "Alt+3"),
    "textbook_autoreveal": auto_reveal_setting_config("Textbook", False),
    "additional_resources_button": button_shortcut_setting_config(
        "Additional Resources", "Alt+4"
    ),
    "additional_resources_autoreveal": auto_reveal_setting_config(
        "Additional Resources", False
    ),
    "extra_button": button_shortcut_setting_config("Extra", "Alt+1"),
    "extra_autoreveal": auto_reveal_setting_config("Extra", False),
    "definitions_button": button_shortcut_setting_config("Definitions", "Alt+1"),
    "definitions_autoreveal": auto_reveal_setting_config("Definitions", False),
    "examples_button": button_shortcut_setting_config("Definitions", "Alt+1"),
    "examples_autoreveal": button_shortcut_setting_config("Definitions", "Alt+1"),
    "alternative_translations_button": button_shortcut_setting_config(
        "Definitions", "Alt+1"
    ),
    "alternative_translations_autoreveal": auto_reveal_setting_config(
        "Definitions", False
    ),
    "toggle_all_buttons": {
        "name": "Toggle all buttons shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +ToggleAllButtonsShortcut += +"([^"]*?)"',
        "default": "'",
    },
    "autoscroll_to_button": {
        "name": "scroll to button when toggled",
        "tooltip": "",
        "type": "checkbox",
        "file": "back",
        "regex": "var +ScrollToButton += +(false|true)",
        "default": True,
    },
    "reveal_cloze_shortcut": {
        "name": "Reveal Cloze Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +revealClozeShortcut += +"([^"]*?)"',
        "default": "N",
    },
    "reveal_cloze_word_shortcut": {
        "name": "Reveal Cloze Word Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +revealClozeWordShortcut += +"([^"]*?)"',
        "default": "Shift + N",
    },
    "reveal_next_cloze_mode": {
        "name": "Reveal Next Cloze Mode",
        "tooltip": "cloze: clozes are revealed normally\nword: clozes are revealed word by word",
        "type": "dropdown",
        "file": "back",
        "regex": 'var +revealNextClozeMode += +"([^"]*?)"',
        "options": ["cloze", "word"],
        "default": "cloze",
    },
    "cloze_hider": {
        "name": "Cloze Hider",
        "tooltip": "Text that will displayed instead of the clozed text",
        "type": "text",
        "file": "back",
        "regex": 'var +clozeHider +=[^"]+"([^"]*?)"',
        "default": "👑",
    },
    "timer_secs": {
        "name": "timer duration (seconds)",
        "tooltip": "",
        "type": "number",
        "file": "front",
        "regex": "var +seconds += +([^ /\n]*)",
        "min": 0,
        "default": 9,
    },
    "timer_minutes": {
        "name": "timer duration (minutes)",
        "tooltip": "",
        "type": "number",
        "file": "front",
        "regex": "var +minutes += +([^ /\n]*)",
        "min": 0,
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
        "default": False,
    },
    "back_tts": {
        "name": "Back TTS",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "back",
        "regex": "(<!--|{{)tts.+?(-->|}})",
        "replacement_pairs": [("<!--", "{{"), ("-->", "}}")],
        "default": False,
    },
    "front_signal_tag": {
        "name": "tag that will trigger red background for the front",
        "tooltip": "",
        "type": "text",
        "file": "front",
        "regex": 'var +tagID += +"([^"]*?)"',
        "default": "XXXYYYZZZ",
    },
    "back_signal_tag": {
        "name": "tag that will trigger red background for the back",
        "tooltip": "",
        "type": "text",
        "file": "back",
        "regex": 'var +tagID += +"([^"]*?)"',
        "default": "XXXYYYZZZ",
    },
    "timer": {
        "name": "Timer",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".timer *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "default": True,
    },
    "tags_container": {
        "name": "Tags container",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".#tags-container *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "default": True,
    },
    "tags_container_mobile": {
        "name": "Tags container (mobile)",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "style",
        "regex": ".mobile +#tags-container *{[^}]*?display: (block|none);",
        "replacement_pairs": [("none", "block")],
        "default": False,
    },
    "font_size": {
        "name": "Font Size",
        "tooltip": "",
        "type": "number",
        "file": "style",
        "regex": "html *{[^}]*?font-size: ([\d]+)px;",
        "min": 1,
        "max": 50,
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
        "default": 28,
    },
    "font_style": {
        "name": "Font Style",
        "tooltip": "",
        "type": "text",
        "file": "style",
        "regex": ".card.*\n*kbd *{[^}]*?font-family: (.+);",
        "default": "Arial Greek, Arial",
    },
    "image_height": {
        "name": "Max Image Height",
        "tooltip": "a css value is needed for this field",
        "type": "text",
        "file": "style",
        "regex": "img *{[^}]*?max-height: (.+);",
        "default": "none",
    },
    "image_width": {
        "name": "Max Image Width",
        "tooltip": "a css value is needed for this field",
        "type": "text",
        "file": "style",
        "regex": "img *{[^}]*?max-width: (.+);",
        "default": "85%",
    },
    "text_color": {
        "name": "Default Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".card *{[^}]*?color: (.+?);",
        "default": "black",
    },
    "background_color": {
        "name": "Background color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".card *{[^}]*?background-color: (.+?);",
        "default": "#D1CFCE",
    },
    "cloze_color": {
        "name": "Cloze Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".cloze *{[^}]*?color: (.+?);",
        "default": "blue",
    },
    "extra_text_color": {
        "name": "Extra Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": "#extra *{[^}]*?color: (.+?);",
        "default": "navy",
    },
    "hint_text_color": {
        "name": "Hint Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".hints *{[^}]*?color: (.+?);",
        "default": "#4297F9",
    },
    "missed_text_color": {
        "name": "Missed Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": "#missed *{[^}]*?color: (.+?);",
        "default": "red",
    },
    "timer_text_color": {
        "name": "Timer Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".timer *{[^}]*?color: (.+?);",
        "default": "transparent",
    },
    "nm_text_color": {
        "name": "Night Mode Text color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .card *{[^}]*?color: (.+?) +(!important)?;",
        "default": "#FFFAFA",
    },
    "nm_background_color": {
        "name": "Night Mode Background color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .card *{[^}]*?background-color: (.+?) +(!important)?;",
        "default": "#272828",
    },
    "nm_cloze_color": {
        "name": "Night Mode Cloze color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .cloze *{[^}]*?color: (.+?) +(!important)?;",
        "default": "#4297F9",
    },
    "nm_extra_color": {
        "name": "Night Mode Extra color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode #extra *{[^}]*?color: (.+?) +(!important)?;",
        "default": "magenta",
    },
    "nm_hint_color": {
        "name": "Night Mode Hint Reveal color",
        "tooltip": "",
        "type": "color",
        "file": "style",
        "regex": ".night_mode .hints *{[^}]*?color: (.+?) *(!important)?;",
        "default": "cyan",
    },
    "bold_text_color": {
        "name": "Bold Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "b *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "default": "inherit",
    },
    "underlined_text_color": {
        "name": "Underlined Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "u *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "default": "inherit",
    },
    "italic_text_color": {
        "name": "Italic Text color",
        "tooltip": "set to transparent for normal color",
        "type": "color",
        "file": "style",
        "regex": "i *{[^}]*?color: (.+?) *(!important)?;",
        "with_inherit_option": True,
        "default": "inherit",
    },
}


def settings_by_notetype_dict() -> Dict[str, List[str]]:
    result = defaultdict(lambda: [])
    for x in (Path(__file__).parent / "note_types").iterdir():
        if not x.is_dir():
            continue
        notetype_name = x.name

        front_template = (x / "Front Template.html").read_text()
        back_template = (x / ("Back Template.html")).read_text()
        styling = (x / ("Styling.css")).read_text()

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


settings_by_notetype = settings_by_notetype_dict()

# settings that apply to multiple note types
# (the ones that have this setting listed in
# settings_by_notetype)
# they can be overwritten in the note types settings
general_settings = [
    "toggle_all_buttons",
    "autoscroll_to_button",
    "reveal_cloze_shortcut",
    "reveal_next_cloze_mode",
    "cloze_hider",
    "timer_secs",
    "timer_minutes",
    "autoflip",
    "front_tts",
    "back_tts",
    "front_signal_tag",
    "back_signal_tag",
    "timer",
    "tags_container",
    "tags_container_mobile",
    "font_size",
    "font_size_mobile",
    "font_style",
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
