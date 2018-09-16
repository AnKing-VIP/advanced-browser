from anki.hooks import addHook
import aqt
from aqt.qt import *
from PyQt5.QtWidgets import *


def setupMenu(browser):
    a = QAction("unique card by note", browser)
    a.setShortcut(QKeySequence("Ctrl+Alt+N")) 
    a.triggered.connect(browser.negateUniqueNote)
    browser.form.menuEdit.addAction(a)


addHook("browser.setupMenus", setupMenu)
