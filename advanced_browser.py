# -*- coding: utf-8 -*-
# Version: 1.0
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

from anki.hooks import addHook, runHook
from aqt import mw

from advancedbrowser.core import AdvancedBrowser
from advancedbrowser import custom_fields

# Uncomment this if you want internal fields (card/note/model IDs, etc)
#from advancedbrowser import internal_fields

def onLoad():
    
    # TODO: Remove this in next major version
    # Remove any saved data from the internal_fields_in_browser add-on that
    # this add-on replaces. Don't let them interfere with each other.
    mw.col.conf.pop('ifib_activeCols', None)
    
    advBrowser = AdvancedBrowser()
    
    # Signal that the add-on has loaded. Other add-ons can add their
    # own columns through this hook.
    runHook("advBrowserLoaded", advBrowser)


# Set up Advanced Browser after profile load so we have a guarantee
# that other add-ons have been imported. It also means we set up a
# new Advanced Browser and discard the state of the old one (on a
# profile switch, for example).
addHook("profileLoaded", onLoad)
