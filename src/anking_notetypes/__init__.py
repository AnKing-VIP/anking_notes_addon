from concurrent.futures import Future
from pathlib import Path
from typing import TYPE_CHECKING, List, Sequence

if TYPE_CHECKING:
    from anki.notes import Note, NoteId

from anki.utils import ids2str
from aqt import mw
from aqt.browser import Browser
from aqt.gui_hooks import (
    browser_will_show_context_menu,
    card_layout_will_show,
    profile_did_open,
)
from aqt.qt import QMenu, QPushButton
from aqt.utils import askUserDialog, tooltip

from . import editor
from .compat import add_compat_aliases
from .gui.config_window import (
    NotetypesConfigWindow,
    models_with_available_updates,
    note_type_version,
)
from .gui.menu import setup_menu
from .gui.utils import choose_subset
from .notetype_setting_definitions import (
    HINT_BUTTONS,
    anking_notetype_models,
)

ADDON_DIR_NAME = str(Path(__file__).parent.name)
RESOURCES_PATH = Path(__file__).parent / "resources"


def setup():
    add_compat_aliases()

    setup_menu(open_window)

    card_layout_will_show.append(add_button_to_clayout)

    replace_default_addon_config_action()

    profile_did_open.append(on_profile_did_open)

    browser_will_show_context_menu.append(on_browser_will_show_context_menu)

    editor.init()


def on_profile_did_open():
    copy_resources_into_media_folder()

    maybe_show_notetypes_update_notice()


def open_window():
    window = NotetypesConfigWindow()
    window.open()


def add_button_to_clayout(clayout):
    button = QPushButton()
    button.setAutoDefault(False)
    button.setText("Configure AnKing notetypes")

    def open_window_with_clayout():
        window = NotetypesConfigWindow(clayout)
        window.open()

    button.clicked.connect(open_window_with_clayout)
    clayout.buttons.insertWidget(1, button)


def maybe_show_notetypes_update_notice():
    # can happen when restoring data from backup
    if not mw.col:
        return

    models_with_updates = models_with_available_updates()
    if not models_with_updates:
        return

    # Return early if user was already notified about this version (and didn't choose "Remind me later")
    latest_version = note_type_version(anking_notetype_models()[0])
    conf = mw.addonManager.getConfig(ADDON_DIR_NAME)
    if latest_version == conf.get("latest_notified_note_type_version"):
        return

    answer = askUserDialog(
        title="AnKing note types update",
        text="New versions of the AnKing note types are available! \nYou can choose to update them in the "
        "AnKing Note Types dialog. Open the dialog now?",
        buttons=reversed(["Yes", "No", "Remind me later"]),
    ).run()
    if answer == "Yes":
        conf["latest_notified_note_type_version"] = latest_version
        mw.addonManager.writeConfig(ADDON_DIR_NAME, conf)
        open_window()
    elif answer == "No":
        conf["latest_notified_note_type_version"] = latest_version
        mw.addonManager.writeConfig(ADDON_DIR_NAME, conf)
    elif answer == "Remind me later":
        # Don't update the config, so the user will be asked again next time
        pass


def copy_resources_into_media_folder():
    # add recources of all notetypes to collection media folder
    for file in Path(RESOURCES_PATH).iterdir():
        if not mw.col.media.have(file.name):
            mw.col.media.add_file(str(file.absolute()))


def replace_default_addon_config_action():
    mw.addonManager.setConfigAction(ADDON_DIR_NAME, open_window)


def hint_fields_for_nids(nids: Sequence["NoteId"]) -> List[str]:
    all_fields = mw.col.db.list(
        "select distinct name from fields where ntid in (select distinct mid from notes where id in %s)"
        % ids2str(nids)
    )
    hint_fields = []
    for field in all_fields:
        if field in HINT_BUTTONS.values():
            hint_fields.append(field)
    return hint_fields


def note_autoopen_fields(note: "Note") -> List[str]:
    tags = []
    prefix = "autoopen::"
    for tag in note.tags:
        if tag.startswith(prefix):
            tags.append(tag[tag.index(prefix) + len(prefix) :].replace("_", " "))
    return tags


def on_auto_reveal_fields_action(
    browser: Browser, selected_nids: Sequence["NoteId"]
) -> None:
    fields = hint_fields_for_nids(selected_nids)
    if not fields:
        tooltip("No hint fields found in the selected notes.", parent=browser)
        return
    current = (
        note_autoopen_fields(mw.col.get_note(selected_nids[0]))
        if len(selected_nids) == 1
        else []
    )
    chosen = choose_subset(
        "Choose which fields of the selected notes should be automatically revealed<br>",
        choices=fields,
        current=current,
        description_html="This will modify the autoopen::field_name tags of the notes.",
        parent=browser,
    )
    if chosen is None:
        return
    autoopen_tags = []
    for field in chosen:
        autoopen_tags.append(f"autoopen::{field.lower().replace(' ', '_')}")

    def task() -> None:
        notes = []
        for nid in selected_nids:
            note = mw.col.get_note(nid)
            notes.append(note)
            new_tags = []
            for tag in note.tags:
                if not tag.startswith("autoopen::"):
                    new_tags.append(tag)
            new_tags.extend(autoopen_tags)
            note.tags = new_tags
            note.flush()

    def on_done(fut: Future) -> None:
        mw.progress.finish()
        browser.onReset()
        fut.result()

    mw.progress.start(label="Updating notes...", immediate=True)
    mw.taskman.run_in_background(task, on_done)


def on_browser_will_show_context_menu(browser: Browser, context_menu: QMenu) -> None:
    selected_nids = browser.selectedNotes()
    action = context_menu.addAction(
        "AnKing Notetypes: Auto-reveal fields",
        lambda: on_auto_reveal_fields_action(browser, selected_nids),
    )
    context_menu.addAction(action)
    if not selected_nids:
        action.setDisabled(True)


if mw is not None:
    setup()
