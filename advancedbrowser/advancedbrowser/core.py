# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

import time
from PyQt5 import QtWidgets
from anki.hooks import runHook
from aqt import *
from aqt import gui_hooks
from aqt.browser import Browser, DataModel, SearchContext, StatusDelegate
from operator import itemgetter

from . import config
from .column import Column, CustomColumn
from .contextmenu import ContextMenu

CONF_KEY = 'advbrowse_activeCols'


class AdvancedDataModel(DataModel):

    def __init__(self, browser):
        """Load our copy of the active columns and suppress the built-in one.

        This function runs after custom columns have been registered, so our
        list of custom types has already been populated."""
        super(AdvancedDataModel, self).__init__(browser)

        gui_hooks.browser_will_search.append(self.willSearch)
        gui_hooks.browser_did_search.append(self.didSearch)

        # Keep a reference to this function; we need the original later
        self._columnData = DataModel.columnData

        # Model->flds cache, similar to self.cardObjs
        self.modelFldObjs = {}

        # Keep a copy of the original active columns to restore on closing.
        self.origActiveCols = list(self.activeCols)

        configuredCols = self.browser.mw.col.get_config(CONF_KEY)
        if configuredCols:
            # We've used this add-on before and have a configured list of columns.
            # Adjust activeCols to reflect it.

            # Make sure the columns we are loading are still valid. If not, we
            # just ignore them. This guards against the event that a column is
            # removed or renamed.
            #
            # The list of valid columns are the built-in ones + our custom ones.
            valids = set([c[0] for c in browser.columns] +
                         list(browser.customTypes.keys()))

            self.activeCols = [col for col in configuredCols if col in valids]

            # Also make sure the sortType is valid
            if self.browser.mw.col.get_config('sortType') not in valids:
                self.browser.mw.col.set_config('sortType', 'noteFld')
                # If there is no sorted column, we add the 'Sort Field' column
                # and sort on that. This method is one way to guarantee that we
                # always start with at least one valid column.
                if 'noteFld' not in self.activeCols:
                    self.activeCols.append('noteFld')

    def getFld(self, index):
        """"
        Field cache, similar to getCard().
        This method only exists to make fetching field settings efficient in
        order to determine if it is RTL.
        """
        model = self.getCard(index).note().model()
        id = model['id']
        fldName = self.activeCols[index.column()]
        if fldName.startswith("_field_"):
            fldName = fldName[7:]
        else:
            # This custom column is not a field column
            return None
        if id not in self.modelFldObjs:
            self.modelFldObjs[id] = {}
        if fldName not in self.modelFldObjs[id]:
            flds = [f for f in model['flds'] if f['name'] == fldName]
            if len(flds) == 0:
                # This model does not have a field with that name
                self.modelFldObjs[id][fldName] = None
            else:
                self.modelFldObjs[id][fldName] = flds[0]
        return self.modelFldObjs[id][fldName]

    def data(self, index, role):
        if role == Qt.TextAlignmentRole:
            col = self.activeCols[index.column()]
            if col in self.browser.customTypes:
                # If this is one of our columns, use custom alignment rules
                align = Qt.AlignVCenter | Qt.AlignLeft
                return align
        return super(AdvancedDataModel, self).data(index, role)

    def columnData(self, index):
        # Try to handle built-in Anki column
        returned = self._columnData(self, index)
        if returned is not None:
            return returned

        # If Anki can't handle it, it must be one of ours.
        col = index.column()
        type = self.columnType(col)
        c = self.getCard(index)
        n = c.note()

        if type in self.browser.customTypes:
            return self.browser.customTypes[type].onData(c, n, type)

    def willSearch(self, ctx: SearchContext):
        # If the column is not a custom one handled by this add-on, do it
        # internally.
        cTypes = self.browser.customTypes
        type = self.col.get_config('sortType')
        if type not in cTypes:
            return

        cc = cTypes[type]
        order = cc.onSort()
        if not order:
            ctx.order = None
        else:
            if self.col.get_config('sortBackwards'):
                order = order.replace(" asc", " desc")
            ctx.order = order

        self.time = time.time()

        # If this column relies on a temporary table for sorting, build it now
        if cc.sortTableFunction:
            cc.sortTableFunction()



    def didSearch(self, ctx: SearchContext):
        #print("Search took: %dms" % ((time.time() - self.time)*1000))
        pass


    def flags(self, index):
        s = super().flags(index)
        if config.getSelectable() != "No interaction":
            s = s | Qt.ItemIsEditable
        return s

    def setData(self, index, value, role):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return False
        old_value = self.columnData(index)
        if value == old_value:
            return False
        col = index.column()
        c = self.getCard(index)

        type = self.columnType(col)
        if type in self.browser.customTypes:
            r = self.browser.customTypes[type].setData(c, value)
            if r is True:
                self.dataChanged.emit(index, index, [role])
            return r
        else:
            return False


class AdvancedStatusDelegate(StatusDelegate):
    def paint(self, painter, option, index):
        fld = self.browser.model.getFld(index)
        if fld and fld['rtl']:
            option.direction = Qt.RightToLeft
        return super(AdvancedStatusDelegate, self).paint(painter, option, index)


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

        # Workaround for double-saving (see closeEvent)
        self.saveEvent = False
        if config.getSelectable() == "Editable":
            self.form.tableView.setEditTriggers(
                QtWidgets.QAbstractItemView.DoubleClicked)

    def newCustomColumn(self, type, name, onData, onSort=None,
                        setData=None, sortTableFunction=False):
        """Add a CustomColumn to the browser. See CustomColumn for a
        detailed description of the parameters."""
        cc = CustomColumn(type, name, onData, onSort,
                          sortTableFunction, setData=setData)
        self.customTypes[cc.type] = cc
        return cc

    def removeColumn(self, type):
        """Remove a column from the columns list so that it will not appear
        in the browser. Applies to built-in or custom columns."""
        self.columnsToRemove.append(type)

    def __removeColumns(self):
        self.removedBuiltIns = []
        for type in self.columnsToRemove:
            # Remove from ours
            if type in self.customTypes:
                self.customTypes.pop(type, None)

            # Built-in list is a list of tuples.
            for tup in list(self.columns):
                if tup[0] == type:
                    self.removedBuiltIns.append(tup)
                    self.columns.remove(tup)

            # Remove it from the active columns if it's there.
            if type in self.model.activeCols:
                self.toggleField(type)

    def setupTable(self):
        """Some customizations to the table view"""
        super(AdvancedBrowser, self).setupTable()
        self.form.tableView.setHorizontalScrollMode(
            QAbstractItemView.ScrollPerPixel)
        self.form.tableView.setItemDelegate(
            AdvancedStatusDelegate(self, self.model))

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
            a.toggled.connect(lambda b, t=type: self.toggleField(t))

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
        """Preserve our column state in a collection preference."""

        # After we save our columns, we restore activeCols to the original
        # copy that Anki maintains and allow it to resume its own save
        # routine unhindered by our unsupported columns.
        # When the add-on resumes on next startup, we replace activecols
        # again with our own version.
        # NOTE: we use a flag to check if we have performed this action before
        # as a workaround to this function being called twice and overriding
        # the custom columns with the original columns.

        if not self.saveEvent:
            # Save ours
            self.mw.col.set_config(CONF_KEY, self.model.activeCols)
            # Restore old
            self.model.activeCols = self.model.origActiveCols
            # Restore built-in columns we removed
            self.columns.extend(self.removedBuiltIns or [])
            # Only save once
            self.saveEvent = True

        gui_hooks.browser_will_search.remove(self.model.willSearch)
        gui_hooks.browser_did_search.remove(self.model.didSearch)

        # Let Anki do its stuff now
        super(AdvancedBrowser, self).closeEvent(evt)

    def _onSortChanged(self, idx, ord):
        type = self.model.activeCols[idx]
        if type in self.customTypes:
            if self.col.get_config('sortType') == type:
                self.col.set_config('sortType', "")
        super(AdvancedBrowser, self)._onSortChanged(idx, ord)

# Override DataModel with our subclass
aqt.browser.DataModel = AdvancedDataModel

# Make Anki load AdvancedBrowser instead of the original Browser
aqt.dialogs._dialogs['Browser'] = [AdvancedBrowser, None]
