from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from anki.models import NotetypeDict
from aqt import mw
from aqt.clayout import CardLayout
from aqt.utils import askUser, showInfo, tooltip
from PyQt5.QtCore import *  # type: ignore
from PyQt5.QtGui import *  # type: ignore
from PyQt5.QtWidgets import *

from .ankiaddonconfig import ConfigManager, ConfigWindow
from .ankiaddonconfig.window import ConfigLayout
from .gui.anking_widgets import AnkingIconsLayout, AnkiPalaceLayout
from .notetype_setting import NotetypeParseException, NotetypeSetting
from .notetype_setting_definitions import (
    anking_notetype_names,
    anking_notetype_templates,
    btn_name_to_shortcut_odict,
    general_settings,
    general_settings_defaults_dict,
    setting_configs,
)

# contains the last opened config window
window: Optional[ConfigWindow] = None


def notetype_settings_tab(
    notetype_name: str,
    model: Optional["NotetypeDict"],
    clayout: CardLayout,
) -> Callable:
    def tab(window: ConfigWindow):
        tab = window.add_tab(notetype_name)

        if model:
            ntss = ntss_for_model(model)
            ordered_ntss = adjust_hint_button_nts_order(ntss, notetype_name)
            scroll = tab.scroll_layout()
            add_nts_widgets_to_layout(scroll, ordered_ntss, notetype_name)
            scroll.stretch()
            tab.button(
                "Reset",
                on_click=lambda: reset_notetype_and_reload_ui(model, window, clayout),
            )
        else:
            tab.text("The notetype is not in the collection.")
            tab.stretch()

            # TODO implement importing of notetypes
            tab.button(
                "Import",
                on_click=lambda: showInfo("Not implemented yet"),
            )

    return tab


def reset_notetype_and_reload_ui(
    model: NotetypeDict, window: ConfigWindow, clayout: CardLayout
):
    notetype_name = model["name"]
    if askUser(
        f"Do you really want to reset the <b>{notetype_name}</b> notetype to its default form?",
        defaultno=True,
    ):
        front, back, styling = anking_notetype_templates()[notetype_name]
        model["tmpls"][0]["qfmt"] = front
        model["tmpls"][0]["afmt"] = back
        model["css"] = styling

        if not clayout:
            mw.col.models.update_dict(model)

        read_in_settings_from_notetypes(window.conf)

        if clayout:
            read_in_settings_from_clayout_model(window.conf, clayout)

        window.update_widgets()

        tooltip("Notetype was reset", parent=window, period=1200)


def general_tab() -> Callable:

    ntss = general_ntss()

    def tab(window: ConfigWindow):
        tab = window.add_tab("General")

        scroll = tab.scroll_layout()
        add_nts_widgets_to_layout(scroll, ntss, None, general=True)
        scroll.stretch()

        for nts in ntss:
            nts.register_general_setting(tab.conf)

        tab.space(10)
        tab.text(
            "Changes made here will be applied to all notetypes that have this setting",
            bold=True,
            multiline=True,
        )

    return tab


def add_nts_widgets_to_layout(
    layout: ConfigLayout, ntss: List[NotetypeSetting], notetype_name: str, general=False
) -> None:

    if general:
        assert notetype_name == None

    nts_to_section = {
        nts: section_name
        for nts in ntss
        if (section_name := nts.config.get("section", None))
    }

    section_to_ntss: Dict[str, List[NotetypeSetting]] = defaultdict(lambda: [])
    for nts, section in nts_to_section.items():
        section_to_ntss[section].append(nts)

    for section_name, section_ntss in sorted(section_to_ntss.items()):
        section = layout.collapsible_section(section_name)
        for nts in section_ntss:
            if general:
                nts.add_widget_to_general_config_layout(section)
            else:
                nts.add_widget_to_config_layout(section, notetype_name)
            section.space(7)
        layout.hseparator()
        layout.space(10)

    other_ntss: List[NotetypeSetting] = [
        nts for nts in ntss if nts not in nts_to_section.keys()
    ]
    for nts in other_ntss:
        if general:
            nts.add_widget_to_general_config_layout(layout)
        else:
            nts.add_widget_to_config_layout(layout, notetype_name)
        layout.space(7)


def change_window_settings(window: ConfigWindow, clayout=None):
    window.setWindowTitle("AnKing note types")
    window.setMinimumHeight(500)
    window.setMinimumWidth(500)

    # hide reset and advanced buttons
    window.reset_btn.hide()
    window.advanced_btn.hide()

    if clayout:
        # hide save button in live preview (notetype manager) mode
        # because changes are saved using the save button of the notetype manager window
        window.save_btn.hide()
    else:
        # overwrite on_save function
        def on_save(window: ConfigWindow):
            update_notetypes(window.conf)
            window.close()

        window.save_btn.clicked.disconnect()  # type: ignore
        window.save_btn.clicked.connect(lambda: on_save(window))  # type: ignore

    if clayout:
        change_tab_to_current_notetype(window, clayout)

    # add anking links layouts
    widget = QWidget()
    window.main_layout.insertWidget(0, widget)
    AnkingIconsLayout(widget)

    widget = QWidget()
    window.main_layout.addWidget(widget)
    AnkiPalaceLayout(widget)


def change_tab_to_current_notetype(
    window: ConfigWindow,
    clayout: CardLayout,
) -> None:
    notetype_name = clayout.model["name"]
    tab_widget = window.main_tab

    def get_tab_by_name(tab_name):
        return next(
            (
                index
                for index in range(tab_widget.count())
                if tab_name == tab_widget.tabText(index)
            ),
            None,
        )

    tab_widget.setCurrentIndex(get_tab_by_name(notetype_name))


def ntss_for_model(model: "NotetypeDict") -> List[NotetypeSetting]:
    # returns all nts that are present on the notetype
    result = []
    for setting_config in setting_configs.values():
        nts = NotetypeSetting.from_config(setting_config)
        if nts.is_present(model):
            result.append(nts)

    return result


def adjust_hint_button_nts_order(
    ntss: List[NotetypeSetting], notetype_name: str
) -> List[NotetypeSetting]:
    # adjusts the order of the hint button settings to be the same as
    # on the original anking card
    # it would probably be better to check the order of the buttons on the current
    # version of the card, not the original one

    hint_button_ntss = [
        nts for nts in ntss if nts.config.get("hint_button_setting", False)
    ]
    ordered_btn_names = list(btn_name_to_shortcut_odict(notetype_name).keys())
    ordered_hint_button_ntss = sorted(
        hint_button_ntss,
        key=lambda nts: (
            ordered_btn_names.index(name)
            if (name := nts.config["hint_button_setting"]) in ordered_btn_names
            else -1  # can happen because of different quotes in template versions
        ),
    )

    other_ntss = [nts for nts in ntss if nts not in hint_button_ntss]
    return ordered_hint_button_ntss + other_ntss


def general_ntss() -> List[NotetypeSetting]:
    result = []
    for setting_name in general_settings:
        result.append(NotetypeSetting.from_config(setting_configs[setting_name]))
    return result


def safe_update_model(ntss: List[NotetypeSetting], model, conf: ConfigManager):
    result = model.copy()
    parse_exception = None
    for nts in ntss:
        try:
            result = nts.updated_model(result, result["name"], conf)
        except NotetypeParseException as e:
            parse_exception = e
    if parse_exception:
        tooltip(f"failed parsing notetype:\n{str(parse_exception)}")

    return result


def read_in_settings_from_notetypes(conf: ConfigManager):
    error_msg = ""
    for notetype_name in anking_notetype_names():
        model = mw.col.models.by_name(notetype_name)
        if not model:
            continue
        for nts in ntss_for_model(model):
            try:
                conf[nts.key(notetype_name)] = nts.setting_value(model)
            except NotetypeParseException as e:
                error_msg += f"failed parsing notetype:\n{str(e)}\n\n"

    if error_msg:
        showInfo(error_msg)


def read_in_general_settings(conf: ConfigManager):
    for key, value in general_settings_defaults_dict().items():
        conf[f"general.{key}"] = value


def read_in_settings_from_clayout_model(conf: ConfigManager, clayout: CardLayout):
    notetype_name = clayout.model["name"]
    for nts in ntss_for_model(clayout.model):
        conf[nts.key(notetype_name)] = nts.setting_value(clayout.model)


def update_notetypes(conf: ConfigManager):
    for notetype_name in anking_notetype_names():
        model = mw.col.models.by_name(notetype_name)
        if not model:
            continue
        ntss = ntss_for_model(model)
        model = safe_update_model(ntss, model, conf)
        mw.col.models.update_dict(model)


def open_config_window(clayout_: CardLayout = None):
    global window

    # dont open another window if one is already open
    if window:
        is_open = True
        # when the window is closed c++ deletes the qdialog and calling methods
        # of the window fails with a RuntimeError
        try:
            window.isVisible()
        except RuntimeError:
            is_open = False

        if is_open:
            window.setWindowState(Qt.WindowState.WindowActive)
            return

    # ankiaddonconfig's ConfigManager is used here in a way that is not intended
    # the save functionality gets overwritten and nothing gets saved to the Anki
    # addon config
    # the config is populated at the start with the current setting values parsed
    # from the notetype and then used to update the settings
    conf = ConfigManager()

    # read in settings from notetypes and general ones into config
    read_in_settings_from_notetypes(conf)
    read_in_general_settings(conf)

    # code after this assumes that if bool(clayout) is true, clayout.model contains
    # an anking notetype model
    clayout = None
    if clayout_ and clayout_.model["name"] in anking_notetype_names():
        clayout = clayout_

    # if in live preview mode read in current not confirmed settings
    if clayout:
        read_in_settings_from_clayout_model(conf, clayout)

    # add general tab
    conf.add_config_tab(general_tab())

    # setup tabs for all notetypes
    for notetype_name in sorted(anking_notetype_names()):
        if clayout and clayout.model["name"] == notetype_name:
            model = clayout.model
        else:
            model = mw.col.models.by_name(notetype_name)
        conf.add_config_tab(notetype_settings_tab(notetype_name, model, clayout))

    # setup live update of clayout model on changes
    def update_clayout_model(key: str, _: Any):
        model = clayout.model
        notetype_name, setting_name = key.split(".")
        if notetype_name != clayout.model["name"]:
            return

        nts = NotetypeSetting.from_config(setting_configs[setting_name])
        model = safe_update_model([nts], model, conf)

        clayout.model = model
        clayout.change_tracker.mark_basic()
        clayout.update_current_ordinal_and_redraw(clayout.ord)

    if clayout:
        conf.on_change(update_clayout_model)

    # change window settings, overwrite on_save, setup notetype updates
    conf.on_window_open(lambda window: change_window_settings(window, clayout=clayout))

    # open the config window
    if clayout:
        window = conf.open_config(clayout)
    else:
        window = conf.open_config()
