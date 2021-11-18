from aqt.qt import QAction

from .anking_menu import get_anking_menu


def setup_menu(func) -> None:
    menu = get_anking_menu()
    a = QAction("Anking notetypes", menu)
    menu.addAction(a)
    a.triggered.connect(lambda: func())
