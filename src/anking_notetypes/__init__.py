from aqt import mw

from .config import open_config_window
from .gui.menu import setup_menu


if mw is not None:
    setup_menu(open_config_window)
