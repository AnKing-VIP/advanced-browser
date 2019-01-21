import aqt
from aqt import mw

found = False
singleList = False
def getEachFieldInSingleList():
    global singleList, found
    if not found:
        found = True
        userOption = aqt.mw.addonManager.getConfig(__name__)
        singleList = userOption.get("Use a single list for fields", False)
    return singleList

def update(_):
    global found
    found = False
mw.addonManager.setConfigUpdatedAction(__name__,update)

