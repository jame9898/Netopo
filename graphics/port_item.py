from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPen, QBrush, QColor

PORT_TYPE_ETHERNET = "ethernet"
PORT_TYPE_FIBER = "fiber"
PORT_TYPE_CONSOLE = "console"
PORT_TYPE_USB = "usb"

PORT_COLORS = {
    PORT_TYPE_ETHERNET: QColor(100, 180, 100),
    PORT_TYPE_FIBER: QColor(100, 150, 200),
    PORT_TYPE_CONSOLE: QColor(180, 150, 100),
    PORT_TYPE_USB: QColor(180, 130, 180)
}

PORT_TYPE_NAMES = {
    PORT_TYPE_ETHERNET: "电口",
    PORT_TYPE_FIBER: "光口",
    PORT_TYPE_CONSOLE: "Console口",
    PORT_TYPE_USB: "USB口"
}


class PortItem(QGraphicsRectItem):
    def __init__(self, port_id: str, port_type: str = PORT_TYPE_ETHERNET, parent=None):
        super().__init__(-8, -6, 16, 12, parent)
        self.port_id = port_id
        self.port_type = port_type
        self._connected = False
        self._connection = None
        self._original_color = None
        self._flash_timer = QTimer()
        self._flash_timer.timeout.connect(self._toggle_flash)
        self._flash_state = False
        self.setFlag(QGraphicsRectItem.GraphicsItemFlag.ItemIsSelectable)
        self._update_color()
        self.setAcceptHoverEvents(True)
        self._hover = False

    def _update_color(self):
        if self._connected:
            self.setBrush(QBrush(QColor(255, 100, 0)))
        else:
            color = PORT_COLORS.get(self.port_type, QColor(0, 150, 0))
            self.setBrush(QBrush(color))
        self.setPen(QPen(QColor(30, 30, 30), 0.5))

    def is_connected(self):
        return self._connected

    def set_connected(self, connected, connection=None):
        self._connected = connected
        self._connection = connection
        self._update_color()

    def get_connection(self):
        return self._connection

    def start_flash(self):
        self._original_color = self.brush().color()
        self._flash_state = False
        self._flash_timer.start(500)

    def stop_flash(self):
        self._flash_timer.stop()
        if self._connected:
            self.setBrush(QBrush(QColor(255, 100, 0)))
        elif self._original_color:
            self.setBrush(QBrush(self._original_color))
        else:
            self._update_color()

    def _toggle_flash(self):
        self._flash_state = not self._flash_state
        if self._flash_state:
            self.setBrush(QBrush(QColor(255, 255, 0)))
        else:
            if self._original_color:
                self.setBrush(QBrush(self._original_color))
            else:
                self._update_color()

    def hoverEnterEvent(self, event):
        self._hover = True
        if not self._connected and not self._flash_timer.isActive():
            self.setBrush(QBrush(QColor(255, 255, 0)))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hover = False
        if not self._flash_timer.isActive():
            self._update_color()
        super().hoverLeaveEvent(event)
    
    def contextMenuEvent(self, event):
        parent = self.parentItem()
        if parent:
            scene = parent.scene()
            if scene and hasattr(scene, 'contextMenuEvent'):
                scene.contextMenuEvent(event)
                return
        super().contextMenuEvent(event)

    def get_global_pos(self):
        return self.scenePos()

    def get_label(self):
        node = self.parentItem()
        if node:
            return f"{node.node_id}:{self.port_id}"
        return self.port_id
