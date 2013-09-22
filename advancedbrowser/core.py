# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

import time
from operator import  itemgetter

from aqt import *
from aqt.browser import DataModel, Browser
from anki.hooks import runHook
from anki.find import Finder
from advancedbrowser.contextmenu import ContextMenu
from advancedbrowser.column import Column, CustomColumn

CONF_KEY = 'advbrowse_activeCols'

class AdvancedDataModel(DataModel):
    
    def __init__(self, browser):
        """Load any custom columns that were saved in a previous session."""
        super(AdvancedDataModel, self).__init__(browser)

        # Keep a copy of functions we are overriding since we still use them.
        self._columnData = DataModel.columnData

        # First, we make sure those columns are still valid. If not, we ignore
        # them. This is to guard against the event that we remove or rename a
        # column. Also make sure the sortType is set to a valid column.
        
        sortType = mw.col.conf['sortType']
        validSortType = False
        custCols = mw.col.conf.get(CONF_KEY, [])
        
        for custCol in custCols:
            for type in self.browser.customTypes:
                if custCol == type and custCol not in self.activeCols:
                    self.activeCols.append(custCol)
                if sortType == type:
                    validSortType = True
        
        if not validSortType:
            mw.col.conf['sortType'] = 'noteFld'
            # Guarantee that we always start with at least one column.
            if 'noteFld' not in self.activeCols:
                self.activeCols.append('noteFld')

    def columnData(self, index):
        # Try to handle built-in Anki column
        returned = self._columnData(self, index)
        if returned:
            return returned
        
        # If Anki can't handle it, it must be one of ours.
        col = index.column()
        type = self.columnType(col)
        c = self.getCard(index)
        n = c.note()
        
        if type in self.browser.customTypes:
            return self.browser.customTypes[type].onData(c, n, type)
    
    def search(self, txt, reset=True):
        """This is a direct copy of DataModel.search but instead calls
        our custom findCards instead of the built-in one."""
        if reset:
            self.beginReset()
        self.cards = []
        self.cards = self.myFindCards(txt)
        if reset:
            self.endReset()

    def myFindCards(self, query):
        """This function takes over the call chain of
        Collection.findCards -> Finder.findCards but only handles custom
        columns maintained by the add-on. If we find that the column
        to be sorted is a built-in column, we defer to the original
        Finder.findCards.
        
        Our version differs in its approach by building a more
        efficiently sortable query for the cases where it makes sense
        to do so."""
        
        finder = anki.find.Finder(self.col)
        cTypes = self.browser.customTypes

        # If the column is not a custom one handled by this add-on, do it
        # internally.
        type = self.col.conf['sortType']
        if type not in cTypes:
            return finder.findCards(query, order=True)
        
        # We bypass _query() and _order and write our own combined version
        #
        # NOTE: the "order by x is null, x is '', x is X" pattern is to
        # ensure null values and empty strings are sorted after useful
        # values. The default is to place them first, which we don't want.
        
        tokens = finder._tokenize(query)
        preds, args = finder._where(tokens)
        if preds is None:
            return []
    
        if preds:
            preds = "(" + preds + ")"
        else:
            preds = "1"
        
        order = cTypes[type].onSort()
                
        t = time.time()
        drop = False
        
        if not order:
            print "NO SORT PATH"
    
            if "n." not in preds:
                sql = "select c.id from cards c where "
            else:
                sql = "select c.id from cards c, notes n where c.nid=n.id and "
            sql += preds
        elif cTypes[type].cacheSortValue or "select" in order.lower():
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

class AdvancedBrowser(Browser):
    """Maintains state for the add-on."""
    
    def newBrowserInit(self, mw):
        """Init stub to allow us to construct a Browser without doing
        the setup until we need to."""
        QMainWindow.__init__(self, None, Qt.Window)
    
    def __init__(self, mw):
        # Override Browser __init_. We manually invoke the original after
        # we use our stub one. This is to work around the fact that super
        # needs to be called on Browser before its methods can be invoked,
        # which add-ons need to do in the hook.
        origInit = Browser.__init__
        Browser.__init__ = self.newBrowserInit
        super(AdvancedBrowser, self).__init__(mw)
        
        # A list of columns to exclude when building the final column list.
        self.columnsToRemove = []
        
        # CustomColumn objects maintained by this add-on.
        # {type -> CustomColumn}
        self.customTypes = {}
        
        # Let add-ons add or remove columns now.
        runHook("advBrowserLoaded", self)
        
        # Build the actual browser, which now has our state in it,
        # and restore constructor.
        origInit(self, mw)
        Browser.__init__ = origInit
        
        # Remove excluded columns after the browser is built. Doing it here
        # is mostly a compromise in complexity. The alternative is to
        # rewrite the order of the original __init__ method, which is
        # cumbersome and error-prone.
        self.__removeColumns()
       
    def newCustomColumn(self, type, name, onData, onSort=None,
                 cacheSortValue=False):
        """Add a CustomColumn to the browser. See CustomColumn for a
        detailed description of the parameters."""
        cc = CustomColumn(type, name, onData, onSort, cacheSortValue)
        self.customTypes[cc.type] = cc
        return cc
    
    def removeColumn(self, type):
        """Remove a column from the columns list so that it will not appear
        in the browser. Applies to built-in or custom columns."""
        self.columnsToRemove.append(type)

    def __removeColumns(self):
        for type in self.columnsToRemove:
            # Remove from ours
            if type in self.customTypes:
                self.customTypes.pop(type, None)
            
            # Built-in list is a list of tuple.
            for tup in list(self.columns):
                if tup[0] == type:
                    self.columns.remove(tup)
            
            # Remove it from the active columns if it's there.
            if type in self.model.activeCols:
                self.toggleField(type)

    def setupColumns(self):
        """Build a list of candidate columns. We extend the internal
        self.columns list with our custom types."""
        super(AdvancedBrowser, self).setupColumns()
        for type in self.customTypes:
            self.columns.append((self.customTypes[type].type,
                                 self.customTypes[type].name))
        self.columns.sort(key=itemgetter(1))
    
    def onHeaderContext(self, pos):
        """Override the original onHeaderContext. We are responsible for
        building the entire menu, so we include the original columns as
        well."""
        
        gpos = self.form.tableView.mapToGlobal(pos)
        main = QMenu()
        contextMenu = ContextMenu()
        
        # We are also a client and we need to add the built-in columns first.
        for item in self.columns:
            type, name = item
            if type not in self.customTypes:
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

    def closeEvent(self, evt):
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
            for type in self.customTypes:
                if col == type:
                    customCols.append(col)
                    isOrig = False
                    break
            if isOrig:
                origCols.append(col)
    
        self.model.activeCols = origCols
        mw.col.conf[CONF_KEY] = customCols
        # Let Anki do its stuff now
        super(AdvancedBrowser, self).closeEvent(evt)


# Override DataModel with our subclass
aqt.browser.DataModel = AdvancedDataModel

# Make Anki load AdvancedBrowser instead of the original Browser
aqt.dialogs._dialogs['Browser'] = [AdvancedBrowser, None]
