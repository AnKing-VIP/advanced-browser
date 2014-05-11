# -*- coding: utf-8 -*-
# Version: 1.4b1
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

from anki.hooks import addHook
from aqt import mw
from advancedbrowser.core import AdvancedBrowser

# Advanced Browser modules
from advancedbrowser import custom_fields
from advancedbrowser import note_fields

# Uncomment the next line to include internal fields (card/note/model IDs, etc)
#from advancedbrowser import internal_fields

def onLoad():
    # TODO: Transfer saved filters to built-in version.
    pass


# Do any important work when the collection loads.
addHook("profileLoaded", onLoad)
