from typing import Any, List, Optional

import aqt
from aqt.qt import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    Qt,
    QVBoxLayout,
    qconnect,
)

# NOTE: Adapted from AnkiHub


def choose_subset(
    prompt: str,
    choices: List[str],
    current: Optional[List[str]] = None,
    adjust_height_to_content=True,
    description_html: Optional[str] = None,
    parent: Any = None,
) -> Optional[List[str]]:
    if not parent:
        parent = aqt.mw.app.activeWindow()
    if current is None:
        current = []
    dialog = QDialog(parent)
    try:
        from aqt.utils import disable_help_button

        disable_help_button(dialog)
    except ImportError:
        pass
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    layout = QVBoxLayout()
    dialog.setLayout(layout)
    label = QLabel(prompt)
    layout.addWidget(label)
    list_widget = QListWidget()
    layout.addWidget(list_widget)

    layout.addSpacing(5)

    # add a "select all" button
    def select_all():
        all_selected = all(
            list_widget.item(i).checkState() == Qt.CheckState.Checked
            for i in range(list_widget.count())
        )
        if all_selected:
            for i in range(list_widget.count()):
                list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)
        else:
            for i in range(list_widget.count()):
                list_widget.item(i).setCheckState(Qt.CheckState.Checked)

    button = QPushButton("Select All")
    qconnect(button.clicked, select_all)
    layout.addWidget(button)
    current = [c.lower() for c in current]
    for choice in choices:
        item = QListWidgetItem(choice)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)  # type: ignore
        item.setCheckState(
            Qt.CheckState.Checked
            if choice.lower() in current
            else Qt.CheckState.Unchecked
        )
        list_widget.addItem(item)

    # toggle item check state when clicked
    qconnect(
        list_widget.itemClicked,
        lambda item: item.setCheckState(
            Qt.CheckState.Checked
            if item.checkState() == Qt.CheckState.Unchecked
            else Qt.CheckState.Unchecked
        ),
    )

    if description_html:
        label = QLabel(f"<i>{description_html}</i>")
        layout.addWidget(label)

    layout.addSpacing(10)
    button_box = QDialogButtonBox(  # type: ignore
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    qconnect(button_box.accepted, dialog.accept)
    qconnect(button_box.rejected, dialog.reject)

    layout.addWidget(button_box)

    if adjust_height_to_content:
        list_widget.setMinimumHeight(
            list_widget.sizeHintForRow(0) * list_widget.count() + 20
        )

    if not dialog.exec():
        return None

    result = [
        list_widget.item(i).text()
        for i in range(list_widget.count())
        if list_widget.item(i).checkState() == Qt.CheckState.Checked
    ]
    return result
