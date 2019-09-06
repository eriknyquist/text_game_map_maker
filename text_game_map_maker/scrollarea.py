from PyQt5 import QtWidgets, QtCore, QtGui

# Custom QScrollArea that ignores mouse wheel events
class ScrollArea(QtWidgets.QScrollArea):
    LEFT = 0
    RIGHT = 1
    TOP = 2
    BOTTOM = 3

    def __init__(self, parent=None):
        super(ScrollArea, self).__init__(parent)
        self.border_width = 50
        self.timer_delay_ms = 33
        self.increment = 15
        self.scroll_directions = []

        self.mouse_timer = QtCore.QTimer(self)
        self.mouse_timer.timeout.connect(self.updateScrollbars)
        self.mouse_timer.start(100)

    def wheelEvent(self, ev):
        if ev.type() == QtCore.QEvent.Wheel:
            ev.ignore()

    def leaveEvent(self, e):
        if self.mouse_timer.isActive():
            self.mouse_timer.stop()

    def mouseMoveEvent(self, event):
        new_dirs = self.checkScrollBorders(event.pos().x(), event.pos().y())
        if new_dirs == self.scroll_directions:
            return

        self.scroll_directions = new_dirs
        if not new_dirs:
            self.mouse_timer.stop()
            return

        self.mouse_timer.start(self.timer_delay_ms)

    def checkScrollBorders(self, x, y):
        width = self.frameGeometry().width()
        height = self.frameGeometry().height()
        ret = []

        if x < self.border_width:
            ret.append(self.LEFT)

        if x > (width - self.border_width):
            ret.append(self.RIGHT)

        if y < self.border_width:
            ret.append(self.TOP)

        if y > (height - self.border_width):
            ret.append(self.BOTTOM)

        return ret

    def updateScrollbars(self):
        if self.LEFT in self.scroll_directions:
            curr = self.horizontalScrollBar().value()
            self.horizontalScrollBar().setValue(max(0, curr - self.increment))

        if self.RIGHT in self.scroll_directions:
            max_value = self.horizontalScrollBar().maximum()
            curr = self.horizontalScrollBar().value()
            self.horizontalScrollBar().setValue(min(max_value, curr + self.increment))

        if self.TOP in self.scroll_directions:
            curr = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(max(0, curr - self.increment))

        if self.BOTTOM in self.scroll_directions:
            max_value = self.verticalScrollBar().maximum()
            curr = self.verticalScrollBar().value()
            self.verticalScrollBar().setValue(min(max_value, curr + self.increment))

    def setMouseTracking(self, flag):
        def recursive_set(parent):
            for child in parent.findChildren(QtCore.QObject):
                try:
                    child.setMouseTracking(flag)
                except:
                    pass
                recursive_set(child)

        super(ScrollArea, self).setMouseTracking(flag)
        recursive_set(self)
