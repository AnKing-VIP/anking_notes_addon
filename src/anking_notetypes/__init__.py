from aqt import mw
from aqt.gui_hooks import card_layout_will_show
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

from .config import open_config_window
from .gui.menu import setup_menu

if mw is not None:
    setup_menu(open_config_window)


def add_button_to_clayout(clayout):
    button = QPushButton()
    button.setAutoDefault(False)
    button.setText("Configure AnKing notetypes")
    button.clicked.connect(lambda: open_config_window(clayout))
    clayout.buttons.insertWidget(1, button)


card_layout_will_show.append(add_button_to_clayout)
