# -*- coding: utf-8 -*-
# Version: 0.1alpha4
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

from anki.hooks import addHook
import advanced_browser


class InternalFields():
    
    noteColumns = []
    cardColumns = []
    
    def onBuildContextMenu(self):
        nGroup = advanced_browser.ContextColumnGroup("Note (internal)")
        cGroup = advanced_browser.ContextColumnGroup("Card (internal)")
        
        for cc in self.noteColumns:
            nGroup.addItem(cc)
        for cc in self.cardColumns:
            cGroup.addItem(cc)
        
        advanced_browser.addContextItem(nGroup)
        advanced_browser.addContextItem(cGroup)
    
    def onAdvBrowserLoad(self):
        """
        Called when the Advanced Browser add-on has finished loading.
        
        Create and add all custom columns owned by this add-on.
        """
        
        from advanced_browser import CustomColumn
        
        self.noteColumns.append(CustomColumn(
            type = "nid",
            name = "Note ID",
            onData = lambda c, n, t: n.id,
            onSort = lambda: "n.id"
        ))
        
        self.noteColumns.append(CustomColumn(
            type = "nguid",
            name = "Note Guid",
            onData = lambda c, n, t: n.guid,
            onSort = lambda: "n.guid"
        ))
        
        self.noteColumns.append(CustomColumn(
            type = "nmid",
            name = "Model ID",
            onData = lambda c, n, t: n.mid,
            onSort = lambda: "n.mid"
        ))
       
        self.noteColumns.append(CustomColumn(
            type = "nusn",
            name = "Note USN",
            onData = lambda c, n, t: n.usn,
            onSort = lambda: "n.usn"
        ))

        self.noteColumns.append(CustomColumn(
            type = "nfields",
            name = "Note Fields",
            onData = lambda c, n, t: u"\u25A0".join(unicode(field) for field in n.fields),
            onSort = lambda: "n.flds"
        ))
        
        self.noteColumns.append(CustomColumn(
            type = "nflags",
            name = "Note Flags",
            onData = lambda c, n, t: n.flags,
            onSort = lambda: "n.flags"
        ))
        
        self.noteColumns.append(CustomColumn(
            type = "ndata",
            name = "Note Data",
            onData = lambda c, n, t: n.data,
            onSort = lambda: "n.data"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "cid",
            name = "Card ID",
            onData = lambda c, n, t: c.id,
            onSort = lambda: "c.id"
        ))

        
        self.cardColumns.append(CustomColumn(
            type = "cdid",
            name = "Deck ID",
            onData = lambda c, n, t: c.did,
            onSort = lambda: "c.did"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "codid",
            name = "Original Deck ID",
            onData = lambda c, n, t: c.odid,
            onSort = lambda: "c.odid"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "cord",
            name = "Card Ordinal",
            onData = lambda c, n, t: c.ord,
            onSort = lambda: "c.ord"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "cusn",
            name = "Card USN",
            onData = lambda c, n, t: c.usn,
            onSort = lambda: "c.usn"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "ctype",
            name = "Card Type",
            onData = lambda c, n, t: c.type,
            onSort = lambda: "c.type"
        ))

        self.cardColumns.append(CustomColumn(
            type = "cqueue",
            name = "Card Queue",
            onData = lambda c, n, t: c.queue,
            onSort = lambda: "c.queue"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "cleft",
            name = "Card Left",
            onData = lambda c, n, t: c.left,
            onSort = lambda: "c.left"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "codue",
            name = "Card Original Due",  # I think?
            onData = lambda c, n, t: c.odue,
            onSort = lambda: "c.odue"
        ))
        
        self.cardColumns.append(CustomColumn(
            type = "cflags",
            name = "Card Flags",
            onData = lambda c, n, t: c.flags,
            onSort = lambda: "c.flags"
        ))
        
        for cc in self.noteColumns + self.cardColumns:
            advanced_browser.addCustomColumn(cc)

iff = InternalFields()

addHook("advBrowserLoaded", iff.onAdvBrowserLoad)
addHook("advBrowserBuildContext", iff.onBuildContextMenu)