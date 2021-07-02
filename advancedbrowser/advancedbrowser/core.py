# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

import time

from anki.collection import BrowserColumns, Collection
from anki.hooks import runHook, wrap
from aqt import *
from aqt import gui_hooks
from aqt.browser import Browser, Column as BuiltinColumn, DataModel, SearchContext, CardState, NoteState

from . import config
from .column import Column, CustomColumn
from .contextmenu import ContextMenu


CONF_KEY_PREFIX = 'advbrowse_'


class AdvancedBrowser:
    """Maintains state for the add-on."""

    def __init__(self, mw):
        self.mw = mw
        # A list of columns to exclude when building the final column list.
        self.columnsToRemove = []
        # CustomColumn objects maintained by this add-on.
        # {type -> CustomColumn}
        self.customTypes = {}
        # Model->flds cache, similar to self.cardObjs
        self.modelFldObjs = {}

    def _load(self, browser):
        self.browser = browser
        self.table = browser.table
        self.editor = browser.editor
        self.col = browser.col

        # Let add-ons add or remove columns now.
        runHook("advBrowserLoaded", self)

        self.__removeColumns()
        self.setupColumns()

        # Workaround for double-saving (see closeEvent)
        self.saveEvent = False
        if config.getSelectable() != "No interaction":
            self.table._view.setEditTriggers(self.table._view.DoubleClicked)

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

            # Columns are a dict of str keys and builtin columns
            for column in self.table._model.columns:
                if column == type:
                    self.removedBuiltIns.append(column)
                    del self.table._model.columns[column]

            # Remove it from the active columns if it's there.
            if type in self.table._state.active_columns:
                self.table._on_column_toggled(False, type)

    def setupColumns(self):
        """Build a list of candidate columns. We extend the internal
        self.columns list with our custom types."""
        for key, column in self.customTypes.items():
            self.table._model.columns[key] = BuiltinColumn(
                key=key,
                cards_mode_label=column.name,
                notes_mode_label=column.name,
                sorting=BrowserColumns.SORTING_NORMAL if column.onSort() else BrowserColumns.SORTING_NONE,
                uses_cell_font=False,
                alignment=BrowserColumns.ALIGNMENT_CENTER,
            )

    def willSearch(self, ctx: SearchContext):
        # If the order is a custom column, apply the column's sorting
        if type(ctx.order) == BuiltinColumn and (cc := self.customTypes.get(ctx.order.key)):
            order = cc.onSort()
            if not order:
                ctx.order = None
            else:
                if self.table._state.sort_backwards:
                    order = order.replace(" asc", " desc")
                ctx.order = order

            self.time = time.time()

            # If this column relies on a temporary table for sorting, build it now
            if cc.sortTableFunction:
                cc.sortTableFunction()

    def didSearch(self, ctx: SearchContext):
        #print("Search took: %dms" % ((time.time() - self.time)*1000))
        pass

    def _column_data(self, item, is_notes_mode, row, active_columns):
        """Fill in data of custom columns."""
        c = self.table._state.get_card(item)
        n = self.table._state.get_note(item)
        for index, key in enumerate(active_columns):
            # Filter for custom types with a data function
            if (custom_type := self.customTypes.get(key)) is None:
                continue
            if custom_type.onData is None:
                continue

            # Get cell content
            try:
                row.cells[index].text = custom_type.onData(c, n, key)
            except Exception as error:
                row.cells[index].text = f"{error}"

            # Get rtl info for field cells
            if key.startswith("_field_"):
                fldName = key[7:]
                model = n.note_type()
                model_id = model["id"]
                if model_id not in self.modelFldObjs:
                    self.modelFldObjs[model_id] = {}
                if fldName not in self.modelFldObjs[model_id]:
                    flds = [f for f in model['flds'] if f['name'] == fldName]
                    if len(flds) == 0:
                        # This model does not have a field with that name
                        self.modelFldObjs[model_id][fldName] = None
                    else:
                        self.modelFldObjs[model_id][fldName] = flds[0]
                fld = self.modelFldObjs[model_id][fldName]
                row.cells[index].is_rtl = bool(fld and fld["rtl"])

    def setData(self, model, index, value, role):
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return False
        if config.getSelectable() != "Editable":
            return False
        old_value = model.get_cell(index).text
        if value == old_value:
            return False
        c = model.get_card(index)

        type = model.column_at(index).key
        if type in self.customTypes:
            r = self.customTypes[type].setData(c, value)
            if r is True:
                model.dataChanged.emit(index, index, [role])
            return r
        else:
            return False

    def _on_header_context(self, table, pos):
        """Override the original onHeaderContext. We are responsible for
        building the entire menu, so we include the original columns as
        well."""

        gpos = table._view.mapToGlobal(pos)
        main = QMenu()
        contextMenu = ContextMenu()

        # We are also a client and we need to add the built-in columns first.
        for key, column in table._model.columns.items():
            if key not in self.customTypes:
                contextMenu.addItem(Column(key, table._state.column_label(column)))

        # Now let clients do theirs.
        runHook("advBrowserBuildContext", contextMenu)

        def addCheckableAction(menu, type, name):
            a = menu.addAction(name)
            a.setCheckable(True)
            a.setChecked(table._model.active_column_index(type) is not None)
            a.toggled.connect(lambda checked, key=type: table._on_column_toggled(checked, key))

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


# Table model expansions for editable cells
################################################################################

def wrap_flags(self, index, _old):
    s = _old(self, index)
    if config.getSelectable() != "No interaction":
        s |=  Qt.ItemIsEditable
    return s


def wrap_data(self, index, role, _old):
    if role == Qt.EditRole:
        role = Qt.DisplayRole
    return _old(self, index, role)


# Config getting and setting
################################################################################

def _set_advanced_browser_card_columns(self, columns):
    self.set_config(CONF_KEY_PREFIX + "activeCols", columns)
    self._backend.set_active_browser_columns(columns)


def _set_advanced_browser_note_columns(self, columns):
    self.set_config(CONF_KEY_PREFIX + "activeNoteCols", columns)
    self._backend.set_active_browser_columns(columns)


def _load_advanced_browser_card_columns(self):
    columns = self.get_config(CONF_KEY_PREFIX + "activeCols") or self.get_config(
        "activeCols", ["noteFld", "template", "cardDue", "deck"])
    self._backend.set_active_browser_columns(columns)
    return columns


def _load_advanced_browser_note_columns(self):
    columns = self.get_config(CONF_KEY_PREFIX + "activeNoteCols") or self.get_config(
        "activeNoteCols", ["noteFld", "note", "noteCards", "noteTags"])
    self._backend.set_active_browser_columns(columns)
    return columns


class AdvancedCardState(CardState):
    def __init__(self, col):
        super().__init__(col)
        self.config_key_prefix = CONF_KEY_PREFIX + self.config_key_prefix
        self._sort_column = self.col.get_config(
            CONF_KEY_PREFIX + "sortType", self._sort_column)
        self._sort_backwards = self.col.get_config(
            CONF_KEY_PREFIX + "sortBackwards", self._sort_backwards)

    @property
    def sort_column(self) -> str:
        return self._sort_column

    @sort_column.setter
    def sort_column(self, column):
        self.col.set_config(CONF_KEY_PREFIX + "sortType", column)
        self._sort_column = column

    @property
    def sort_backwards(self) -> bool:
        return self._sort_backwards

    @sort_backwards.setter
    def sort_backwards(self, order):
        self.col.set_config(CONF_KEY_PREFIX + "sortBackwards", order)
        self._sort_backwards = order


class AdvancedNoteState(NoteState):
    def __init__(self, col):
        super().__init__(col)
        self.config_key_prefix = CONF_KEY_PREFIX + self.config_key_prefix
        # Override loaded config if there are configs for advanced browser
        self._sort_column = self.col.get_config(
            CONF_KEY_PREFIX + "noteSortType", self._sort_column)
        self._sort_backwards = self.col.get_config(
            CONF_KEY_PREFIX + "noteSortBackwards", self._sort_backwards)

    @property
    def sort_column(self) -> str:
        return self._sort_column

    @sort_column.setter
    def sort_column(self, column):
        self.col.set_config(CONF_KEY_PREFIX + "noteSortType", column)
        self._sort_column = column

    @property
    def sort_backwards(self) -> bool:
        return self._sort_backwards

    @sort_backwards.setter
    def sort_backwards(self, order):
        self.col.set_config(CONF_KEY_PREFIX + "sortBackwards", order)
        self._sort_backwards = order


################################################################################

# Override methods to use our own config keys instead, when loading or setting configs 
Collection.set_browser_card_columns = _set_advanced_browser_card_columns
Collection.set_browser_note_columns = _set_advanced_browser_note_columns
Collection.load_browser_card_columns = _load_advanced_browser_card_columns
Collection.load_browser_note_columns = _load_advanced_browser_note_columns
aqt.browser.table.state.CardState = AdvancedCardState
aqt.browser.table.state.NoteState = AdvancedNoteState

# Init AdvancedBrowser
advanced_browser = AdvancedBrowser(mw)

# Hooks
gui_hooks.browser_will_show.append(advanced_browser._load)
gui_hooks.browser_will_search.append(advanced_browser.willSearch)
gui_hooks.browser_did_search.append(advanced_browser.didSearch)
gui_hooks.browser_did_fetch_row.append(advanced_browser._column_data)

# Override table's context menu to include our own columns
aqt.browser.Table._on_header_context = lambda *args: advanced_browser._on_header_context(*args)

# Override table model flags to make cells editable if applicable
DataModel.flags = wrap(DataModel.flags, wrap_flags, "around")

# Override table model data to return data in case of edit role
DataModel.data = wrap(DataModel.data, wrap_data, "around")

# Add setData() to table model (Qt API)
DataModel.setData = lambda *args: advanced_browser.setData(*args)
