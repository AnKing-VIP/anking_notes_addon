import json
import re
from os.path import dirname, realpath
from pathlib import Path
from typing import Any, List, Optional, Tuple

from aqt import mw
from aqt.editor import Editor, EditorWebView
from aqt.gui_hooks import (
    editor_did_init_buttons,
    editor_did_init_shortcuts,
    editor_did_load_note,
    editor_will_load_note,
    editor_will_munge_html,
    editor_will_show_context_menu,
    webview_did_receive_js_message,
    webview_will_set_content,
)
from aqt.qt import QAction, QKeySequence, QMenu, QUrl, qconnect, qtmajor
from aqt.utils import shortcut, showInfo
from bs4 import BeautifulSoup

from .notetype_setting_definitions import is_io_note_type

occlude_shortcut = "Ctrl+Shift+O"
occlusion_behavior = "autopaste"


def get_base_top(editor, prefix: str, suffix: str) -> int:
    matches = []
    query = re.escape(prefix) + r"(\d+)" + re.escape(suffix)

    for _name, item in editor.note.items():
        matches.extend(re.findall(query, item))

    values = [0]
    values.extend([int(x) for x in matches])

    return max(values)


def get_top_index(editor, prefix: str, suffix: str) -> int:
    base_top = get_base_top(editor, prefix, suffix)

    return base_top + 1 if base_top == 0 else base_top


def get_incremented_index(editor, prefix: str, suffix: str) -> int:
    base_top = get_base_top(editor, prefix, suffix)

    return base_top + 1


def activate_matching_field(indexer):
    def get_value(editor, prefix: str, suffix: str) -> int:
        current_index = indexer(editor, prefix, suffix)
        was_filled = activate_matching_fields(editor, [current_index])[0]

        return current_index if was_filled else 0

    return get_value


def no_index(_editor, _prefix: str, _suffix: str) -> str:
    return ""


def top_index(type_):
    if type_ == "free":
        return get_top_index
    elif type_ == "flashcard":
        return activate_matching_field(get_top_index)
    else:  # type_ == "none":
        return no_index


def incremented_index(type_):
    if type_ == "free":
        return get_incremented_index
    elif type_ == "flashcard":
        return activate_matching_field(get_incremented_index)
    else:  # type_ == "none":
        return no_index


def is_text_empty(editor, text) -> bool:
    return editor.mungeHTML(text) == ""


def escape_js_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")


def make_insertion_js(field_index: int, text: str) -> str:
    escaped = escape_js_text(text)

    cmd = (
        f"pycmd(`key:{field_index}:${{getNoteId()}}:{escaped}`); "
        f"EditorIO.setFieldHTML({field_index}, `{escaped}`); "
    )
    return cmd


def insert_into_zero_indexed(editor, text: str) -> None:
    for index, (name, _item) in enumerate(editor.note.items()):
        match = re.search(r"\d+$", name)

        if not match or int(match[0]) != 0:
            continue

        editor.web.eval(f"EditorIO.insertIntoZeroIndexed(`{text}`, {index}); ")
        break


def activate_matching_fields(editor, indices: List[int]) -> List[bool]:
    founds = [False for index in indices]

    for index, (name, item) in enumerate(editor.note.items()):
        match = re.search(r"\d+$", name)

        if not match:
            continue

        matched = int(match[0])

        if matched not in indices:
            continue

        founds[indices.index(matched)] = True

        if not is_text_empty(editor, item):
            continue

        editor.web.eval(make_insertion_js(index, "active"))

    return founds


def include_closet_code(webcontent, context) -> None:
    if not isinstance(context, Editor):
        return

    addon_package = mw.addonManager.addonFromModule(__name__)
    webcontent.css.append(f"/_addons/{addon_package}/web/editor.css")
    webcontent.js.append(f"/_addons/{addon_package}/web/editor.js")


def process_occlusion_index_text(index_text: str) -> List[int]:
    return [] if len(index_text) == 0 else [int(text) for text in index_text.split(",")]


old_occlusion_indices = []
occlusion_editor_active = False


def add_occlusion_messages(
    handled: Tuple[bool, Any], message: str, context
) -> Tuple[bool, Any]:
    if isinstance(context, Editor):
        editor: Editor = context
        global old_occlusion_indices, occlusion_editor_active  # pylint: disable=global-statement
        if message.startswith("ankingOldOcclusions"):
            _, _src, index_text = message.split(":", 2)
            old_occlusion_indices = process_occlusion_index_text(index_text)

            return (True, None)

        elif message.startswith("ankingNewOcclusions"):
            _, _src, index_text = message.split(":", 2)
            indices = process_occlusion_index_text(index_text)

            fill_indices = list(set(indices).difference(set(old_occlusion_indices)))
            could_fill = activate_matching_fields(editor, fill_indices)

            return (True, could_fill)

        elif message.startswith("ankingOcclusionText"):
            text = message.split(":", 1)[1]

            if occlusion_behavior == "autopaste":
                insert_into_zero_indexed(editor, text)
            else:  # occlusion_behavior == 'copy':
                mw.app.clipboard().setText(text)

            return (True, None)

        elif message == "ankingOcclusionEditorActive":
            occlusion_editor_active = True
            return (True, None)

        elif message == "ankingOcclusionEditorInactive":
            occlusion_editor_active = False
            return (True, None)

        elif message.startswith("ankingClosetRefocus"):
            refocus(editor)
            return (True, None)

        elif message.startswith("ankingClosetMultipleImages"):
            showInfo("Cannot start occlusion editor if field contains multiple images.")
            return (True, None)

    return handled


# code 0 field is optional
trailing_number = re.compile(r"[123456789]\d*$")


def get_max_code_field(editor) -> int:
    number_suffixes = map(
        lambda item: trailing_number.search(item[0]), editor.note.items()
    )
    indices = [suffix[0] for suffix in number_suffixes if suffix]
    sorted_indices = sorted(set([int(index) for index in indices]))

    max = 0
    for index, value in enumerate(sorted_indices):
        # probably skipped an index
        if value != index + 1:
            break

        max = value

    return max


def anking_io_js_filename() -> Optional[str]:
    path = next((Path(__file__).parent / "resources").glob("__ankingio-*.js"), None)
    if not path:
        return None
    return path.name


def toggle_occlusion_mode(editor):
    model = editor.note.note_type()

    if not is_io_note_type(model["name"]):
        showInfo("Please choose an AnKing image occlusion note type")
        editor.web.eval("EditorIO.setInactive()")
        return

    addon_package = mw.addonManager.addonFromModule(__name__)
    js_path = json.dumps(f"_addons/{addon_package}/resources/{anking_io_js_filename()}")
    max_code_fields = get_max_code_field(editor)

    if not mw.focusWidget() is editor:
        refocus(editor)

    editor.web.eval(f"EditorIO.toggleOcclusionMode({js_path}, {max_code_fields})")


def add_occlusion_button(buttons, editor):
    file_path = dirname(realpath(__file__))
    icon_path = Path(file_path, "icons", "occlude.png")

    shortcut_as_text = shortcut(QKeySequence(occlude_shortcut).toString())

    occlusion_button = editor._addButton(  # pylint: disable=protected-access
        str(icon_path.absolute()),
        "anking_occlude",
        f"Put all fields into occlusion mode ({shortcut_as_text})",
        id="ankingOcclude",
        disables=False,
    )

    editor._links[  # pylint: disable=protected-access
        "anking_occlude"
    ] = toggle_occlusion_mode
    buttons.insert(-1, occlusion_button)


def wrap_as_option(name: str, code: str, tooltip: str, shortcut_text: str) -> str:
    return f'<option title="{tooltip} ({shortcut(shortcut_text)})">{name} [{code}]</option>'


def add_buttons(buttons, editor):
    global occlusion_editor_active  # pylint: disable=global-statement
    occlusion_editor_active = False

    add_occlusion_button(buttons, editor)


def add_occlusion_shortcut(cuts, editor):
    cuts.append((occlude_shortcut, lambda: toggle_occlusion_mode(editor), True))


occlusion_container_pattern = re.compile(
    # remove trailing <br> to prevent accumulation
    r'<div class="anking-occlusion-container">.*?(<img.*?>).*?</div>(<br>)*'
)


def remove_occlusion_code(txt: str, _editor) -> str:
    if match := re.search(occlusion_container_pattern, txt):
        rawImage = match[1]

        return re.sub(occlusion_container_pattern, rawImage, txt)

    return txt


def clear_occlusion_mode(js, _note, _editor):
    return f"EditorIO.clearOcclusionMode().then(() => {{ {js} }}); "


def refocus(editor):
    editor.web.setFocus()
    editor.web.eval("EditorIO.refocus(); ")


def maybe_refocus(editor):
    editor.web.eval("EditorIO.maybeRefocus(); ")


def on_editor_will_show_context_menu(webview: EditorWebView, menu: QMenu) -> None:
    def on_blur_image() -> None:
        editor = webview.editor
        url = data.mediaUrl()
        if url.matches(QUrl(mw.serverURL()), QUrl.UrlFormattingOption.RemovePath):
            src = url.path().strip("/")
        else:
            src = url.toString()
        field = editor.note.fields[editor.currentField]
        soup = BeautifulSoup(field, "html.parser")
        for img in soup("img"):
            if img.get("src", "").strip("/") != src:
                continue
            classes = img.get("class", [])
            if "blur" in classes:
                classes.remove("blur")
            else:
                classes.append("blur")
            if classes:
                img["class"] = classes
            elif "class" in img.attrs:
                del img["class"]
        editor.note.fields[editor.currentField] = soup.decode_contents()
        editor.loadNoteKeepingFocus()

    if qtmajor >= 6:
        data = webview.lastContextMenuRequest()  # type: ignore
    else:
        data = webview.page().contextMenuData()
    if data.mediaUrl().isValid():
        blur_image_action = QAction("AnKing Notetypes: Blur/Unblur Image", menu)
        qconnect(blur_image_action.triggered, on_blur_image)
        menu.addAction(blur_image_action)


def init():
    webview_will_set_content.append(include_closet_code)
    webview_did_receive_js_message.append(add_occlusion_messages)
    editor_did_init_buttons.append(add_buttons)
    editor_did_init_shortcuts.append(add_occlusion_shortcut)
    editor_will_load_note.append(clear_occlusion_mode)
    editor_did_load_note.append(maybe_refocus)
    editor_will_munge_html.append(remove_occlusion_code)
    editor_will_show_context_menu.append(on_editor_will_show_context_menu)
    mw.addonManager.setWebExports(__name__, r"(web|resources)/.*(css|js)")
