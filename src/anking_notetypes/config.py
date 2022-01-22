import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from aqt import mw
from aqt.clayout import CardLayout
from aqt.qt import *
from aqt.utils import askUser, showInfo, tooltip

from .ankiaddonconfig import ConfigManager, ConfigWindow
from .ankiaddonconfig.window import ConfigLayout
from .gui.anking_widgets import AnkingIconsLayout, AnkiPalaceLayout, GithubLinkLayout
from .notetype_setting import NotetypeParseException, NotetypeSetting
from .notetype_setting_definitions import (
    anking_notetype_model,
    anking_notetype_names,
    btn_name_to_shortcut_odict,
    general_settings,
    general_settings_defaults_dict,
    setting_configs,
)

try:
    from anki.models import NotetypeDict  # type: ignore
except:
    pass

RESOURCES_PATH = Path(__file__).parent / "resources"


def ntss_for_model(model: "NotetypeDict") -> List[NotetypeSetting]:

    # returns all nts that are present on the notetype
    result = []
    for setting_config in setting_configs.values():
        nts = NotetypeSetting.from_config(setting_config)
        if nts.is_present(model):
            result.append(nts)

    return result


def general_ntss() -> List[NotetypeSetting]:
    result = []
    for setting_name in general_settings:
        result.append(NotetypeSetting.from_config(setting_configs[setting_name]))
    return result


class NotetypesConfigWindow:

    window: Optional[ConfigWindow] = None

    def __init__(self, clayout_: CardLayout = None):

        # code in this class assumes that if bool(clayout) is true, clayout.model contains
        # an anking notetype model
        self.clayout = None
        if clayout_ and clayout_.model["name"] in anking_notetype_names():
            self.clayout = clayout_

        self.conf = None

    def open(self):

        # dont open another window if one is already open
        if self.window:
            is_open = True
            # when the window is closed c++ deletes the qdialog and calling methods
            # of the window fails with a RuntimeError
            try:
                self.window.isVisible()
            except RuntimeError:
                is_open = False

            if is_open:
                self.window.activateWindow()
                self.window.raise_()
                return

        # ankiaddonconfig's ConfigManager is used here in a way that is not intended
        # the save functionality gets overwritten and nothing gets saved to the Anki
        # addon config
        # the config is populated at the start with the current setting values parsed
        # from the notetype and then used to update the settings
        self.conf = ConfigManager()

        self._read_in_settings()

        # add general tab
        self.conf.add_config_tab(lambda window: self._general_tab(window))

        # setup tabs for all notetypes
        for notetype_name in sorted(anking_notetype_names()):
            self.conf.add_config_tab(
                lambda window, notetype_name=notetype_name: self._notetype_settings_tab(
                    notetype_name, window
                )
            )

        # setup live update of clayout model on changes
        def update_clayout_model(key: str, _: Any):
            model = self.clayout.model
            notetype_name, setting_name = key.split(".")
            if notetype_name != self.clayout.model["name"]:
                return

            nts = NotetypeSetting.from_config(setting_configs[setting_name])
            model = self._safe_update_model([nts], model)

            scroll_bar = self.clayout.tform.edit_area.verticalScrollBar()
            scroll_pos = scroll_bar.value()
            self.clayout.model = model
            self.clayout.change_tracker.mark_basic()
            self.clayout.update_current_ordinal_and_redraw(self.clayout.ord)
            scroll_bar.setValue(min(scroll_pos, scroll_bar.maximum()))

        if self.clayout:
            self.conf.on_change(update_clayout_model)

        # change window settings, overwrite on_save, setup notetype updates
        self.conf.on_window_open(self._setup_window_settings)

        # open the config window
        if self.clayout:
            self.window = self.conf.open_config(self.clayout)
        else:
            self.window = self.conf.open_config()

    def _setup_window_settings(self, window: ConfigWindow):
        self.window = window
        window.setWindowTitle("AnKing Note Types")
        window.setMinimumHeight(500)
        window.setMinimumWidth(500)

        # hide reset and advanced buttons
        window.reset_btn.hide()
        window.advanced_btn.hide()

        if self.clayout:
            # hide save button in live preview (notetype manager) mode
            # because changes are saved using the save button of the notetype manager window
            window.save_btn.hide()
        else:
            # overwrite on_save function
            def on_save(window: ConfigWindow):
                self._update_notetypes()
                window.close()

            window.save_btn.clicked.disconnect()  # type: ignore
            window.save_btn.clicked.connect(lambda: on_save(window))  # type: ignore

        if self.clayout:
            self._set_active_tab(self.clayout.model["name"])

        # add anking links layouts
        widget = QWidget()
        window.main_layout.insertWidget(0, widget)
        AnkingIconsLayout(widget)

        widget = QWidget()
        window.main_layout.addWidget(widget)
        AnkiPalaceLayout(widget)

        window.main_layout.addSpacing(10)
        widget = QWidget()
        window.main_layout.addWidget(widget)
        GithubLinkLayout(
            widget, href="https://github.com/AnKingMed/AnKing-Note-Types/issues"
        )

    # tabs and NotetypeSettings (ntss)
    def _notetype_settings_tab(
        self,
        notetype_name: str,
        window: ConfigWindow,
    ):
        if self.clayout and self.clayout.model["name"] == notetype_name:
            model = self.clayout.model
        else:
            model = mw.col.models.by_name(notetype_name)  # type: ignore

        tab = window.add_tab(notetype_name)

        if model:
            ntss = ntss_for_model(model)
            ordered_ntss = self._adjust_hint_button_nts_order(ntss, notetype_name)
            scroll = tab.scroll_layout()
            self._add_nts_widgets_to_layout(scroll, ordered_ntss, model)
            scroll.stretch()
            tab.button(
                "Reset",
                on_click=lambda: self._reset_notetype_and_reload_ui(model),
            )
        else:
            tab.text("The notetype is not in the collection.")
            tab.stretch()

            tab.button(
                "Import",
                on_click=lambda: self._import_notetype_and_reload_tab(notetype_name),
            )

    def _general_tab(self, window: ConfigWindow):
        tab = window.add_tab("General")

        ntss = general_ntss()

        scroll = tab.scroll_layout()
        self._add_nts_widgets_to_layout(scroll, ntss, None, general=True)
        scroll.stretch()

        for nts in ntss:
            nts.register_general_setting(tab.conf)

        tab.space(10)
        tab.text(
            "Changes made here will be applied to all notetypes that have this setting",
            bold=True,
            multiline=True,
        )

    def _add_nts_widgets_to_layout(
        self,
        layout: ConfigLayout,
        ntss: List[NotetypeSetting],
        model: "NotetypeDict",
        general=False,
    ) -> None:

        if general:
            assert model is None

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
                    nts.add_widget_to_config_layout(section, model)
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
                nts.add_widget_to_config_layout(layout, model)
            layout.space(7)

    def _adjust_hint_button_nts_order(
        self, ntss: List[NotetypeSetting], notetype_name: str
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
        return other_ntss + ordered_hint_button_ntss

    # miscellanous
    def _set_active_tab(self, tab_name: str) -> None:
        tab_widget = self.window.main_tab
        tab_widget.setCurrentIndex(self._get_tab_idx_by_name(tab_name))

    def _reset_notetype_and_reload_ui(self, model: "NotetypeDict"):
        notetype_name = model["name"]
        if askUser(
            f"Do you really want to reset the <b>{notetype_name}</b> notetype to its default form?",
            defaultno=True,
        ):
            new_model = anking_notetype_model(notetype_name)

            new_model["id"] = model["id"]
            new_model["mod"] = int(time.time())  # not sure if this is needed
            new_model = self._adjust_field_ords(model, new_model)

            if not self.clayout:
                mw.col.models.update_dict(new_model)  # type: ignore
            else:
                model.update(new_model)

            self._reload_tab(notetype_name)

            tooltip("Notetype was reset", parent=self.window, period=1200)

    def _adjust_field_ords(
        self, cur_model: "NotetypeDict", new_model: "NotetypeDict"
    ) -> "NotetypeDict":
        # this makes sure that when fields get added, removed or are moved
        # field contents end up in the field with the same name as before
        for fld in new_model["flds"]:
            if (
                cur_ord := next(
                    (
                        _fld["ord"]
                        for _fld in cur_model["flds"]
                        if _fld["name"] == fld["name"]
                    ),
                    None,
                )
            ) is not None:
                fld["ord"] = cur_ord
            else:
                # it's okay to assign this to multiple fields because the
                # backend assigns new ords equal to the fields index
                fld["ord"] = len(new_model["flds"]) - 1
        return new_model

    def _import_notetype_and_reload_tab(self, notetype_name: str) -> None:
        self._import_notetype(notetype_name)
        self._reload_tab(notetype_name)

    def _reload_tab(self, notetype_name: str) -> None:
        tab_widget = self.window.main_tab
        index = self._get_tab_idx_by_name(notetype_name)
        tab_widget.removeTab(index)
        tab_widget.addTab(
            self._notetype_settings_tab(notetype_name, self.window),
            notetype_name,
        )
        # inserting the tab at its index or moving it to it after adding doesn't work for
        # some reason
        # tab_widget.tabBar().move(tab_widget.tabBar().count()-1, index)

        self._read_in_settings()
        self.window.update_widgets()
        self._set_active_tab(notetype_name)

    def _get_tab_idx_by_name(self, tab_name: str) -> int:
        tab_widget = self.window.main_tab
        return next(
            (
                index
                for index in range(tab_widget.count())
                if tab_name == tab_widget.tabText(index)
            ),
            None,
        )

    # read / write / create notetypes
    def _read_in_settings(self):

        # read in settings from notetypes and general ones into config
        self._read_in_settings_from_notetypes()
        self._read_in_general_settings()

    def _read_in_settings_from_notetypes(self):
        error_msg = ""
        for notetype_name in anking_notetype_names():

            if self.clayout and notetype_name == self.clayout.model["name"]:
                # if in live preview mode read in current not confirmed settings
                model = self.clayout.model
            else:
                model = mw.col.models.by_name(notetype_name)

            if not model:
                continue
            for nts in ntss_for_model(model):
                try:
                    self.conf[nts.key(notetype_name)] = nts.setting_value(model)
                except NotetypeParseException as e:
                    error_msg += f"failed parsing {notetype_name}:\n{str(e)}\n\n"

        if error_msg:
            showInfo(error_msg)

    def _read_in_general_settings(self):

        # read in default values
        for setting_name, value in general_settings_defaults_dict().items():
            self.conf.set(f"general.{setting_name}", value, on_change_trigger=False)

        # if all notetypes that have a nts have the same value set the value to it
        models_by_nts: Dict[NotetypeSetting, "NotetypeDict"] = defaultdict(lambda: [])
        for notetype_name in anking_notetype_names():
            model = mw.col.models.by_name(notetype_name)
            if not model:
                continue

            ntss = ntss_for_model(model)
            for nts in ntss:
                models_by_nts[nts].append(model)

        for nts, models in models_by_nts.items():
            setting_value = nts.setting_value(models[0]) if models else None
            if all(setting_value == nts.setting_value(model) for model in models):
                self.conf.set(
                    f"general.{nts.name()}", setting_value, on_change_trigger=False
                )

    def _update_notetypes(self):
        for notetype_name in anking_notetype_names():
            model = mw.col.models.by_name(notetype_name)
            if not model:
                continue
            ntss = ntss_for_model(model)
            model = self._safe_update_model(ntss, model)
            mw.col.models.update_dict(model)

    def _import_notetype(self, notetype_name: str) -> None:
        model = anking_notetype_model(notetype_name)
        model["id"] = 0
        mw.col.models.add_dict(model)  # type: ignore

        # add recources of all notetypes to collection media folder
        for file in Path(RESOURCES_PATH).iterdir():
            mw.col.media.add_file(str(file.absolute()))

    def _safe_update_model(self, ntss: List[NotetypeSetting], model):
        result = model.copy()
        parse_exception = None
        for nts in ntss:
            try:
                result = nts.updated_model(result, self.conf)
            except NotetypeParseException as e:
                parse_exception = e
        if parse_exception:
            tooltip(f"failed parsing notetype:\n{str(parse_exception)}")

        return result
