# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

# Basic fields which are not sortable in anki

from aqt import mw
from aqt.main import AnkiQt
from anki.consts import *
from anki.hooks import addHook, wrap
from anki.utils import htmlToTextLine

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
            onData=lambda card, n, t: card.templateName() + (f" {card.ord+1}" if card.model()['type'] == MODEL_CLOZE else ""),
            onSort=lambda:"nameByMidOrd(n.mid, c.ord)",
        )
        self.customColumns.append(cc)
        cc = advBrowser.newCustomColumn(
            type="noteTags",
            name="Tags",
            onData=lambda card, n, t: " ".join(card.note().tags),
            onSort=lambda:"n.tags",
        )
        self.customColumns.append(cc)
        cc = advBrowser.newCustomColumn(
            type="note",
            name="Note",
            onData=lambda card, n, t: card.model()['name'],
            onSort=lambda:"nameByMid(n.mid)",
        )
        self.customColumns.append(cc)

        cc = advBrowser.newCustomColumn(
            type="deck",
            name="Deck",
            onData=lambda card, n, t: f"{mw.col.decks.name(card.did)} ({mw.col.decks.name(card.odid)})" if card.odid else mw.col.decks.name(card.did),
            onSort=lambda:"nameForDeck(c.did)",
           )
        self.customColumns.append(cc)

        cc = advBrowser.newCustomColumn(
            type="question",
            name="Question",
            onData=lambda card, n, t: htmlToTextLine(card.q(browser=True)),
            onSort=lambda:"questionContentByCid(c.id)"
           )
        self.customColumns.append(cc)

        cc = advBrowser.newCustomColumn(
            type="answer",
            name="Answer",
            onData=lambda card, n, t: htmlToTextLine(card.a()),
            onSort=lambda:"answerContentByCid(c.id)"
           )
        self.customColumns.append(cc)

    def myLoadCollection(self, _self):
        """Wrap collection load so we can add our custom DB function.
        We do this here instead of on startup because the collection
        might get closed/reopened while Anki is still open (e.g., after
        sync), which clears the DB function we added."""

        # Create a new SQL function that we can use in our queries.
        mw.col.db._db.create_function("answerContentByCid", 1, lambda cid: htmlToTextLine(mw.col.getCard(cid).a()))
        mw.col.db._db.create_function("questionContentByCid", 1, lambda cid: htmlToTextLine(mw.col.getCard(cid).q(browser=True)))
        mw.col.db._db.create_function("nameForDeck", 1, self.nameForDeck)
        mw.col.db._db.create_function("nameByMid", 1, self.nameByMid)
        mw.col.db._db.create_function("nameByMidOrd", 2, self.nameByMidOrd)

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
            return templates[0]['name']+ f" {ord+1}"
        else:
            template = templates[ord]
            return template['name']

bf = BasicFields()
addHook("advBrowserLoaded", bf.onAdvBrowserLoad)
AnkiQt.loadCollection = wrap(AnkiQt.loadCollection, bf.myLoadCollection)
