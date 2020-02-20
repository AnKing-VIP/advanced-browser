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
from aqt import mw
from aqt.main import AnkiQt


class BasicFields:

    def onAdvBrowserLoad(self, advBrowser):
        """Called when the Advanced Browser add-on has finished
        loading. Create and add all custom columns owned by this
        module."""

        # Store a list of CustomColumns managed by this module. We later
        # use this to build our part of the context menu.
        self.customColumns = []

        cc = advBrowser.newCustomColumn(
            type="template",
            name="Card",
            onData=None,
            onSort=lambda: "nameByMidOrd(n.mid, c.ord)",
        )
        self.customColumns.append(cc)

        cc = advBrowser.newCustomColumn(
            type="noteTags",
            name="Tags",
            onData=None,
            onSort=lambda: "n.tags",
        )
        self.customColumns.append(cc)

        cc = advBrowser.newCustomColumn(
            type="note",
            name="Note",
            onData=None,
            onSort=lambda: "nameByMid(n.mid)",
        )
        self.customColumns.append(cc)

        cc = advBrowser.newCustomColumn(
            type="deck",
            name="Deck",
            onData=None,
            onSort=lambda: "nameForDeck(c.did)",
        )
        self.customColumns.append(cc)

        cc = advBrowser.newCustomColumn(
            type="cardEase",
            name="Ease",
            onData=None,
            onSort=lambda: "factorByType(c.factor, c.type)"
        )
        self.customColumns.append(cc)

    def myLoadCollection(self, _self):
        """Wrap collection load so we can add our custom DB function.
        We do this here instead of on startup because the collection
        might get closed/reopened while Anki is still open (e.g., after
        sync), which clears the DB function we added."""

        # Create a new SQL function that we can use in our queries.
        mw.col.db._db.create_function("nameForDeck", 1, self.nameForDeck)
        mw.col.db._db.create_function("nameByMid", 1, self.nameByMid)
        mw.col.db._db.create_function("nameByMidOrd", 2, self.nameByMidOrd)
        mw.col.db._db.create_function("factorByType", 2, self.factorByType)

    @staticmethod
    def nameForDeck(did):
        deck = mw.col.decks.get(did)
        if deck:
            return deck['name']
        return _("[no deck]")

    @staticmethod
    def nameByMid(mid):
        return mw.col.models.get(mid)['name']

    @staticmethod
    def nameByMidOrd(mid, ord):
        model = mw.col.models.get(mid)
        templates = model['tmpls']
        if model['type'] == MODEL_CLOZE:
            template = templates[0]
            return templates[0]['name'] + f" {ord+1}"
        else:
            template = templates[ord]
            return template['name']

    @staticmethod
    def factorByType(factor, type):
        if type == 0:
            return -1
        return factor

    def onBuildContextMenu(self, contextMenu):
        for cc in self.customColumns:
            contextMenu.addItem(cc)


bf = BasicFields()
addHook("advBrowserLoaded", bf.onAdvBrowserLoad)
addHook("advBrowserBuildContext", bf.onBuildContextMenu)
AnkiQt.loadCollection = wrap(AnkiQt.loadCollection, bf.myLoadCollection)
