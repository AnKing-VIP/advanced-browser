# -*- coding: utf-8 -*-
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

import time

from aqt import *
from anki.hooks import addHook, wrap
from aqt.browser import Browser

#######################################################################
## Let's use our own HTML-stripping function for now until the improved
## version is merged upstream. This should be quite a bit faster.
import re, htmlentitydefs

reStyle = re.compile("(?s)<style.*?>.*?</style>")
reScript = re.compile("(?s)<script.*?>.*?</script>")
reTag = re.compile("<.*?>")
reEnts = re.compile("&#?\w+;")
reMedia = re.compile("<img[^>]+src=[\"']?([^\"'>]+)[\"']?[^>]*>")

def stripHTML(s):
    s = reStyle.sub("", s)
    s = reScript.sub("", s)
    s = reTag.sub("", s)
    s = entsToTxt(s)
    return s

def entsToTxt(html):
    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text # leave as is
    return reEnts.sub(fixup, html)
#######################################################################


class CustomFields:

    def __init__(self):
        
        # Dictionary of field names indexed by "type" name. Used to
        # figure out if the requested column is a note field.
        # {type -> name}
        self.fieldTypes = {}

        # Dictionary of dictionaries to get position for field in model.
        # We build this dictionary once to avoid needlessly finding the
        # field order for every single row when sorting. It's
        # significantly faster that way.
        # { mid -> {fldName -> pos}}
        self.modelFieldPos = {}

        # Keep a copy of CustomColumns managed by this module. We use
        # this collection to decide how to build the context menu.
        self.customColumns = []

    def buildKnownModels(self):
        for model in mw.col.models.all():
            # For some reason, some mids return as unicode, so convert to int
            mid = int(model['id'])
            # And some platforms get a signed 32-bit integer from SQlite, so
            # we will also provide an index to that as a workaround.
            mid32 = (mid + 2**31) % 2**32 - 2**31
            self.modelFieldPos[mid] = {}
            self.modelFieldPos[mid32] = {}
            for field in model['flds']:
                name = field['name']
                ord = field['ord']
                type = "_field_"+name  #prefix to avoid potential clashes
                self.modelFieldPos[mid][name] = ord
                self.modelFieldPos[mid32][name] = ord
                if type not in self.fieldTypes:  #avoid dupes
                    self.fieldTypes[type] = name
    
    def onAdvBrowserLoad(self, advBrowser):
        """Called when the Advanced Browser add-on has finished
        loading. Create and add all custom columns owned by this
        module.
        
        """

        # Clear existing state
        self.fieldTypes = {}
        self.modelFieldPos = {}
        self.customColumns = []

        # First review
        def cFirstOnData(c, n, t):
            first = mw.col.db.scalar(
                "select min(id) from revlog where cid = ?", c.id)
            if first:
                return time.strftime("%Y-%m-%d", time.localtime(first / 1000))
       
        cc = advBrowser.newCustomColumn(
            type = 'cfirst',
            name = 'First Review',
            onData = cFirstOnData,
            onSort = lambda: "(select min(id) from revlog where cid = c.id)"
        )
        self.customColumns.append(cc)


        # Last review
        def cLastOnData(c, n, t):
            last = mw.col.db.scalar(
                "select max(id) from revlog where cid = ?", c.id)
            if last:
                return time.strftime("%Y-%m-%d", time.localtime(last / 1000))
       
        cc = advBrowser.newCustomColumn(
            type = 'clast',
            name = 'Last Review',
            onData = cLastOnData,
            onSort = lambda: "(select max(id) from revlog where cid = c.id)"
        )
        self.customColumns.append(cc)
    
        
        # Average time
        def cAvgtimeOnData(c, n, t):
            avgtime = mw.col.db.scalar(
                "select avg(time) from revlog where cid = ?", c.id)
            if avgtime:
                return str(round(avgtime / 1000, 1)) + "s"
        
        cc = advBrowser.newCustomColumn(
            type = 'cavgtime',
            name = 'Time (Average)',
            onData = cAvgtimeOnData,
            onSort = lambda: "(select avg(time) from revlog where cid = c.id)"
        )
        self.customColumns.append(cc)
    
    
        # Total time
        def cTottimeOnDAta(c, n, t):
            tottime = mw.col.db.scalar(
                "select sum(time) from revlog where cid = ?", c.id)
            if tottime:
                return str(round(tottime / 1000, 1)) + "s"
    
        cc = advBrowser.newCustomColumn(
            type = 'ctottime',
            name = 'Time (Total)',
            onData = cTottimeOnDAta,
            onSort = lambda: "(select sum(time) from revlog where cid = c.id)"
        )
        self.customColumns.append(cc)
        
        
        # Tags
        cc = advBrowser.newCustomColumn(
            type = 'ntags',
            name = 'Tags',
            onData = lambda c, n, t: " ".join(unicode(tag) for tag in n.tags),
            onSort = lambda: "n.tags"
        )
        self.customColumns.append(cc)
        
        
        # Note fields
        self.buildKnownModels()
        
        def fldOnData(c, n, t):
            field = self.fieldTypes[t]
            if field in c.note().keys():
                #return anki.utils.stripHTML(c.note()[field])
                return stripHTML(c.note()[field])
    
        def getOnSort(f): return lambda: f
        
        for type, name in self.fieldTypes.iteritems():
            srt = ("(select valueForField(mid, flds, '%s') "
                   "from notes where id = c.nid)" % name)
            
            cc = advBrowser.newCustomColumn(
                type = type,
                name = name,
                onData = fldOnData,
                onSort = getOnSort(srt)
            )
            self.customColumns.append(cc)

    def onBuildContextMenu(self, contextMenu):
        """Build our part of the browser columns context menu. Decide
        which columns to show.
        
        Currently, we show all "useful" columns in the top-level menu
        and all note fields in a submenu.
        
        """
        
        # Model might have changed. Ensure we only offer existing columns.
        self.buildKnownModels()
        
        fldGroup = contextMenu.newSubMenu("Fields")
        for column in self.customColumns:
            if column.type in self.fieldTypes:
                fldGroup.addItem(column)
            else:
                contextMenu.addItem(column)

    def valueForField(self, mid, flds, fldName):
        """Function called from SQLite to get the value of a field,
        given a field name and the model id for the note.
        
        mid is the model id. The model contains the definition of a note,
        including the names of all fields.
        
        flds contains the text of all fields, delimited by the character
        "x1f". We split this and index into it according to a precomputed
        index for the model (mid) and field name (fldName).
        
        fldName is the name of the field we are after.
        
        """
    
        try:
            index = self.modelFieldPos.get(mid).get(fldName, None)
            if index is not None:
                fieldsList = flds.split("\x1f", index+1)
                #return anki.utils.stripHTML(fieldsList[index])
                return stripHTML(fieldsList[index])
        except Exception, e:
            print "Failed to get value for field."
            print "Mid:" + (mid or 'None')
            print "flds" + (flds or 'None')
            print "fldName" + (fldName or 'None')
            print "_modelFieldPos" + self.modelFieldPos
            print "Error was: " + e.message

cf = CustomFields()

def myBrowser__init__(self, browser):
    """Wrap Browser's init so we can add our custom DB function. We
    do this here instead of on startup because the collection might get
    closed/reopened while Anki is still open (e.g., after sync), which
    clears the DB function we added. Doing it here ensures we always
    have the function when the browser opens.
    
    """

    # Create a new SQL function that we can use in our queries.
    mw.col.db._db.create_function("valueForField", 3, cf.valueForField)


addHook("advBrowserLoaded", cf.onAdvBrowserLoad)
addHook("advBrowserBuildContext", cf.onBuildContextMenu)
Browser.__init__ = wrap(Browser.__init__, myBrowser__init__)
