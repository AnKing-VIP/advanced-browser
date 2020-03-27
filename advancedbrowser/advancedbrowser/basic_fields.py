# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

# Built-in columns which are not sortable by default are made sortable here.
#
# Question/Answer columns are too slow so they are not handled.
# Note: the onData function of the columns is None as the data will still
# be fetched from the original source and that function is never reached.

from anki.consts import *
from anki.hooks import addHook, wrap


class BasicFields:

    def onAdvBrowserLoad(self, advBrowser):
        """Called when the Advanced Browser add-on has finished
        loading. Create and add all custom columns owned by this
        module."""

        # Store a list of CustomColumns managed by this module. We later
        # use this to build our part of the context menu.
        self.customColumns = []

        cc = advBrowser.newCustomColumn(
            type="cardEase",
            name="Ease",
            onData=None,
            onSort=lambda: f"(case when type = {CARD_TYPE_NEW} then -1 else factor end)"
        )
        self.customColumns.append(cc)

        # fixme: to sort on this column, will need to write to a temp table
        # then sort based on that table, like in Anki's Rust code
        cc = advBrowser.newCustomColumn(
            type="odeck",
            name="Original Deck",
            onData=lambda c, n, t: advBrowser.mw.col.decks.name(c.odid),
            onSort=lambda: "c.odid",
        )
        self.customColumns.append(cc)

    def onBuildContextMenu(self, contextMenu):
        for cc in self.customColumns:
            contextMenu.addItem(cc)


bf = BasicFields()
addHook("advBrowserLoaded", bf.onAdvBrowserLoad)
addHook("advBrowserBuildContext", bf.onBuildContextMenu)
