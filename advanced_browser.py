# -*- coding: utf-8 -*-
# Version: 1.5.2
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
    # Move saved filters to built-in setting
    transferSavedFilters()

def transferSavedFilters():
    """Courtesy upgrade of saved filter setting. Move them out of this
    add-on and into the built-in setting."""
    
    d = mw.pm.profile.get('ab_saved_filters', {})
    if d:
        # Add conf if missing (i.e., first run)
        if not mw.col.conf.has_key('savedFilters'):
            mw.col.conf['savedFilters'] = {}

        # Transfer filters to collection conf
        for key, value in d.iteritems():
            mw.col.conf['savedFilters'][key] = value
        
        # Remove local conf
        mw.pm.profile.pop('ab_saved_filters')

# Do any important work when the collection loads.
addHook("profileLoaded", onLoad)
