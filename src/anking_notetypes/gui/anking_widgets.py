from pathlib import Path
from typing import Tuple

from aqt.qt import (
    QCursor,
    QDir,
    QHBoxLayout,
    QIcon,
    QLabel,
    QPixmap,
    QSize,
    QSizePolicy,
    Qt,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import openLink

QDir.addSearchPath("icons", f"{Path(__file__).parent.parent}/resources")


def icon_button(icon_data: Tuple[str, Tuple[int, int], str]) -> QToolButton:
    (image, size, url) = icon_data
    icon = QIcon(QPixmap(f"icons:{image}"))
    button = QToolButton()
    button.setIcon(icon)
    button.setIconSize(QSize(size[0], size[1]))
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    button.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
    button.setAutoRaise(True)
    button.setToolTip(url)
    button.clicked.connect(lambda _, url=url: openLink(url))  # type: ignore
    return button


class AnkingIconsLayout(QHBoxLayout):
    def __init__(self, parent: QWidget) -> None:
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setup()
        parent.setLayout(self)

    def setup(self) -> None:
        self.addStretch()
        icon_objs = [
            ("AnKingSmall.png", (31, 31), "https://www.ankingmed.com"),
            ("YouTube.png", (31, 31), "https://www.youtube.com/theanking"),
            ("Patreon.png", (221, 31), "https://www.patreon.com/ankingmed"),
            ("Instagram.png", (31, 31), "https://instagram.com/ankingmed"),
            ("Facebook.png", (31, 31), "https://facebook.com/ankingmed"),
        ]
        for obj in icon_objs:
            btn = icon_button(obj)
            self.addWidget(btn)
        self.addStretch()


class AnkiMasteryCourseLayout(QHBoxLayout):
    def __init__(self, parent: QWidget) -> None:
        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setup()
        parent.setLayout(self)

    def setup(self) -> None:
        addon_name = __name__.split(".")[0]
        icon_data = (
            "AnKingSmall.png",
            (64, 64),
            f"https://www.theanking.com/anki-mastery-course/?utm_source={addon_name}&utm_medium=anki_add-on&utm_campaign=mastery_course",
        )
        btn = icon_button(icon_data)
        self.addStretch()
        self.addWidget(btn)
        self.addSpacing(5)

        text_layout = QVBoxLayout()
        self.addLayout(text_layout)
        self.addStretch()

        label1 = QLabel("Interested in learning how to use Anki effectively?")
        label2 = QLabel(
            "Check out the Anki Mastery Course, a comprehensive series of lessons\n"
            "and video tutorials designed by the AnKing team."
        )
        text_layout.addWidget(label1)
        text_layout.addWidget(label2)


class GithubLinkLayout(QHBoxLayout):
    def __init__(self, parent: QWidget, href: str) -> None:
        self.href = href

        QHBoxLayout.__init__(self, parent)
        self.setContentsMargins(0, 0, 0, 0)
        self.setup()
        parent.setLayout(self)

    def setup(self) -> None:
        self.addStretch()
        text_layout = QVBoxLayout()
        self.addLayout(text_layout)
        self.addStretch()

        label = QLabel()
        label.setText(
            f'You can report bugs and request features <a href="{self.href}">here</a>.'
        )
        label.setOpenExternalLinks(True)
        text_layout.addWidget(label)
