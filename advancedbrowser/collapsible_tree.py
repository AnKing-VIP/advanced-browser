# -*- coding: utf-8 -*-

# This module adds the ability to collapse and expand items in the tree
# and preserve their state. Note that Anki doesn't store any identifying
# elements in each item besides the name, so we have to rebuild nested
# deck names manually.

from aqt import *
from anki.hooks import wrap
from aqt.browser import Browser

CONF_KEY_COLLAPSIBLE_TREE = 'ab_collapsible_tree'


def myBrowserInit(self, mw, _old):
    # Ensure we create our key before we start using the add-on
    if not mw.pm.profile.has_key(CONF_KEY_COLLAPSIBLE_TREE):
        mw.pm.profile[CONF_KEY_COLLAPSIBLE_TREE] = {}

    _old(self, mw)
    self.form.tree.setItemsExpandable(True)
    self.connect(self.form.tree,
                 SIGNAL("itemExpanded(QTreeWidgetItem*)"),
                 lambda item: onExpand(self, item))
    self.connect(self.form.tree,
                 SIGNAL("itemCollapsed(QTreeWidgetItem*)"),
                 lambda item: onCollapse(self, item))


def onExpand(self, item):
    key = getKey(item)
    mw.pm.profile[CONF_KEY_COLLAPSIBLE_TREE][key] = False


def onCollapse(self, item):
    key = getKey(item)
    mw.pm.profile[CONF_KEY_COLLAPSIBLE_TREE][key] = True


def getKey(item):
    "Rebuild the parent-deck-name hierarchy to use as key."
    
    l = []
    p = item
    while p:
        l.append(p.text(0))
        p = p.parent()
    l.reverse()
    return '::'.join(l)

def postSetupTree(self):
    """Every time the tree is built, figure out which items need to be
    collapsed and collapse them."""
    
    root = self.form.tree.invisibleRootItem()
    checkNodeForCollapse(self, root)
                

def checkNodeForCollapse(self, item):
    key = getKey(item)
    collapse = mw.pm.profile[CONF_KEY_COLLAPSIBLE_TREE].get(key, False)
    if collapse:
        self.form.tree.collapseItem(item)
    
    child_count = item.childCount()
    for i in range(child_count):
        child = item.child(i)
        checkNodeForCollapse(self, child)


Browser.__init__ = wrap(Browser.__init__, myBrowserInit, "around")
Browser.setupTree = wrap(Browser.setupTree, postSetupTree)