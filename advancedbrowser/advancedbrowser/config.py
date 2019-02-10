import aqt
from aqt import mw
from .internal_fields import iff
from anki.hooks import addHook, remHook


singleList = False
userOption = None
def getUserOption():
    global userOption
    if userOption is None:
        userOption = aqt.mw.addonManager.getConfig(__name__)
    return userOption

def getEachFieldInSingleList():
    return getUserOption().get("Use a single list for fields", False)

def getUseAdvancedFields():
    return getUserOption().get("Show advanced fields", False)

def update(_):
    global userOption
    userOption = None
    processAdvanced()


def processAdvanced():
    fn = addHook if getUseAdvancedFields() else remHook
    fn("advBrowserLoaded", iff.onAdvBrowserLoad)
    fn("advBrowserBuildContext", iff.onBuildContextMenu)


mw.addonManager.setConfigUpdatedAction(__name__,update)
