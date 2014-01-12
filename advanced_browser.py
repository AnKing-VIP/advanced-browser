# -*- coding: utf-8 -*-
# Version: 1.3.1
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

from anki.hooks import addHook
from aqt import mw

from advancedbrowser.core import AdvancedBrowser

from advancedbrowser import custom_fields
from advancedbrowser import saved_filters

# Uncomment the next line to include internal fields (card/note/model IDs, etc)
#from advancedbrowser import internal_fields

def onLoad():
    # TODO: Remove this in next major version
    # Remove any saved data from the internal_fields_in_browser add-on that
    # this add-on replaces. Don't let them interfere with each other.
    mw.col.conf.pop('ifib_activeCols', None)


# Do any important work when the collection loads.
addHook("profileLoaded", onLoad)
