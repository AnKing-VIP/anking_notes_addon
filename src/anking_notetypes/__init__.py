from aqt import mw
from aqt.gui_hooks import card_layout_will_show
from aqt.qt import *

from .compat import add_compat_aliases
from .config import NotetypesConfigWindow
from .gui.menu import setup_menu

if mw is not None:
    window = NotetypesConfigWindow()
    setup_menu(window.open)


def add_button_to_clayout(clayout):
    button = QPushButton()
    button.setAutoDefault(False)
    button.setText("Configure AnKing notetypes")
    window = NotetypesConfigWindow(clayout)
    button.clicked.connect(lambda: window.open())
    clayout.buttons.insertWidget(1, button)


card_layout_will_show.append(add_button_to_clayout)

add_compat_aliases()
