# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

import time
from operator import  itemgetter

from aqt import *
from aqt.browser import DataModel, Browser
from anki.hooks import wrap, runHook
from anki.find import Finder
from advancedbrowser.contextmenu import ContextMenu
from advancedbrowser.column import Column, CustomColumn

CONF_KEY = 'advbrowse_activeCols'

# Global reference to an AdvancedBrowser object (set when
# AdvancedBrowser is instantiated). We need this to work around the
# fact that the overridden Anki functions require their own instance
# objects as the first parameter ("self"). The overridden functions,
# thus, cannot be functions in the AdvancedBrowser class.
AB = None

origColumnData = DataModel.columnData
origFindCards = Finder.findCards

class AdvancedBrowser:
    """Maintains state for the add-on."""
    
    def __init__(self):
                
        # CustomColumn objects maintained by this add-on.
        # {type -> CustomColumn}
        self.customTypes = {}
       
        global AB
        AB = self

    def newCustomColumn(self, type, name, onData, onSort=None,
                 cacheSortValue=False):
        """Add a CustomColumn to the browser. See CustomColumn for a
        detailed description of the parameters.
        
        """
        cc = CustomColumn(type, name, onData, onSort, cacheSortValue)
        self.customTypes[cc.type] = cc
        return cc



def myDataModel__init__(self, browser):
    """Load any custom columns that were saved in a previous session."""
    
    # First, we make sure those columns are still valid. If not, we ignore
    # them. This is to guard against the event that we remove or rename a
    # column. Also make sure the sortType is set to a valid column.
    
    sortType = mw.col.conf['sortType']
    validSortType = False
    custCols = mw.col.conf.get(CONF_KEY, [])
    
    for custCol in custCols:
        for type in AB.customTypes:
            if custCol == type and custCol not in self.activeCols:
                self.activeCols.append(custCol)
            if sortType == type:
                validSortType = True
    
    if not validSortType:
        mw.col.conf['sortType'] = 'noteFld'
        # Guarantee that we always start with at least one column.
        if 'noteFld' not in self.activeCols:
            self.activeCols.append('noteFld')


def mySetupColumns(self):
    """Build a list of candidate columns. We extend the internal
    self.columns list with our custom types.
    
    """
    
    for type in AB.customTypes:
        self.columns.append((AB.customTypes[type].type,
                             AB.customTypes[type].name))
    self.columns.sort(key=itemgetter(1))
    
def myOnHeaderContext(self, pos):
    """Override the original onHeaderContext. We are responsible for
    building the entire menu, so we include the original columns as
    well.
    
    """
    
    gpos = self.form.tableView.mapToGlobal(pos)
    main = QMenu()
    contextMenu = ContextMenu()
    
    # We are also a client and we need to add the built-in columns first.
    for item in self.columns:
        type, name = item
        if type not in AB.customTypes:
            contextMenu.addItem(Column(type, name))
    
    # Now let clients do theirs.
    runHook("advBrowserBuildContext", contextMenu)
    
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
            if isinstance(item, ContextMenu):
                sub = QMenu(item.name)
                tmp.append(sub)
                menu.addMenu(sub)
                addToSubgroup(sub, item.items())
            else:
                addCheckableAction(menu, item.type, item.name)

    # Start adding from the top
    addToSubgroup(main, contextMenu.items())
    main.exec_(gpos)


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
    
    if type in AB.customTypes:
        return AB.customTypes[type].onData(c, n, type)


def myFindCards(self, query, order=False):
    """Overriding Finder.findCards. Our version will build a more
    efficiently sortable query when it comes across a case handled
    only by this add-on, but aims to leave the rest intact.
    
    Since we intend to augment the sort behaviour for our custom types
    only, we defer to the original findCards in cases where this add-on
    has no special work to do. The following cases are deferred:
    
    1. order=False: No ordering is expected. This is likely coming from
    a filtered deck being built where no order is required. Since we
    don't provide access to custom types outside of the browser, this
    case should never need to be handled by this add-on.
    
    2. order="some string": A custom order string has been provided.
    This is likely coming from a filtered deck being built where some
    specific order is required. As above, this add-on doesn't provide
    access to custom types outside of the browser, so this case should
    always be handled internally.
    
    3. order=True: The cards need to be ordered, but we are left with
    the decision of how to order them. This is likely coming from the
    browser, where a column needs to be sorted by some database column
    or value associated with it. If the column is not a custom one
    handled by this add-on, do it internally.
    
    If the above three are not satisfied, then the only remaining
    possibility is that a column needs to be sorted according to its
    own rules and it's one of ours.
    
    """
    
    if not order: # Case 1
        return origFindCards(self, query, order)
    elif order is not True:
        return origFindCards(self, query, order) # Case 2
        
    type = self.col.conf['sortType']
    if type not in AB.customTypes:
        return origFindCards(self, query, order) # Case 3
    
    # We bypass _query() and _order and write our own combined version
    #
    # NOTE: the "order by x is null, x is '', x is X" pattern is to
    # ensure null values and empty strings are sorted after useful
    # values. The default is to place them first, which we don't want.
    
    tokens = self._tokenize(query)
    preds, args = self._where(tokens)
    if preds is None:
        return []

    if preds:
        preds = "(" + preds + ")"
    else:
        preds = "1"
    
    order = AB.customTypes[type].onSort()
            
    t = time.time()
    drop = False
    
    if not order:
        print "NO SORT PATH"

        if "n." not in preds:
            sql = "select c.id from cards c where "
        else:
            sql = "select c.id from cards c, notes n where c.nid=n.id and "
        sql += preds
    elif AB.customTypes[type].cacheSortValue or "select" in order.lower():
        print "TEMP SORT TABLE PATH"
        
        # Use a temporary table to store the results of the ORDER BY
        # clause for efficiency since we repeatedly access those values.

        try:
            if "n." not in preds:
                tmpSql = ("create temp table tmp as select *, %s as srt "
                          "from cards c where %s" % (order, preds))
            else:
                tmpSql = ("create temp table tmp as select *, %s as srt "
                          "from cards c, notes n where c.nid=n.id and %s"
                           % (order, preds))
            
            print "Temp sort table sql: ", tmpSql
            self.col.db.execute(tmpSql, *args)
            drop = True
            args = {} # We've consumed them, so empty this.
        except Exception, e:
            print "Failed to create temp sort table: " + e.message
            return []

        sql = ("select id, srt from tmp order by "
               "tmp.srt is null, tmp.srt is '', tmp.srt collate nocase")
    else:
        print "NORMAL SORT PATH"
        
        if "n." not in preds and "n." not in order:
            sql = "select * from cards c where "
        else:
            sql = "select * from cards c, notes n where c.nid=n.id and "
    
        sql += preds
        sql += (" order by %s is null, %s is '', %s collate nocase" %
                (order, order, order))

    try:
        print "sql :", sql
        res = self.col.db.list(sql, *args)
    except Exception, e:
        print "Error finding cards:", e
        return []
    finally:
        if drop:
            self.col.db.execute("drop table tmp")

    if self.col.conf['sortBackwards']:
        res.reverse()
        
    print "Search took: %dms" % ((time.time() - t)*1000)
    return res


def myCloseEvent(self, evt):
    """Remove our columns from self.model.activeCols when closing.
    Otherwise, Anki would save them to the equivalent in the collection
    conf, which might have ill effects elsewhere. We save our custom
    types in a custom conf item instead.
    
    """
    
    #sortType = mw.col.conf['sortType']
    # TODO: should we avoid saving the sortType? We will continue to do
    # so unless a problem with doing so becomes evident.

    customCols = []
    origCols = []
    
    for col in self.model.activeCols:
        isOrig = True
        for type in AB.customTypes:
            if col == type:
                customCols.append(col)
                isOrig = False
                break
        if isOrig:
            origCols.append(col)

    self.model.activeCols = origCols
    mw.col.conf[CONF_KEY] = customCols


DataModel.__init__ = wrap(DataModel.__init__, myDataModel__init__)
DataModel.columnData = myColumnData
Browser.setupColumns = wrap(Browser.setupColumns, mySetupColumns)
Browser.onHeaderContext = myOnHeaderContext
Browser.closeEvent = wrap(Browser.closeEvent, myCloseEvent, "before")
Finder.findCards = myFindCards

