# -*- coding: utf-8 -*-
# Version: 0.1alpha3
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

import time

from aqt import *
from anki.hooks import addHook
try:
    import advanced_browser
except:
    print "Failed to import. Module loaded before advanced_browser."
    pass


# Dictionary of field names indexed by "type" name. Used to figure out if
# the requested column is a note field.
# {type -> name}
_fieldTypes = {}

# Dictionary of dictionaries to get position for field in model.
# We build this dictionary once to avoid needlessly finding the field order
# for every single row when sorting. It's significantly faster that way.
# { mid -> {fldName -> pos}}
_modelFieldPos = {}

# Keep a copy of CustomColumns managed by this module. We use this
# collection to decide how to build the context menu.
_customColumns = []

## Let's use our own HTML-stipping function for now until the improved
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

#################

def onLoad():
    print "advanced_browser_custom_fields: onLoad"
    # Create a new SQL function that we can use in our queries.
    mw.col.db._db.create_function("valueForField", 3, valueForField)

def valueForField(mid, flds, fldName):
    """
    SQLite function to get the value of a field, given a field name and
    the model id for the note.
    
    mid is the model id. The model contains the definition of a note,
    including the names of all fields.
    
    flds contains the text of all fields, delimited by the character
    "x1f". We split this and index into it according to a precomputed
    index for the model (mid) and field name (fldName).
    
    fldName is the field name we are after.
    """

    index = _modelFieldPos.get(mid).get(fldName, None)
    if index is not None:
        fieldsList = flds.split("\x1f", index+1)
        #return anki.utils.stripHTML(fieldsList[index])
        return stripHTML(fieldsList[index])


def buildKnownModels():
    global _fieldTypes
    global _modelFieldPos

    for model in mw.col.models.all():
        # For some reason, some mids return as unicode, so convert to int
        mid = int(model['id'])
        _modelFieldPos[mid] = {}
        for field in model['flds']:
            name = field['name']
            ord = field['ord']
            type = "_field_"+name #prefix to avoid potential clashes
            _modelFieldPos[mid][name] = ord
            if type not in _fieldTypes:
                _fieldTypes[type] = name    


def onBuildContextMenu():
    """
    Build our part of the browser columns context menu. Decide which
    columns to show.
    
    Currently, we show all "useful" fields in the top-level menu and
    all note fields in a submenu.
    """
    
    # Model might have changed. Ensure we only offer existing columns.
    buildKnownModels()
    
    fldGroup = advanced_browser.ContextColumnGroup("Fields")
    for column in _customColumns:
        if column.type in _fieldTypes:
            fldGroup.addItem(column)
        else:
            advanced_browser.addContextItem(column)
    
    advanced_browser.addContextItem(fldGroup)
    

def onAdvBrowserLoad():
    """
    Called when the Advanced Browser add-on has finished loading.
    
    Create and add all custom columns owned by this add-on.
    """
    global _customColumns
    import advanced_browser
    from advanced_browser import CustomColumn
    
    # First review
    def cFirstOnData(c, n, t):
        first = mw.col.db.scalar(
            "select min(id) from revlog where cid = ?", c.id)
        if first:
            return time.strftime("%Y-%m-%d", time.localtime(first / 1000))
   
    _customColumns.append(CustomColumn(
        type = 'cfirst',
        name = 'First Review',
        onData = cFirstOnData,
        onSort = lambda: "(select min(id) from revlog where cid = c.id)"
    ))

    
    # Last review
    def cLastOnData(c, n, t):
        last = mw.col.db.scalar(
            "select max(id) from revlog where cid = ?", c.id)
        if last:
            return time.strftime("%Y-%m-%d", time.localtime(last / 1000))
   
    _customColumns.append(CustomColumn(
        type = 'clast',
        name = 'Last Review',
        onData = cLastOnData,
        onSort = lambda: "(select max(id) from revlog where cid = c.id)"
    ))

    
    # Average time
    def cAvgtimeOnData(c, n, t):
        avgtime = mw.col.db.scalar(
            "select avg(time) from revlog where cid = ?", c.id)
        if avgtime:
            return str(round(avgtime / 1000, 1)) + "s"
    
    _customColumns.append(CustomColumn(
        type = 'cavgtime',
        name = 'Time (Average)',
        onData = cAvgtimeOnData,
        onSort = lambda: "(select avg(time) from revlog where cid = c.id)"
    ))    


    # Total time
    def cTottimeOnDAta(c, n, t):
        tottime = mw.col.db.scalar(
            "select sum(time) from revlog where cid = ?", c.id)
        if tottime:
            return str(round(tottime / 1000, 1)) + "s"

    _customColumns.append(CustomColumn(
        type = 'ctottime',
        name = 'Time (Total)',
        onData = cTottimeOnDAta,
        onSort = lambda: "(select sum(time) from revlog where cid = c.id)"
    ))

    
    # Tags
    _customColumns.append(CustomColumn(
        type = 'ntags',
        name = 'Tags',
        onData = lambda c, n, t: " ".join(str(tag) for tag in n.tags),
        onSort = lambda: "n.tags"
    ))

    
    # Note fields
    buildKnownModels()
    
    def fldOnData(c, n, t):
        field = _fieldTypes[t]
        if field in c.note().keys():
            #return anki.utils.stripHTML(c.note()[field])
            return stripHTML(c.note()[field])

    def getOnSort(f): return lambda: f
    
    for type, name in _fieldTypes.iteritems():
        srt = ("(select valueForField(mid, flds, '%s') "
               "from notes where id = c.nid)" % name)
        
        _customColumns.append(CustomColumn(
            type = type,
            name = name,
            onData = fldOnData,
            onSort = getOnSort(srt)
        ))
    
    for column in _customColumns:
        advanced_browser.addCustomColumn(column)


addHook("profileLoaded", onLoad)
addHook("advBrowserLoad", onAdvBrowserLoad)
addHook("advBrowserBuildContext", onBuildContextMenu)