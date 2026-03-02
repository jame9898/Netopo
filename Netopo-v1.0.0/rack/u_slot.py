from PySide6.QtWidgets import QGraphicsRectItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QColor, QFont, QPainter


class USlot(QGraphicsRectItem):
    def __init__(self, u_number: int, parent=None):
        from .rack_device import U_HEIGHT_PX, RACK_WIDTH_PX
        
        super().__init__(0, 0, RACK_WIDTH_PX - 20, U_HEIGHT_PX, parent)
        
        self.u_number = u_number
        self._is_occupied = False
        self._device_id = None
        self._device_type = None
        self._device_color = None
        
        self.setPen(QPen(QColor(100, 100, 100), 1))
        self.setBrush(Qt.BrushStyle.NoBrush)
        self.setZValue(1)
        self.setAcceptHoverEvents(True)
    
    def is_occupied(self):
        return self._is_occupied
    
    def occupy(self, device_id: str, device_type: str, device_color: QColor):
        self._is_occupied = True
        self._device_id = device_id
        self._device_type = device_type
        self._device_color = device_color
        self.update()
        # 强制父项也更新
        if self.parentItem():
            self.parentItem().update()
        print(f"U{self.u_number} 已被设备 {device_id} 占用")
    
    def release(self):
        device_id = self._device_id
        self._is_occupied = False
        self._device_id = None
        self._device_type = None
        self._device_color = None
        self.update()
        print(f"U{self.u_number} 已释放，原设备: {device_id}")
        return device_id
    
    def get_device_id(self):
        return self._device_id
    
    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)
        
        if self._is_occupied:
            pass
