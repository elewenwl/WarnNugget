"""Shared project credits for the About dialog and idle support panel."""
from pathlib import Path
from PySide6.QtCore import QT_TRANSLATE_NOOP

CREDITS = [
    (QT_TRANSLATE_NOOP("SupportPanel", "Owner / Main Developer"), "elewenwl", "https://github.com/elewenwl"),
    (QT_TRANSLATE_NOOP("SupportPanel", "Based on GoldenNugget"), "awesomenull", "https://github.com/awesomenull-dev"),
    (QT_TRANSLATE_NOOP("SupportPanel", "Nugget Creator"), "leminlimez", "https://github.com/leminlimez"),
    (QT_TRANSLATE_NOOP("SupportPanel", "pymobiledevice3"), "doronz88", "https://github.com/doronz88"),
    (QT_TRANSLATE_NOOP("SupportPanel", "PySide6"), "Qt Company", "https://github.com/qt"),
    (QT_TRANSLATE_NOOP("SupportPanel", "Legacy Translations"), QT_TRANSLATE_NOOP("SupportPanel", "Nugget translation contributors"), "https://poeditor.com/join/project/UTqpVSE2UD"),
]

CREDIT_AVATARS = {
    "https://github.com/qt":
        str(Path(__file__).resolve().parents[1] / "qt" / "credits" / "pyside6.png"),
}

CREDIT_AVATAR_SOURCES = {}