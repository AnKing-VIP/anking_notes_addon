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
    "Cloze-AnKing": ["front_tts"],
    "Cloze-AnKingMaster-v3": ["front_tts"],
    "Cloze-AnKingDerm": ["front_tts"],
}

setting_configs: Dict[str, Any] = {
    "front_tts": {
        "name": "TTS",
        "tooltip": "",
        "type": "re_checkbox",
        "file": "front",
        "regex": "(<!--|{{)tts en_US voices=Apple_Samantha speed=1.4:cloze:Text(-->|\}\})",
        "checked_value": "{{tts en_US voices=Apple_Samantha speed=1.4:cloze:Text}}",
        "unchecked_value": "<!--tts en_US voices=Apple_Samantha speed=1.4:cloze:Text-->",
        "default": False,
    },
    "signal_tag": {
        "name": "tag that will trigger red background",
        "tooltip": "",
        "type": "text",
        "file": "front",
        "regex": 'var +tagID += +"(\w+?)"',
        "default": "XXXYYYZZZ",
    },
    "toggle_all_buttons": {
        "name": "Toggle all buttons shortcut",
        "tooltip": "",
        "type": "shortcut",
        "file": "back",
        "regex": "var +ToggleAllButtons += +'(\w+?)'",
        "default": "222",
    },
}
