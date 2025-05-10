import json
import re
from pathlib import Path
from typing import Any, Dict, List, OrderedDict, Tuple, Union

try:
    from anki.models import NotetypeDict  # pylint: disable=unused-import
except:
    pass

ANKING_NOTETYPES_PATH = Path(__file__).parent / "note_types"

FIELD_BOUNDARY_RE = (  # noqa: E731
    lambda ch, field_name_re: rf"(?:\{{\{{{ch}{field_name_re}\}}\}}|<span.+?PSEUDO-FIELD {ch}{field_name_re}</span>)"
)

# Regular expression for fields for which the add-on offers settings aka configurable fields.
# Most of these fields are represented as hint buttons, but not all of them.
# To be recognized by the add-on the field html needs to contain text matching
# CONFIGURABLE_FIELD_HAS_TO_CONTAIN_RE.
# Whether something is a hint button or not is determined by its presence in the ButtonShortcuts dict.
# The surrounding "<!--" are needed because of the disable field setting.
# With the default argument, the regex matches all conditional fields.
CONDITIONAL_FIELD_RE = lambda field_name_re=".+?": (  # noqa: E731
    rf"(?:<!-- ?)?{FIELD_BOUNDARY_RE('#', field_name_re)}[\w\W]+?{FIELD_BOUNDARY_RE('/', field_name_re)}(?: ?-->)?"
)

CONFIGURABLE_FIELD_HAS_TO_CONTAIN_RE = (
    r'(class="hint"|id="extra"|id="dermnet"|id="ome"|id="ca1")'
)

CONFIGURABLE_FIELD_NAME_RE = r'data-name="([\w\W]+?)"'
CONFIGURABLE_FIELD_FALLBACK_NAME_RE = r"\{\{#(.+?)\}\}"


# for matching text between double quotes which can contain escaped quotes
QUOT_STR_RE = r'(?:\\.|[^"\\])'


HINT_BUTTONS = {
    "ln": "Personal/Lecture Notes",
    "mq": "Missed Questions",
    "tx": "Textbook",
    "ar": "Additional Resources",
    "pixorize": "Pixorize",
    "sketchy": "Sketchy",
    "sketchy2": "Sketchy 2",
    "sketchyextra": "Sketchy Extra",
    "pat": "Pathoma",
    "bb": "Boards and Beyond",
    "fa": "First Aid",
    "picomnic": "Picomnic",
    "physeo": "Physeo",
    "bootcamp": "Bootcamp",
    "ome": "OME",
    "df": "Definitions",
    "exp": "Examples",
    "alt": "Alternative Translations",
    "ex": "Extra",
}

ANKIMOBILE_USER_ACTIONS = [
    "undefined",
    "window.revealNextCloze",
    "window.toggleAllCloze",
    "() => revealNextClozeOf('word')",
    "window.toggleNextButton",
    "() => (Array.from(document.getElementsByClassName('hintBtn')).forEach(e => toggleHintBtn(e.id)))",
    "window.toggleNext",
    "window.toggleAll",
    "window.showtags",
    *[f"() => toggleHintBtn('hint-{id}')" for id in HINT_BUTTONS.keys()],
]
ANKIMOBILE_USER_ACTION_LABELS = [
    "None",
    "Reveal Next Cloze",
    "Toggle All Clozes",
    "Reveal Cloze Word",
    "Toggle Next Button",
    "Toggle All Buttons",
    "Reveal Next Occlusion",
    "Toggle All Occlusions",
    "Toggle Tags",
    *[f"Reveal {name}" for name in HINT_BUTTONS.values()],
]


setting_configs: Dict[str, Any] = OrderedDict(
    {
        "field_order": {
            "text": "Field Order",
            "tooltip": "drag and drop the field names to adjust their order",
            "type": "order",
            "file": "back",
            "regex": r"[\w\W]*",
            "elem_re": CONDITIONAL_FIELD_RE(),
            "name_res": (
                CONFIGURABLE_FIELD_NAME_RE,
                CONFIGURABLE_FIELD_FALLBACK_NAME_RE,
            ),
            "has_to_contain": CONFIGURABLE_FIELD_HAS_TO_CONTAIN_RE,
            "section": "Fields",
        },
        "toggle_next_button": {
            "text": "Toggle next button shortcut",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +ToggleNextButtonShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Hint Buttons",
            "default": "H",
        },
        "toggle_all_buttons": {
            "text": "Toggle all buttons shortcut",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +ToggleAllButtonsShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Hint Buttons",
            "default": "'",
        },
        "autoscroll_to_button": {
            "text": "scroll to button when toggled",
            "tooltip": "",
            "type": "checkbox",
            "file": "back",
            "regex": r"var +ScrollToButton += +(false|true)",
            "section": "Hint Buttons",
            "default": True,
        },
        "io_reveal_next_shortcut": {
            "text": "Image Occlusion Reveal Next",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +RevealIncrementalShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Image Occlusion",
            "default": "N",
        },
        "io_toggle_all_shortcut": {
            "text": "Image Occlusion Toggle All",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +ToggleAllOcclusionsShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Image Occlusion",
            "default": ",",
        },
        "reveal_cloze_shortcut": {
            "text": "Reveal Cloze Shortcut",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +revealNextShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Clozes",
            "default": "N",
        },
        "reveal_cloze_word_shortcut": {
            "text": "Reveal Cloze Word Shortcut",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +revealNextWordShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Clozes",
            "default": "Shift+N",
        },
        "toggle_all_clozes_shortcut": {
            "text": "Toggle all clozes shortcut",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +toggleAllShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Clozes",
            "default": ",",
        },
        "reveal_next_cloze_mode": {
            "text": "Reveal Next Cloze Mode",
            "tooltip": "cloze: clozes are revealed normally\nword: clozes are revealed word by word",
            "type": "dropdown",
            "file": "back",
            "regex": r'var +revealNextClozeMode += +"([^"]*?)"',
            "options": ["cloze", "word"],
            "section": "Clozes",
            "default": "cloze",
        },
        "cloze_hider": {
            "text": "Cloze Hider",
            "tooltip": "Text that will displayed instead of the clozed text",
            "type": "text",
            "file": "back",
            "regex": rf'var +clozeHider +=[^"]+"({QUOT_STR_RE}*?)"',
            "section": "Clozes",
            "default": "👑",
        },
        "always_one_by_one": {
            "text": "Always enable one-by-one regardless of whether the one-by-one field is non-empty",
            "tooltip": "",
            "type": "checkbox",
            "file": ["front", "back"],
            "regex": r"var +alwaysOneByOne += +(false|true)",
            "section": "Clozes",
            "default": False,
        },
        "selective_one_by_one": {
            "text": "Selective one-by-one",
            "tooltip": "Allows you to selectively enable one-by-one for some cards "
            "by adding their number to the one-by-one field (separated by commas)",
            "type": "checkbox",
            "file": ["front", "back"],
            "regex": r"var +selectiveOneByOne += +(false|true)",
            "section": "Clozes",
            "default": False,
        },
        "min_number_of_clozes_fo_one_by_one": {
            "text": "Minimum number of clozes for one-by-one (if 0, then no limit)",
            "tooltip": "",
            "type": "number",
            "file": ["front", "back"],
            "regex": r"var +minNumberOfClozes += +([^ /\n]*);",
            "min": 0,
            "section": "Clozes",
            "default": 0,
        },
        "timer": {
            "text": "Timer",
            "tooltip": "",
            "type": "re_checkbox",
            "file": "style",
            "regex": r"\.timer *{[^}]*?display: (block|none);",
            "replacement_pairs": [("none", "block")],
            "section": "Timer",
            "default": True,
        },
        "timer_secs": {
            "text": "timer duration (seconds)",
            "tooltip": "",
            "type": "number",
            "file": "front",
            "regex": r"var +seconds += +([^ /\n]*)",
            "min": 0,
            "section": "Timer",
            "default": 9,
        },
        "timer_minutes": {
            "text": "timer duration (minutes)",
            "tooltip": "",
            "type": "number",
            "file": "front",
            "regex": r"var +minutes += +([^ /\n]*)",
            "min": 0,
            "section": "Timer",
            "default": 0,
        },
        "autoflip": {
            "text": "flip to back of card automatically when one by one is enabled\n(doesn't work on AnkiMobile)",
            "tooltip": "",
            "type": "checkbox",
            "file": "front",
            "regex": r"var +autoflip += +(false|true)",
            "default": True,
        },
        "front_tts": {
            "text": "Front TTS",
            "tooltip": "",
            "type": "re_checkbox",
            "file": "front",
            "regex": r"(<!--|{{)tts.+?(-->|}})",
            "replacement_pairs": [("<!--", "{{"), ("-->", "}}")],
            "section": "Text to Speech",
            "default": False,
        },
        "front_tts_speed": {
            "text": "Front TTS Speed",
            "tooltip": "",
            "type": "number",
            "decimal": True,
            "min": 0.1,
            "max": 10,
            "step": 0.1,
            "file": "front",
            "regex": r"(?:<!--|{{)tts.*?speed=([\d\.]+).*?(?:-->|}})",
            "section": "Text to Speech",
            "default": 1.4,
        },
        "back_tts": {
            "text": "Back TTS",
            "tooltip": """if you enable this and want to use the shortcut for revealing hint buttons one by one
you may have to change the \"Toggle next Button\" shortcut to something else than "H"
(it is in the Hint Buttons section)""",
            "type": "re_checkbox",
            "file": "back",
            "regex": r"(<!--|{{)tts.+?(-->|}})",
            "replacement_pairs": [("<!--", "{{"), ("-->", "}}")],
            "section": "Text to Speech",
            "default": False,
        },
        "back_tts_speed": {
            "text": "Back TTS Speed",
            "tooltip": "",
            "type": "number",
            "decimal": True,
            "min": 0.1,
            "max": 10,
            "step": 0.1,
            "file": "back",
            "regex": r"(?:<!--|{{)tts.*?speed=([\d\.]+).*?(?:-->|}})",
            "section": "Text to Speech",
            "default": 1.4,
        },
        "front_signal_tag": {
            "text": "tag that will trigger red background for the front",
            "tooltip": "",
            "type": "text",
            "file": "front",
            "regex": rf'var +tagID += +"({QUOT_STR_RE}*?)"',
            "section": "Tags",
            "default": "XXXYYYZZZ",
        },
        "back_signal_tag": {
            "text": "tag that will trigger red background for the back",
            "tooltip": "",
            "type": "text",
            "file": "back",
            "regex": rf'var +tagID += +"({QUOT_STR_RE}*?)"',
            "section": "Tags",
            "default": "XXXYYYZZZ",
        },
        "tags_container": {
            "text": "Tags container",
            "tooltip": "",
            "type": "re_checkbox",
            "file": "style",
            "regex": r"\n#tags-container *{[^}]*?display: (block|none);",
            "replacement_pairs": [("none", "block")],
            "section": "Tags",
            "default": True,
        },
        "tags_container_mobile": {
            "text": "Tags container (mobile)",
            "tooltip": "",
            "type": "re_checkbox",
            "file": "style",
            "regex": r"\.mobile +#tags-container *{[^}]*?display: (block|none);",
            "replacement_pairs": [("none", "block")],
            "section": "Tags",
            "default": False,
        },
        "tags_toggle_shortcut": {
            "text": "Toggle Tags Shorcut",
            "tooltip": "",
            "type": "shortcut",
            "file": "back",
            "regex": rf'var +toggleTagsShortcut += +"({QUOT_STR_RE}*?)"',
            "section": "Tags",
            "default": "C",
        },
        "tags_num_levels_to_show_front": {
            "text": "Number of tag levels to show on Front (0 means all)",
            "type": "number",
            "file": "front",
            "regex": r"var +numTagLevelsToShow += +(\d+)",
            "section": "Tags",
            "default": 0,
        },
        "tags_num_levels_to_show_back": {
            "text": "Number of tag levels to show on Back (0 means all)",
            "type": "number",
            "file": "back",
            "regex": r"var +numTagLevelsToShow += +(\d+)",
            "section": "Tags",
            "default": 0,
        },
        "font_size": {
            "text": "Font Size",
            "tooltip": "",
            "type": "number",
            "file": "style",
            "regex": r"html *{[^}]*?font-size: (\d+)px;",
            "min": 1,
            "max": 200,
            "section": "Font",
            "default": 28,
        },
        "font_size_mobile": {
            "text": "Font Size (mobile)",
            "tooltip": "",
            "type": "number",
            "file": "style",
            "regex": r"\.mobile *{[^}]*?font-size: ([\d]+)px;",
            "min": 1,
            "max": 200,
            "section": "Font",
            "default": 28,
        },
        "font_family": {
            "text": "Font Family",
            "tooltip": "",
            "type": "font_family",
            "file": "style",
            "regex": r"\.card.*\n*kbd *{[^}]*?font-family: (.+);",
            "section": "Font",
            "default": "Arial Greek, Arial",
        },
        "image_height": {
            "text": "Max Image Height Percent",
            "tooltip": "",
            "type": "number",
            "file": "style",
            "regex": r"\nimg *{[^}]*?max-height: (.+)%;",
            "max": 100,
            "section": "Image Styling",
            "default": 100,
        },
        "image_width": {
            "text": "Max Image Width Percent",
            "tooltip": "",
            "type": "number",
            "file": "style",
            "regex": r"\nimg *{[^}]*?max-width: (.+)%;",
            "max": 100,
            "section": "Image Styling",
            "default": 85,
        },
        "text_color": {
            "text": "Default Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.card *{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "black",
        },
        "back_text_color": {
            "text": "Back Side Text Color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\#back *{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "black",
        },
        "background_color": {
            "text": "Background color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.card *{[^}]*?background-color: (.+?);",
            "section": "Colors",
            "default": "#D1CFCE",
        },
        "cloze_color": {
            "text": "Cloze Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.cloze.*{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "blue",
        },
        "one_by_one_cloze_color": {
            "text": "One-by-one Cloze Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.cloze.one-by-one.*{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "#009400",
        },
        "one_by_one_cloze_hint_color": {
            "text": "One-by-one Cloze Hint color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.cloze-hint.*{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "#009400",
        },
        "extra_text_color": {
            "text": "Extra Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"#extra.*{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "navy",
        },
        "hint_text_color": {
            "text": "Hint Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.hints *{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "#4297F9",
        },
        "missed_text_color": {
            "text": "Missed Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"#missed *{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "red",
        },
        "timer_text_color": {
            "text": "Timer Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.timer *{[^}]*?color: (.+?);",
            "section": "Colors",
            "default": "transparent",
        },
        "nm_text_color": {
            "text": "Night Mode Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode \.card *{[^}]*?color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "#FFFAFA",
        },
        "nm_back_text_color": {
            "text": "Night Mode Back Side Text Color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode \#back *{[^}]*?color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "#FFFAFA",
        },
        "nm_background_color": {
            "text": "Night Mode Background color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode \.card *{[^}]*?background-color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "#272828",
        },
        "nm_cloze_color": {
            "text": "Night Mode Cloze color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode \.cloze.*{[^}]*?color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "#4297F9",
        },
        "nm_one_by_one_cloze_color": {
            "text": "Night Mode One-by-one Cloze Text color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode \.cloze.one-by-one.*{[^}]*?color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "#009400",
        },
        "nm_one_by_one_cloze_hint_color": {
            "text": "Night Mode One-by-one Cloze Hint color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode \.cloze-hint.*{[^}]*?color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "#009400",
        },
        "nm_extra_color": {
            "text": "Night Mode Extra color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode #extra.*{[^}]*?color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "magenta",
        },
        "nm_hint_color": {
            "text": "Night Mode Hint Reveal color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"\.night_mode \.hints *{[^}]*?color: (.+?)( +!important)?;",
            "section": "Colors",
            "default": "cyan",
        },
        "bold_text_color": {
            "text": "Bold Text color",
            "tooltip": "set to transparent for normal color",
            "type": "color",
            "file": "style",
            "regex": r"b *{[^}]*?color: (.+?)( +!important)?;",
            "with_inherit_option": True,
            "section": "Colors",
            "default": "inherit",
        },
        "underlined_text_color": {
            "text": "Underlined Text color",
            "tooltip": "set to transparent for normal color",
            "type": "color",
            "file": "style",
            "regex": r"u *{[^}]*?color: (.+?)( +!important)?;",
            "with_inherit_option": True,
            "section": "Colors",
            "default": "inherit",
        },
        "italic_text_color": {
            "text": "Italic Text color",
            "tooltip": "set to transparent for normal color",
            "type": "color",
            "file": "style",
            "regex": r"\n *i *{[^}]*?color: (.+?)( +!important)?;",
            "with_inherit_option": True,
            "section": "Colors",
            "default": "inherit",
        },
        "image_occlusion_rect_color": {
            "text": "Image Occlusion Rect Color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"--rect-bg: +([^ ]*?);",
            "section": "Colors",
            "default": "moccasin",
        },
        "image_occlusion_border_color": {
            "text": "Image Occlusion Rect Border Color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"--rect-border: +([^ ]*?);",
            "section": "Colors",
            "default": "olive",
        },
        "image_occlusion_active_rect_color": {
            "text": "Image Occlusion Active Rect Color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"--active-rect-bg: +([^ ]*?);",
            "section": "Colors",
            "default": "salmon",
        },
        "image_occlusion_active_border_color": {
            "text": "Image Occlusion Active Rect Border Color",
            "tooltip": "",
            "type": "color",
            "file": "style",
            "regex": r"--active-rect-border: +([^ ]*?);",
            "section": "Colors",
            "default": "yellow",
        },
        **{
            f"user_action_{i}": {
                "text": f"User Action {i}",
                "type": "useraction",
                "file": "back",
                "regex": f"var +userJs{i} += +([^/\\n]*)",
                "options": ANKIMOBILE_USER_ACTIONS,
                "labels": ANKIMOBILE_USER_ACTION_LABELS,
                "section": "AnkiMobile User Actions",
                "default": "undefined",
            }
            for i in range(1, 9)
        },
    }
)


def anking_notetype_names():
    return list(anking_notetype_templates().keys())


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
    result = json.loads(
        (ANKING_NOTETYPES_PATH / notetype_name / f"{notetype_name}.json").read_text()
    )
    front, back, styling = anking_notetype_templates()[notetype_name]
    result["tmpls"][0]["qfmt"] = front
    result["tmpls"][0]["afmt"] = back
    result["css"] = styling
    return result


def anking_notetype_models() -> List["NotetypeDict"]:
    return [anking_notetype_model(name) for name in anking_notetype_names()]


def notetype_base_name(model_name: str) -> str:
    """Returns the base name of a note type, that is if it's a version of a an anking note type
    it will return the base name, otherwise it will return the name itself."""
    return next(
        (
            notetype_base_name
            for notetype_base_name in anking_notetype_names()
            if re.match(rf"{notetype_base_name}($| |-)", model_name)
        ),
        None,
    )


def is_io_note_type(model_name: str) -> bool:
    "Return True if the given note type is an image occlusion type."
    return notetype_base_name(model_name) in ("IO-one by one", "Physeo-IO one by one")


def all_btns_setting_configs():
    result = OrderedDict()
    for notetype_name in anking_notetype_templates().keys():
        fields = configurable_fields_for_notetype(notetype_name)
        for field_name in fields:
            shortcut = btn_name_to_shortcut_odict(notetype_name).get(field_name, None)
            result.update(configurable_field_configs(field_name, shortcut))
        if "OME" in fields:
            result.update(
                {
                    "disable_ome_mobile": disable_mobile_ome_field_setting_config(
                        False
                    ),
                }
            )
    return result


def configurable_fields_for_notetype(notetype_name: str) -> List[str]:
    _, back, _ = anking_notetype_templates()[notetype_name]

    result = []
    for field in re.findall(CONDITIONAL_FIELD_RE(), back):
        if not re.search(CONFIGURABLE_FIELD_HAS_TO_CONTAIN_RE, field):
            continue

        name_patterns = [
            CONFIGURABLE_FIELD_NAME_RE,
            CONFIGURABLE_FIELD_FALLBACK_NAME_RE,
        ]
        for pattern in name_patterns:
            m = re.search(pattern, field)
            if m:
                result.append(m.group(1))
                break

    return result


def btn_name_to_shortcut_odict(notetype_name):
    _, back, _ = anking_notetype_templates()[notetype_name]

    button_shortcuts_dict_pattern = r"var+ ButtonShortcuts *= *{([^}]*)}"
    m = re.search(button_shortcuts_dict_pattern, back)
    if not m:
        return dict()

    result = OrderedDict()
    dict_key_value_pattern = r'"([^"]+)" *: *"([^"]*)"'
    button_shorcut_pairs = re.findall(dict_key_value_pattern, m.group(1))
    for btn_name, shortcut in button_shorcut_pairs:
        result[btn_name] = shortcut
    return result


def configurable_field_configs(
    name: str, default_shortcut_if_hint_button: Union[str, None]
) -> Dict:
    # if default_shortcut_if_hint_button is None, then this function assumes that
    # the configurable field is not a hint button
    name_in_snake_case = name.lower().replace(" ", "_")
    result = {
        f"disable_{name_in_snake_case}": disable_field_setting_config(name, False),
    }

    if default_shortcut_if_hint_button is not None:
        result.update(
            {
                f"btn_shortcut_{name_in_snake_case}": button_shortcut_setting_config(
                    name, default_shortcut_if_hint_button
                ),
                f"autoreveal_{name_in_snake_case}": button_auto_reveal_setting_config(
                    name, False
                ),
            }
        )

    return result


def button_shortcut_setting_config(field_name: str, default) -> Dict:
    return {
        "text": f"{field_name} Shortcut",
        "type": "shortcut",
        "file": "back",
        "regex": rf'var+ ButtonShortcuts *= *{{[^}}]*?"{field_name}" *: *"({QUOT_STR_RE}*?)"',
        "configurable_field_name": field_name,
        "section": "Hint Buttons",
        "default": default,
    }


def button_auto_reveal_setting_config(field_name, default):
    return {
        "text": f"Auto Reveal {field_name}",
        "type": "checkbox",
        "file": "back",
        "regex": rf'var+ ButtonAutoReveal *= *{{[^}}]*?"{field_name}" *: *(.+),\n',
        "configurable_field_name": field_name,
        "section": "Hint Buttons",
        "default": default,
    }


def disable_field_setting_config(field_name, default):
    return {
        "text": f"Disable {field_name} Field",
        "tooltip": "",
        "type": "wrap_checkbox",
        "file": "back",
        "regex": CONDITIONAL_FIELD_RE(field_name),
        "wrap_into": ("<!--", "-->"),
        "section": "Fields",
        "default": default,
    }


def disable_mobile_ome_field_setting_config(default):
    return {
        "text": "Disable OME Field (mobile)",
        "tooltip": "",
        "type": "wrap_checkbox",
        "file": "back",
        "regex": r"(<!--)?{{#OME}}\s*<span id=\"hint-ome[\w\W]+?{{/OME}}(-->)?",
        "wrap_into": ("<!--", "-->"),
        "section": "Fields",
        "default": default,
    }


setting_configs = OrderedDict(**setting_configs, **all_btns_setting_configs())

for setting_name, setting_config in setting_configs.items():
    setting_config["name"] = setting_name

# Settings that apply to multiple note types (the ones that have this setting listed in
# settings_by_notetype).
# They can be overwritten in the note types settings.
general_settings = [
    "toggle_next_button",
    "toggle_all_buttons",
    "autoscroll_to_button",
    "tags_toggle_shortcut",
    "tags_container",
    "tags_container_mobile",
    "reveal_cloze_shortcut",
    "tags_num_levels_to_show_front",
    "tags_num_levels_to_show_back",
    "toggle_all_clozes_shortcut",
    "reveal_next_cloze_mode",
    "cloze_hider",
    "always_one_by_one",
    "selective_one_by_one",
    "min_number_of_clozes_fo_one_by_one",
    "timer",
    "timer_secs",
    "timer_minutes",
    "autoflip",
    "front_tts",
    "front_tts_speed",
    "back_tts",
    "back_tts_speed",
    "front_signal_tag",
    "back_signal_tag",
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
    "image_occlusion_rect_color",
    "image_occlusion_border_color",
    "image_occlusion_active_rect_color",
    "image_occlusion_active_border_color",
    *[f"user_action_{i}" for i in range(1, 9)],
]


def general_settings_defaults_dict():
    result = dict()
    for setting_name in general_settings:
        result[setting_name] = setting_configs[setting_name]["default"]
    return result
