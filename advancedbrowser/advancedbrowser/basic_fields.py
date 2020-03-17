# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

# Built-in columns which are not sortable by default are made sortable here.
#
# Question/Answer columns are too slow so they are not handled.
# Note: the onData function of the columns is None as the data will still
# be fetched from the original source and that function is never reached.

from anki.cards import Card
from anki.consts import *
from anki.hooks import addHook, wrap
from anki.lang import _
from aqt import mw
from aqt.main import AnkiQt
from aqt.utils import askUser


class BasicFields:

    def onAdvBrowserLoad(self, advBrowser):
        """Called when the Advanced Browser add-on has finished
        loading. Create and add all custom columns owned by this
        module."""

        # Store a list of CustomColumns managed by this module. We later
        # use this to build our part of the context menu.
        self.customColumns = []

        def setData(c: Card, value: str):
            n = c.note()
            m = n.model()
            if m["type"] == MODEL_CLOZE:
                tmpl = m["tmpls"][0]
                tmpl_name = tmpl["name"]
                if not value.startswith(tmpl_name):
                    return False
                value = value[len(tmpl_name):]
                try:
                    c.ord = int(value)-1
                except ValueError:
                    return False
            else:
                value = value.strip().lower()
                right_tmpl = None
                for tmpl in m["tmpls"]:
                    if tmpl["name"].strip().lower() == value:
                        right_tmpl = tmpl
                        break
                if right_tmpl is None:
                    return False
                c.ord = right_tmpl["ord"]
            c.flush()
            return True

        cc = advBrowser.newCustomColumn(
            type="template",
            name="Card",
            onData=None,
            onSort=lambda: "nameByMidOrd(n.mid, c.ord)",
            setData=setData,
        )
        self.customColumns.append(cc)

        def setData(c: Card, value: str):
            n = c.note()
            n.setTagsFromStr(value)
            n.flush()
            advBrowser.editor.loadNote()
            return True

        cc = advBrowser.newCustomColumn(
            type="noteTags",
            name="Tags",
            onData=None,
            onSort=lambda: "n.tags",
            setData=setData,
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

        def setData(c: Card, value: str):
            value = value.strip()
            if value.endswith("%"):
                value = value[:-1]
            try:
                f = float(value)
            except ValueError:
                return False
            c.factor = f * 10
            c.flush()
            return True

        cc = advBrowser.newCustomColumn(
            type="cardEase",
            name="Ease",
            onData=None,
            onSort=lambda: "factorByType(c.factor, c.type)",
            setData=setData,
        )
        self.customColumns.append(cc)

        def setData(c: Card, value: str):
            if not c.odid:
                # only accept to change odid if there is already one
                return False
            new_deck = c.col.decks.byName(value)
            if new_deck is None:
                if not askUser(
                        _("%s does not exists, do you want to create this deck ?") % value,
                        parent=advBrowser,
                        defaultno=True):
                    return False
                new_id = c.col.decks.id(value)
                new_deck = c.col.decks.get(new_id)
            if new_deck["dyn"] == DECK_DYN:
                return False
            c.odid = new_deck["id"]
            c.flush()
            return True

        cc = advBrowser.newCustomColumn(
            type="odeck",
            name="Original Deck",
            onData=lambda c, n, t: advBrowser.mw.col.decks.name(c.odid),
            onSort=lambda: "nameForOriginalDeck(c.odid)",
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
        mw.col.db._db.create_function(
            "nameForOriginalDeck", 1, self.nameForOriginalDeck)

    @staticmethod
    def nameForDeck(did):
        deck = mw.col.decks.get(did)
        if deck:
            return deck['name']
        return _("[no deck]")

    @staticmethod
    def nameForOriginalDeck(odid):
        deck = mw.col.decks.get(odid)
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
