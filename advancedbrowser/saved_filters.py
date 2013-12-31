# -*- coding: utf-8 -*-

# This module adds the ability to save a search query (filter), which it adds to the
# tree on the left of the browser window.

from aqt import *
from anki.hooks import wrap

CONF_KEY_SAVED_FILTERS = 'ab_saved_filters'

bSave = QPushButton(u" Save ")
bRemove = QPushButton(u"Forget")

class SavedFilter:
    def __init__(self, name, query):
        self.name = name
        self.query = query

    
def myBrowserInit(self, mw, _old):
    bSave.connect(bSave, SIGNAL("clicked(bool)"), lambda: onSaveClicked(self))    
    bRemove.connect(bRemove, SIGNAL("clicked(bool)"), lambda: onRemoveClicked(self))
    
    if not mw.pm.profile.has_key(CONF_KEY_SAVED_FILTERS):
        mw.pm.profile[CONF_KEY_SAVED_FILTERS] = {}

    _old(self, mw)
   
    
    # Add our button to the right of the search box. We do this by moving
    # every widget out of the gridlayout and into a new list. We then move
    # everything back into the gridLayout in order and place our widget
    # after the search box when it comes up.
    gl = self.form.gridLayout
    n_items = gl.count()
    gl.addWidget(bSave, 0, n_items+1, 1, 1)
    gl.addWidget(bRemove, 0, n_items+2, 1, 1)
    
    self.connect(self.form.searchEdit.lineEdit(),
                 SIGNAL("textEdited(QString)"), lambda: txtChanged(self))

def txtChanged(self):
    updateButton(self)
    
def updateButton(self, reset=True):        
    txt = self.form.searchEdit.lineEdit().text()
    d = self.mw.pm.profile[CONF_KEY_SAVED_FILTERS]
    
    if txt in d.values():
        bSave.setVisible(False)
        bRemove.setVisible(True)
    else:
        bSave.setVisible(True)
        bRemove.setVisible(False)

    
def onSaveClicked(self):
    txt = unicode(self.form.searchEdit.lineEdit().text()).strip()
    name, ok = QInputDialog.getText(self, 'Save filter', 'Filter name:')
    if ok:
        self.mw.pm.profile[CONF_KEY_SAVED_FILTERS][name] = txt
        
    updateButton(self)
    self.setupTree()

def onRemoveClicked(self):
    txt = unicode(self.form.searchEdit.lineEdit().text()).strip()
    d = self.mw.pm.profile[CONF_KEY_SAVED_FILTERS]
    for name, filt in d.items():
        if txt == filt:
            d.pop(name, None)
    updateButton(self)
    self.setupTree()


def filterTree(self, root):
    root = self.CallbackItem(root, "Saved", None)
    for name, filt in self.mw.pm.profile[CONF_KEY_SAVED_FILTERS].items():
        self.CallbackItem(root, name, lambda s=filt: self.setFilter(s))

aqt.browser.Browser._systemTagTree = wrap(aqt.browser.Browser._systemTagTree, filterTree, "before")
aqt.browser.Browser.__init__ = wrap(aqt.browser.Browser.__init__, myBrowserInit, "around")
aqt.browser.Browser.onSearch = wrap(aqt.browser.Browser.onSearch, updateButton)