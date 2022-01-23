from pathlib import Path

from aqt import mw
from aqt.gui_hooks import card_layout_will_show, profile_did_open
from aqt.qt import *
from aqt.utils import askUserDialog

from .compat import add_compat_aliases
from .config_window import NotetypesConfigWindow
from .gui.menu import setup_menu

addon_dir_name = str(Path(__file__).parent.name)


def open_window():
    window = NotetypesConfigWindow()
    window.open()


if mw is not None:
    setup_menu(open_window)


def add_button_to_clayout(clayout):
    button = QPushButton()
    button.setAutoDefault(False)
    button.setText("Configure AnKing notetypes")

    def open_window_with_clayout():
        window = NotetypesConfigWindow(clayout)
        window.open()

    button.clicked.connect(open_window_with_clayout)
    clayout.buttons.insertWidget(1, button)


card_layout_will_show.append(add_button_to_clayout)


def maybe_show_notetypes_update_notice():
    models_with_available_updates = (
        NotetypesConfigWindow.models_with_available_updates()
    )
    if not models_with_available_updates:
        return

    conf = mw.addonManager.getConfig(addon_dir_name)
    latest_notice_version = conf.get("latest_notified_note_type_version")
    if all(
        NotetypesConfigWindow.model_version(model) == latest_notice_version
        for model in models_with_available_updates
    ):
        return

    conf["latest_notified_note_type_version"] = NotetypesConfigWindow.model_version(
        models_with_available_updates[0]
    )

    answer = askUserDialog(
        title="AnKing note types update",
        text="New versions of the AnKing note types are available! \nYou can choose to update them in the AnKing Note Types dialog. Open the dialog now?",
        buttons=reversed(["Yes", "No", "Remind me later"]),
    ).run()
    if answer == "Yes":
        mw.addonManager.writeConfig(addon_dir_name, conf)
        open_window()
    elif answer == "No":
        mw.addonManager.writeConfig(addon_dir_name, conf)
    elif answer == "Remind me later":
        pass


profile_did_open.append(maybe_show_notetypes_update_notice)

add_compat_aliases()
