# -*- coding: utf-8 -*-
# Version: 0.1alpha3
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

from operator import  itemgetter

from aqt import *
from aqt.browser import DataModel, Browser
from anki.hooks import wrap, addHook, runHook
from anki.find import Finder

CONF_KEY = 'advbrowse_activeCols'

origColumnData = DataModel.columnData
origFindCards = Finder.findCards

# CustomColumn objects maintained by this add-on.
# {type -> CustomColumn}
_customTypes = {}

# Context menu items
_contextItems = []

# Context menu groups
_contextGroups = []
    
class CustomColumn:
    """
    A custom browser column.
    
    type = Internally used key to identify the column.   
    
    name = Name of column, visible to the user.
    
    onData = Function that returns an SQL query as a string. The query
    must return a scalar result. The function must be defined with
    three parameters: (card, note, type).
    E.g.:
    def myColumnOnData(card, note, type):
        return mw.col.db.scalar(
            "select min(id) from revlog where cid = ?", card.id)
    
    onSort = Optional function that returns an SQL query as a string to
    sort the column. This query will be used as the "order by" column
    of a larger query.
    def myColumnOnSort1():
        return "c.id"
        
    A nested query is also possible:
    
    def myColumnOnSort2():
        return "(select min(id) from revlog where cid = c.id)"
        
    In this query, you have the names "c" and "n" to refer to cards and
    notes, respectively. See find.py::_query for reference.
    """
    def __init__(self, type, name, onData, onSort=None):
        self.type = type
        self.name = name
        self.onData = onData
        self.onSort = onSort


class ContextColumnGroup:
    """
    A sub-menu in the context menu. Can hold CustomColumns or even more
    nested ContextColumnGroups.
    """
    def __init__(self, name):
        self.name = name
        self.items = []
    
    def addItem(self, item):
        self.items.append(item)

    
def addCustomColumn(cc, group=None):
    """Add a CustomColumn object to be maintained by this add-on."""
    
    global _customTypes
    _customTypes[cc.type] = cc


def myDataModel__init__(self, browser):
    """Load any custom columns that were saved in a previous session."""
    
    # First, we make sure those columns are still valid. If not, we ignore
    # them. This is to guard against the event that we remove or rename a
    # column (i.e., a note field). Also make sure the sortType is set to a
    # valid column.
    
    sortType = mw.col.conf['sortType']
    validSortType = False
    custCols = mw.col.conf.get(CONF_KEY, [])
    
    for custCol in custCols:
        for type in _customTypes:
            if custCol == type and custCol not in self.activeCols:
                self.activeCols.append(custCol)
            if sortType == type:
                validSortType = True
    
    if not validSortType:
        mw.col.conf['sortType'] = 'noteCrt'


# Context menu -------

def mySetupColumns(self):
    """Build a list of candidate columns. We extend the internal
    self.columns list with our custom types."""
    
    for type in _customTypes:
        self.columns.append((_customTypes[type].type, _customTypes[type].name))
    self.columns.sort(key=itemgetter(1))
        
def addContextItem(item):
    global _contextItems
    _contextItems.append(item)

    
def myOnHeaderContext(self, pos):
    """
    Override the original onHeaderContext. We are responsible for
    building the entire menu, so we include the original columns as
    well.
    """
    global _contextItems
    
    gpos = self.form.tableView.mapToGlobal(pos)
    main = QMenu()
    
    # Let clients decide what columns to include before we build the menu.
    # Clear the global list first.
    _contextItems = []
    
    # We are also a client and we need to build the built-in columns first.
    for item in self.columns:
        type, name = item
        if type not in _customTypes:
            _contextItems.append(CustomColumn(type, name, None))
    
    # Now let clients do theirs.
    runHook("advBrowserBuildContext")
    
    
    def addCheckableAction(menu, type, name):
        a = menu.addAction(name)
        a.setCheckable(True)
        a.setChecked(type in self.model.activeCols)
        a.connect(a, SIGNAL("toggled(bool)"),
                  lambda b, t=type: self.toggleField(t))
    

    # For some reason, sub menus aren't added if we don't keep a
    # reference to them until exec, so keep them in this list.
    tmp = []
    # Recursively add each item/group.
    def addToSubgroup(menu, items):
        for item in items:
            # TODO: this isn't great :(
            if isinstance(item, ContextColumnGroup):
                sub = QMenu(item.name)
                tmp.append(sub)
                menu.addMenu(sub)
                # Sort sub-group before addding it
                item.items.sort(key=lambda x: x.name) 
                addToSubgroup(sub, item.items)
            else:
                addCheckableAction(menu, item.type, item.name)

    _contextItems.sort(key=lambda x: x.name) # Sub-groups aren't sorted yet
    addToSubgroup(main, _contextItems)
    main.exec_(gpos)

# --------


def myCloseEvent(self, evt):
    """Remove our columns from self.model.activeCols when closing.
    Otherwise, Anki would save them to the equivalent in the collection
    conf, which might have ill effects elsewhere. We save our custom
    types in a custom conf item instead."""
    
    #sortType = mw.col.conf['sortType']
    # TODO: should we avoid saving the sortType? We will continue to do
    # so unless a problem with doing so becomes evident.
        
    customCols = []
    origCols = []
    
    for col in self.model.activeCols:
        isOrig = True
        for type in _customTypes:
            if col == type:
                customCols.append(col)
                isOrig = False
                break
        if isOrig:
            origCols.append(col)

    self.model.activeCols = origCols
    mw.col.conf[CONF_KEY] = customCols
    
    
def myColumnData(self, index):
    # Try to handle built-in Anki column
    returned = origColumnData(self, index)
    if returned:
        return returned
    
    # If Anki can't handle it, it must be one of ours.
    
    col = index.column()
    type = self.columnType(col)
    c = self.getCard(index)
    n = c.note()
    
    if type in _customTypes:
        return _customTypes[type].onData(c, n, type)


def myFindCards(self, query, order=False):
    """
    Overriding Finder.findCards. Since we intend to augment the sort
    behaviour for our custom types, we defer to the original findCards
    if there is a custom or no order string provided. We also use the
    original if the sort type is not one handled by this add-on. Our
    version will try to build a more efficiently sortable query, but
    aims to leave the rest intact.
    
    Currently, no optimizations are done.
    """
    
    if not order:
        return origFindCards(self, query, order)
    elif order is not True:
        # custom order string provided
        return origFindCards(self, query, order)
        
    type = self.col.conf['sortType']
    if type not in _customTypes:
        return origFindCards(self, query, order)
    
    tokens = self._tokenize(query)
    preds, args = self._where(tokens)
    if preds is None:
        return []
    
    rev = self.col.conf['sortBackwards']
    
    # We bypass _query() and _order and write our own combined version
    
    order = _customTypes[type].onSort()
    
    # can we skip the note table?
    if "n." not in preds and "n." not in order:
        sql = "select c.id from cards c where "
    else:
        sql = "select c.id from cards c, notes n where c.nid=n.id and "
        
    # combine with preds
    if preds:
        sql += "(" + preds + ")"
    else:
        sql += "1"

    # Ensure nulls and empty values appear at the end. Sadly, this can be
    # slow if we have a nested select in the "order by" clause since we're
    # effectively doing it three times. :( There must be a better way.
    sql += " order by %s is null, %s is '', %s " % (order, order, order)
    try:
        print "sql :", sql
        res = self.col.db.list(sql, *args)
    except Exception, e:
        # invalid grouping
        print "Error finding cards:", e
        return []
    
    if rev:
        res.reverse()
    return res
        
DataModel.__init__ = wrap(DataModel.__init__, myDataModel__init__)
DataModel.columnData = myColumnData
Browser.setupColumns = wrap(Browser.setupColumns, mySetupColumns)
Browser.onHeaderContext = myOnHeaderContext
Browser.closeEvent = wrap(Browser.closeEvent, myCloseEvent, "before")
Finder.findCards = myFindCards

def onLoad():
    runHook("advBrowserLoad")
    
# Ensure other add-ons don't try to use this one until it has loaded.
addHook("profileLoaded", onLoad)