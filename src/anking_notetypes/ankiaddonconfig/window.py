from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple, Union

from aqt import mw
from aqt.qt import (
    QT_VERSION_STR,
    QAbstractItemView,
    QAbstractSpinBox,
    QBoxLayout,
    QCheckBox,
    QCloseEvent,
    QColor,
    QColorDialog,
    QComboBox,
    QCursor,
    QDialog,
    QDoubleSpinBox,
    QDropEvent,
    QFileDialog,
    QFont,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QIcon,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStyle,
    Qt,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QWidget,
)
from aqt.utils import restoreGeom, saveGeom, tooltip

from .collapsible_section import CollapsibleSection
from .errors import InvalidConfigValueError

if TYPE_CHECKING:
    from .manager import ConfigManager

QT6 = QT_VERSION_STR.split(".")[0] == "6"


class ConfigWindow(QDialog):
    def __init__(self, conf: "ConfigManager", parent=None) -> None:
        QDialog.__init__(self, parent, Qt.WindowType.Window)  # type: ignore
        self.conf = conf
        self.mgr = mw.addonManager
        self.widget_updates: List[Callable[[], None]] = []
        self.should_save_hook: List[Callable[[], bool]] = []
        self._on_save_hook: List[Callable[[], None]] = []
        self._on_close_hook: List[Callable[[], None]] = []
        self.geom_key = f"addonconfig-{conf.addon_name}"

        self.setWindowTitle(f"Config for {conf.addon_name}")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setup()

    def setup(self) -> None:
        self.outer_layout = ConfigLayout(self, QBoxLayout.Direction.TopToBottom)
        self.main_layout = ConfigLayout(self, QBoxLayout.Direction.TopToBottom)
        self.btn_layout = ConfigLayout(self, QBoxLayout.Direction.LeftToRight)
        self.outer_layout.addLayout(self.main_layout)
        self.outer_layout.addLayout(self.btn_layout)
        self.setLayout(self.outer_layout)

        self.main_tab = QTabWidget()
        main_tab = self.main_tab
        main_tab.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Change the default for macOS
        main_tab.setElideMode(Qt.TextElideMode.ElideNone)
        main_tab.setUsesScrollButtons(True)

        self.main_layout.addWidget(main_tab)
        self.setup_buttons(self.btn_layout)

    def setup_buttons(self, btn_box: "ConfigLayout") -> None:
        btn_box.addStretch(1)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel)  # type: ignore
        btn_box.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.setDefault(True)
        self.save_btn.setShortcut("Ctrl+Return")
        self.save_btn.clicked.connect(self.on_save)  # type: ignore
        btn_box.addWidget(self.save_btn)

    def update_widgets(self) -> None:
        for widget_update in self.widget_updates:
            try:
                widget_update()
            except InvalidConfigValueError:
                pass

    def on_open(self) -> None:
        self.update_widgets()
        restoreGeom(self, self.geom_key)

    def on_save(self) -> None:
        for hook in self.should_save_hook:
            if not hook():
                return
        for hook in self._on_save_hook:
            hook()
        self.conf.save()
        self.close()

    def on_cancel(self) -> None:
        self.close()

    def on_reset(self) -> None:
        self.update_widgets()
        tooltip("Press save to save changes")

    def closeEvent(self, evt: QCloseEvent) -> None:
        # Discard the contents when clicked cancel,
        # and also in case the window was clicked without clicking any of the buttons
        for hook in self._on_close_hook:
            hook()
        self.conf.load()
        saveGeom(self, self.geom_key)
        evt.accept()

    # Add Widgets

    def add_tab(self, name: str, index=None) -> "ConfigLayout":
        tab = QWidget(self)
        layout = ConfigLayout(self, QBoxLayout.Direction.TopToBottom)
        tab.setLayout(layout)
        if index is None:
            self.main_tab.addTab(tab, name)
        else:
            self.main_tab.insertTab(index, tab, name)
        return layout

    def execute_on_save(self, hook: Callable[[], None]) -> None:
        self._on_save_hook.append(hook)

    def execute_on_close(self, hook: Callable[[], None]) -> None:
        self._on_close_hook.append(hook)

    def set_footer(
        self,
        text: str,
        html: bool = False,
        size: int = 0,
        multiline: bool = False,
        tooltip: Optional[str] = None,
    ) -> QLabel:
        footer = QLabel(text)
        if html:
            footer.setTextFormat(Qt.TextFormat.RichText)
            footer.setOpenExternalLinks(True)
        else:
            footer.setTextFormat(Qt.TextFormat.PlainText)
        if size:
            font = QFont()
            font.setPixelSize(size)
            footer.setFont(font)
        if multiline:
            footer.setWordWrap(True)
        if tooltip:
            footer.setToolTip(tooltip)

        self.main_layout.addWidget(footer)
        return footer


class ConfigLayout(QBoxLayout):
    def __init__(self, conf_window: ConfigWindow, direction: QBoxLayout.Direction):
        QBoxLayout.__init__(self, direction)
        self.conf = conf_window.conf
        self.config_window = conf_window
        self.widget_updates = conf_window.widget_updates

    # Config Input Widgets

    def checkbox(
        self, key: str, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> QCheckBox:
        "For boolean config"
        checkbox = QCheckBox()
        if description is not None:
            checkbox.setText(description)
        if tooltip:
            checkbox.setIcon(self._info_icon())
            checkbox.setToolTip(tooltip)

        def update() -> None:
            value = self.conf.get(key)
            if not isinstance(value, bool):
                raise InvalidConfigValueError(key, "boolean", value)
            checkbox.setChecked(value)

        self.widget_updates.append(update)

        checkbox.stateChanged.connect(  # type: ignore
            lambda s: self.conf.set(
                key,
                s == (Qt.CheckState.Checked.value if QT6 else Qt.CheckState.Checked),  # type: ignore
            )
        )
        self.addWidget(checkbox)
        return checkbox

    def dropdown(
        self,
        key: str,
        labels: list,
        values: list,
        description: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> QComboBox:
        combobox = QComboBox()
        combobox.insertItems(0, labels)

        def update() -> None:
            conf = self.conf
            try:
                val = conf.get(key)
                index = values.index(val)
            except ValueError:
                raise InvalidConfigValueError(
                    key, "any value in list " + str(values), val
                )
            combobox.setCurrentIndex(index)

        self.widget_updates.append(update)

        combobox.currentIndexChanged.connect(  # type: ignore
            lambda idx: self.conf.set(key, values[idx])
        )

        row = self.hlayout()

        if tooltip:
            combobox.setToolTip(tooltip)
            row.addWidget(self._info_icon_label(tooltip))

        if description is not None:
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(combobox)
            row.stretch()

        return combobox

    def order_widget(
        self,
        key: str,
        items: List[str],
        description: Optional[str] = None,
        tooltip: Optional[str] = None,
    ) -> QTableWidget:
        def on_edit():
            val = []
            for rIdx in range(table.rowCount()):
                val.append(table.item(rIdx, 0).data(0))
            self.conf.set(key, val)

        table = OrderTable(on_edit=on_edit)
        table.setDragEnabled(True)
        table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().hide()
        table.verticalHeader().hide()

        def update() -> None:
            val = self.conf.get(key)
            if not isinstance(val, list):
                raise InvalidConfigValueError(key, "List[str]", val)
            load_table(val)

        def load_table(data):
            table.setColumnCount(1)
            table.setRowCount(len(data))
            for rIdx, x in enumerate(data):
                item = QTableWidgetItem(x)
                table.setItem(rIdx, 0, item)
            table.resizeColumnsToContents()
            table.resizeRowsToContents()
            table.setMinimumHeight(
                table.rowHeight(0) * table.rowCount() + table.rowCount()
            )
            table.setFixedWidth(
                table.columnWidth(0) + table.verticalHeader().width() + 17,
            )

        load_table(items)

        self.widget_updates.append(update)

        if description is not None:
            self.text(description, tooltip=tooltip)
            self.space(7)
        self.addWidget(table)
        return table

    def text_input(
        self, key: str, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> QLineEdit:
        "For string config"
        line_edit = QLineEdit()

        def update() -> None:
            val = self.conf.get(key)
            if not isinstance(val, str):
                raise InvalidConfigValueError(key, "string", val)
            line_edit.setText(val)
            line_edit.setCursorPosition(0)

        self.widget_updates.append(update)

        def on_editing_finished():
            self.conf.set(key, line_edit.text())

        line_edit.editingFinished.connect(on_editing_finished)  # type: ignore

        row = self.hlayout()

        if tooltip:
            row.addWidget(self._info_icon_label(tooltip))
            line_edit.setToolTip(tooltip)

        if description is not None:
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(line_edit)
        else:
            self.addWidget(line_edit)
        return line_edit

    def number_input(
        self,
        key: str,
        description: Optional[str] = None,
        tooltip: Optional[str] = None,
        minimum: int = 0,
        maximum: int = 99,
        step: int = 1,
        decimal: bool = False,
        precision: int = 2,
    ) -> QAbstractSpinBox:
        "For integer config"
        spin_box: Union[QDoubleSpinBox, QSpinBox]
        if decimal:
            spin_box = QDoubleSpinBox()
            spin_box.setDecimals(precision)
        else:
            spin_box = QSpinBox()

        spin_box.setMinimum(minimum)
        spin_box.setMaximum(maximum)
        spin_box.setSingleStep(step)

        def update() -> None:
            val = self.conf.get(key)
            if not decimal and not isinstance(val, int):
                raise InvalidConfigValueError(key, "integer number", val)
            if decimal and not isinstance(val, (int, float)):
                raise InvalidConfigValueError(key, "number", val)
            if minimum is not None and val < minimum:
                raise InvalidConfigValueError(
                    key, f"integer number greater or equal to {minimum}", val
                )
            if maximum is not None and val > maximum:
                raise InvalidConfigValueError(
                    key, f"integer number lesser or equal to {maximum}", val
                )
            spin_box.setValue(val)

        self.widget_updates.append(update)

        spin_box.valueChanged.connect(lambda val: self.conf.set(key, val))  # type: ignore

        row = self.hlayout()

        if tooltip:
            row.addWidget(self._info_icon_label(tooltip))
            spin_box.setToolTip(tooltip)

        if description is not None:
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(spin_box)
            row.stretch()
        else:
            self.addWidget(spin_box)

        return spin_box

    def color_input(
        self, key: str, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> QPushButton:
        "For hex color config"
        button = QPushButton()
        button.setFixedWidth(25)
        button.setFixedHeight(25)
        button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        color_dialog = QColorDialog(self.config_window)
        color_dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel)

        def set_color(rgb: str) -> None:
            border_style = "none" if rgb != "transparent" else "1px solid #000000"
            button.setStyleSheet(
                f'QPushButton{{ background-color: "{rgb}"; border: {border_style}; border-radius: 3px}}'
            )
            color = QColor()
            color.setNamedColor(rgb)
            if not color.isValid():
                raise InvalidConfigValueError(key, "rgb hex color string", rgb)
            color_dialog.setCurrentColor(color)

        def update() -> None:
            value = self.conf.get(key)

            if value != "inherit":
                set_color(value)
            else:
                set_color("transparent")

        def save(color: QColor) -> None:
            rgb = color.name()
            if color.name(QColor.NameFormat.HexArgb) == "#00000000":
                rgb = "transparent"
            self.conf.set(key, rgb)
            set_color(rgb)

        self.widget_updates.append(update)
        color_dialog.colorSelected.connect(lambda color: save(color))  # type: ignore
        button.clicked.connect(lambda _: color_dialog.exec())  # type: ignore

        row = self.hlayout()

        if tooltip:
            row.addWidget(self._info_icon_label(tooltip))
            button.setToolTip(tooltip)

        if description is not None:
            row.text(description, tooltip=tooltip)
            row.space(7)
            row.addWidget(button)
            row.stretch()
        else:
            self.addWidget(button)

        return button

    def path_input(
        self,
        key: str,
        description: Optional[str] = None,
        tooltip: Optional[str] = None,
        get_directory: bool = False,
        filter: str = "Any files (*)",
    ) -> Tuple[QLineEdit, QPushButton]:
        "For path string config"

        row = self.hlayout()
        if description is not None:
            row.text(description, tooltip=tooltip)
            row.space(7)
        line_edit = QLineEdit()
        line_edit.setReadOnly(True)
        row.addWidget(line_edit)
        button = QPushButton("Browse")
        row.addWidget(button)

        if tooltip:
            row.insertWidget(0, self._info_icon_label(tooltip))
            line_edit.setToolTip(tooltip)

        def update() -> None:
            val = self.conf.get(key)
            if not isinstance(val, str):
                raise InvalidConfigValueError(key, "string file path", val)
            line_edit.setText(val)

        def get_path() -> None:
            val = self.conf.get(key)
            parent_dir = str(Path(val).parent)

            if get_directory:
                path = QFileDialog.getExistingDirectory(
                    self.config_window, directory=parent_dir
                )
            else:
                path = QFileDialog.getOpenFileName(
                    self.config_window, directory=parent_dir, filter=filter
                )[0]
            if path:  # is None if cancelled
                self.conf.set(key, path)
                update()

        self.widget_updates.append(update)
        button.clicked.connect(get_path)  # type: ignore

        return (line_edit, button)

    def shortcut_edit(
        self, key, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> Tuple[QKeySequenceEdit, QPushButton]:
        edit = QKeySequenceEdit()

        if description is not None:
            row = self.hlayout()
            row.text(description, tooltip=tooltip)

        def update():
            val = self.conf.get(key)
            if not isinstance(val, str):
                raise InvalidConfigValueError(key, "str", val)
            val = val.replace(" ", "")
            edit.setKeySequence(val)

        self.widget_updates.append(update)

        edit.keySequenceChanged.connect(  # type: ignore
            lambda s: self.conf.set(key, edit.keySequence().toString())
        )

        self.addWidget(edit)

        def on_shortcut_clear_btn_click():
            edit.clear()

        shortcut_clear_btn = QPushButton("Clear")
        shortcut_clear_btn.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        shortcut_clear_btn.clicked.connect(on_shortcut_clear_btn_click)  # type: ignore

        layout = QHBoxLayout()
        layout.addWidget(edit)
        layout.addWidget(shortcut_clear_btn)

        self.addLayout(layout)
        return edit, shortcut_clear_btn

    def font_family_combobox(
        self, key, description: Optional[str] = None, tooltip: Optional[str] = None
    ) -> QFontComboBox:
        combo = QFontComboBox()

        if description is not None:
            row = self.hlayout()
            row.text(description, tooltip=tooltip)

        def update():
            val = self.conf.get(key)
            if not isinstance(val, str):
                raise InvalidConfigValueError(key, "str", val)
            combo.setCurrentText(val)

        self.widget_updates.append(update)

        combo.currentTextChanged.connect(  # type: ignore
            lambda s: self.conf.set(key, combo.currentText())
        )

        self.addWidget(combo)
        return combo

    # Layout widgets

    def text(
        self,
        text: str,
        bold: bool = False,
        html: bool = False,
        size: int = 0,
        multiline: bool = False,
        tooltip: Optional[str] = None,
    ) -> QLabel:
        label_widget = QLabel(text)
        label_widget.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        if html:
            label_widget.setTextFormat(Qt.TextFormat.RichText)
            label_widget.setOpenExternalLinks(True)
        else:
            label_widget.setTextFormat(Qt.TextFormat.PlainText)
        if bold or size:
            font = QFont()
            if bold:
                font.setBold(True)
            if size:
                font.setPixelSize(size)
            label_widget.setFont(font)
        if multiline:
            label_widget.setWordWrap(True)
        if tooltip:
            label_widget.setToolTip(tooltip)

        self.addWidget(label_widget)
        return label_widget

    def button(
        self,
        text: str,
        on_click: Optional[Callable] = None,
    ) -> QPushButton:
        button = QPushButton()
        button.setText(text)
        button.clicked.connect(on_click)  # type: ignore
        button.setAutoDefault(False)
        self.addWidget(button)
        return button

    def _separator(self, direction: QFrame.Shape) -> QFrame:
        """direction should be either QFrame.Shape.HLine or QFrame.VLine"""
        line = QFrame()
        line.setLineWidth(0)
        line.setFrameShape(direction)
        line.setFrameShadow(QFrame.Shadow.Plain)
        self.addWidget(line)
        return line

    def hseparator(self) -> QFrame:
        return self._separator(QFrame.Shape.HLine)

    def vseparator(self) -> QFrame:
        return self._separator(QFrame.Shape.VLine)

    def _container(self, direction: QBoxLayout.Direction) -> "ConfigLayout":
        """Adds (empty) QWidget > ConfigLayout.

        You can access its parent widget using ConfigLayout.parentWidget()
        """
        container = QWidget()
        inner_layout = ConfigLayout(self.config_window, direction)
        container.setLayout(inner_layout)
        self.addWidget(container)
        return inner_layout

    def hcontainer(self) -> "ConfigLayout":
        """Adds (empty) QWidget > ConfigLayout."""
        return self._container(QBoxLayout.Direction.RightToLeft)

    def vcontainer(self) -> "ConfigLayout":
        """Adds (empty) QWidget > ConfigLayout."""
        return self._container(QBoxLayout.Direction.TopToBottom)

    def _layout(self, direction: QBoxLayout.Direction) -> "ConfigLayout":
        layout = ConfigLayout(self.config_window, direction)
        self.addLayout(layout)
        return layout

    def hlayout(self) -> "ConfigLayout":
        return self._layout(QBoxLayout.Direction.LeftToRight)

    def vlayout(self) -> "ConfigLayout":
        return self._layout(QBoxLayout.Direction.TopToBottom)

    def space(self, space: int = 1) -> None:
        self.addSpacing(space)

    def stretch(self, factor: int = 0) -> None:
        self.addStretch(factor)

    def _scroll_layout(
        self,
        hsizepolicy: QSizePolicy.Policy,
        vsizepolicy: QSizePolicy.Policy,
        hscrollbarpolicy: Qt.ScrollBarPolicy,
        vscrollbarpolicy: Qt.ScrollBarPolicy,
    ) -> "ConfigLayout":
        """Adds QScrollArea > QWidget*2 > ConfigLayout, returns the layout."""
        # QScrollArea seems to automatically add a child widget.
        layout = ConfigLayout(self.config_window, QBoxLayout.Direction.TopToBottom)
        inner_widget = QWidget()
        inner_widget.setLayout(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(inner_widget)
        scroll.setSizePolicy(hsizepolicy, vsizepolicy)
        scroll.setHorizontalScrollBarPolicy(hscrollbarpolicy)
        scroll.setVerticalScrollBarPolicy(vscrollbarpolicy)
        self.addWidget(scroll)
        return layout

    def hscroll_layout(self, always: bool = False) -> "ConfigLayout":
        """Adds QScrollArea > QWidget*2 > ConfigLayout, returns the layout."""
        return self._scroll_layout(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
            (
                Qt.ScrollBarPolicy.ScrollBarAlwaysOn
                if always
                else Qt.ScrollBarPolicy.ScrollBarAsNeeded
            ),
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
        )

    def vscroll_layout(self, always: bool = False) -> "ConfigLayout":
        """Adds QScrollArea > QWidget*2 > ConfigLayout, returns the layout."""
        return self._scroll_layout(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding,
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            (
                Qt.ScrollBarPolicy.ScrollBarAlwaysOn
                if always
                else Qt.ScrollBarPolicy.ScrollBarAsNeeded
            ),
        )

    def scroll_layout(
        self,
        horizontal: bool = True,
        vertical: bool = True,
    ) -> "ConfigLayout":
        """Legacy. Adds QScrollArea > QWidget*2 > ConfigLayout, returns the layout."""
        return self._scroll_layout(
            QSizePolicy.Policy.Expanding if horizontal else QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Expanding if vertical else QSizePolicy.Policy.Minimum,
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

    def collapsible_section(self, title: str) -> "ConfigLayout":
        layout = ConfigLayout(self.config_window, QBoxLayout.Direction.TopToBottom)
        section = CollapsibleSection(title)
        section.setContentLayout(layout)
        self.addWidget(section)
        return layout

    def _info_icon(self) -> QIcon:
        dummy = QCheckBox()
        return dummy.style().standardIcon(
            QStyle.StandardPixmap.SP_MessageBoxInformation
        )

    def _info_icon_label(self, tooltip: str) -> QLabel:
        result = QLabel("")
        pixmap = self._info_icon().pixmap(
            QCheckBox().iconSize()
        )  # use same icon size as for checkbox
        result.setPixmap(pixmap)
        result.setToolTip(tooltip)
        result.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        return result


class OrderTable(QTableWidget):
    def __init__(self, on_edit: Callable):
        super().__init__()
        self._on_edit: Callable = on_edit

    def dropEvent(self, dropEvent: QDropEvent):
        item_src = self.selectedItems()[0]
        try:
            item_dest = self.itemAt(dropEvent.position().toPoint())  # type: ignore
        except:
            # for older versions of qt
            item_dest = self.itemAt(dropEvent.pos())
        src_value = item_src.text()
        item_src.setText(item_dest.text())
        item_dest.setText(src_value)
        self._on_edit()
