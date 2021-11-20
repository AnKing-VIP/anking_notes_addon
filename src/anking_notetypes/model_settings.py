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

from typing import Any, Dict


settings_by_notetype = {
    "AnKing": [
        "timer_minutes",
        "timer_secs",
        "toggle_all_buttons",
        "personal_notes_button",
        "missed_questions_button",
        "front_tts",
        "back_tts",
        "front_signal_tag",
        "back_signal_tag",
    ],
    "Basic-AnKing": ["front_tts"],
    "IO-one by one": ["autoflip"],
    "AnKingDerm": [
        "toggle_all_buttons",
        "personal_notes_button",
        "missed_questions_button",
        "textbook_button",
        "additional_resources_button",
    ],
    "AnKingMCAT": [
        "toggle_all_buttons",
        "lecture_notes_button",
        "missed_questions_button",
        "pixorize_button",
        "additional_resources_button",
    ],
}
}

# settings that apply to multiple note types
# (the ones that have this setting listed in
# settings_by_notetype)
# they can be overwritten in the note types settings
general_settings = [
    "toggle_all_buttons",
]


def button_shortcut_regex(name):
    return


def button_shortcut_setting_config(button_name, default):
    return {
        "name": f"{button_name} Shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": f'ButtonShortcuts += +{{[\w\W]+?"{button_name}" +: +"([^"]*)[\w\W]+?}}"',
        "default": default,
    }


def auto_reveal_setting_config(button_name, default):
    return {
        "name": f"Auto Reveal {button_name}",
        "tooltip": "",
        "type": "checkbox",
        "file": "back",
        "regex": f'ButtonAutoReveal += +{{[\w\W]+?"{button_name}" +: +"([^"]*)[\w\W]+?}}"',
        "default": default,
    }


setting_configs: Dict[str, Any] = {
    "lecture_notes_button": button_shortcut_setting_config("Lecture Notes", "Alt+1"),
    "personal_notes_button": button_shortcut_setting_config("Personal Notes", "Alt+1"),
    "missed_questions_button": button_shortcut_setting_config(
        "Missed Questions", "Alt+2"
    ),
    "pixorize_button": button_shortcut_setting_config("Pixorize", "Alt+3"),
    "textbook_button": button_shortcut_setting_config("Textbook", "Alt+3"),
    "additional_resources_button": button_shortcut_setting_config(
        "Additional Resources", "Alt+4"
    ),
    "toggle_all_buttons": {
        "name": "Toggle all buttons shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": 'var +ToggleAllButtonsShortcut += +"([^"]*?)"',
        "default": "'",
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
        "name": "tag that will trigger red background for front of the card",
        "tooltip": "",
        "type": "text",
        "file": "front",
        "regex": 'var +tagID += +"([^"]*?)"',
        "default": "XXXYYYZZZ",
    },
    "back_signal_tag": {
        "name": "tag that will trigger red background for back of the card",
        "tooltip": "",
        "type": "text",
        "file": "back",
        "regex": 'var +tagID += +"([^"]*?)"',
        "default": "XXXYYYZZZ",
    },
}
