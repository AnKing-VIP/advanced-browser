# -*- coding: utf-8 -*-

# This module adds the ability to save a search query (filter), which it adds to the
# tree on the left of the browser window.

from aqt import *
from anki.hooks import wrap
from aqt.browser import Browser

from widgets import ButtonLineEdit
import icons

CONF_KEY_SAVED_FILTERS = 'ab_saved_filters'


def postFormCreation(self, Dialog):
    """Hooked to run immediately after the form is created so we can
    override the lineEdit inside the combobox before Anki begins to
    edit it for itself."""
    self.sf_save = ButtonLineEdit.ButtonLineEdit()
    self.sf_save.buttonClicked.connect(lambda: onFavClicked(Dialog))
    self.searchEdit.setLineEdit(self.sf_save)


def myBrowserInit(self, mw):
    if not mw.pm.profile.has_key(CONF_KEY_SAVED_FILTERS):
        mw.pm.profile[CONF_KEY_SAVED_FILTERS] = {}

    # Flag for choice of saving or deleting on button click
    self.sf_doSave = True
    # Name of current saved filter (if any)
    self.sf_name = None
    
    self.connect(self.form.searchEdit.lineEdit(),
                 SIGNAL("textEdited(QString)"), lambda: updateButton(self))

    
def updateButton(self, reset=True):
    txt = unicode(self.form.searchEdit.lineEdit().text()).strip()
    d = self.mw.pm.profile[CONF_KEY_SAVED_FILTERS]
    
    for key, value in d.items():
        if txt == value:
            self.sf_doSave = False
            self.sf_name = key
            self.form.sf_save.setIcon(icons.getQIcon("star_32.png"))
            return
        
    self.sf_doSave = True
    self.form.sf_save.setIcon(icons.getQIcon("star_off_32.png"))

def onFavClicked(self):
    if self.sf_doSave:
        saveClicked(self)
    else:
        deleteClicked(self)

def saveClicked(self):
    txt = unicode(self.form.searchEdit.lineEdit().text()).strip()
    dlg = QInputDialog(self)
    dlg.setInputMode(QInputDialog.TextInput)
    dlg.setLabelText("Filter name:")
    dlg.setWindowTitle("Save filter")
    dlg.resize(300,100)
    ok = dlg.exec_()
    name = dlg.textValue()
    if ok:
        self.mw.pm.profile[CONF_KEY_SAVED_FILTERS][name] = txt
        
    updateButton(self)
    self.setupTree()

def deleteClicked(self):
    msg = 'Delete saved filter "%s"?' % self.sf_name
    ok = QMessageBox.question(self, 'Remove filter',
                     msg, QMessageBox.Yes, QMessageBox.No)

    if ok == QMessageBox.Yes:
        self.mw.pm.profile[CONF_KEY_SAVED_FILTERS].pop(self.sf_name, None)
        updateButton(self)
        self.setupTree()


def filterTree(self, root):
    root = self.CallbackItem(root, "Saved", None)
    root.setIcon(0, QIcon(icons.getQIcon("star_dark_32.png")))
    for name, filt in self.mw.pm.profile[CONF_KEY_SAVED_FILTERS].items():
        self.CallbackItem(root, name, lambda s=filt: self.setFilter(s))
        

aqt.forms.browser.Ui_Dialog.setupUi = wrap(aqt.forms.browser.Ui_Dialog.setupUi, postFormCreation)
Browser._systemTagTree = wrap(Browser._systemTagTree, filterTree, "before")
Browser.__init__ = wrap(Browser.__init__, myBrowserInit)
Browser.onSearch = wrap(Browser.onSearch, updateButton)