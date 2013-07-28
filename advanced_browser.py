# -*- coding: utf-8 -*-
# Version: 0.2alpha1
# See github page to report issues or to contribute:
# https://github.com/hssm/advanced-browser

from anki.hooks import addHook, runHook

from advancedbrowser.core import AdvancedBrowser
from advancedbrowser import internal_fields
from advancedbrowser import custom_fields

def onLoad():
    advBrowser = AdvancedBrowser()
    
    # Signal that the add-on has loaded. Other add-ons can add their
    # own columns through this hook.
    runHook("advBrowserLoaded", advBrowser)


# Set up Advanced Browser after profile load so we have a guarantee
# that other add-ons have been imported. It also means we set up a
# new Advanced Browser and discard the state of the old one (on a
# profile switch, for example).
addHook("profileLoaded", onLoad)
