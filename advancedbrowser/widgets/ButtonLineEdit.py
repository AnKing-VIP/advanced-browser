# Code borrowed from here:
# http://stackoverflow.com/questions/12462562/how-to-do-inside-in-qlineedit-insert-the-button-pyqt4 
# Modified for this add-on.

from PyQt4 import QtGui, QtCore

class ButtonLineEdit(QtGui.QLineEdit):
    buttonClicked = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None):
        super(ButtonLineEdit, self).__init__(parent)
        
        self.button = QtGui.QToolButton(self)
        self.button.setStyleSheet('border: 0px;')
        self.button.setCursor(QtCore.Qt.ArrowCursor)
        self.button.clicked.connect(self.buttonClicked.emit)

    def resizeEvent(self, event):
        buttonSize = self.button.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.button.move(self.rect().right() - frameWidth - buttonSize.width(),
                         (self.rect().bottom() - buttonSize.height() + 1)/2)
        super(ButtonLineEdit, self).resizeEvent(event)

    def setIcon(self, icon):
        self.button.setIcon(icon)