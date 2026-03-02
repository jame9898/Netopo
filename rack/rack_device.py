from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QFont, QPainter, QColor

RACK_WIDTH_MM = 600
RACK_HEIGHT_MM = 2200
RACK_DEPTH_MM = 1200
RACK_TOTAL_U = 47
U_HEIGHT_MM = 44.45

RACK_WIDTH_PX = 200
U_HEIGHT_PX = 16

U_HEIGHT_OPTIONS = [1, 2, 4, 6, 8]


class RackDevice(QGraphicsItem):
    def __init__(self, device_id: str, device_type: str, u_height: int, 
                 start_u: int, parent=None):
        super().__init__(parent)
        self.device_id = device_id
        self.device_type = device_type
        self.u_height = u_height
        self.start_u = start_u
        self._width = RACK_WIDTH_PX - 20
        self._height = u_height * U_HEIGHT_PX
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self._ports = []
        self._create_ports()
        
        # 确保设备可见
        self.setVisible(True)
        print(f"创建机架设备: {device_id}, 类型: {device_type}, U位: {start_u}, 尺寸: {self._width}x{self._height}")

    def _create_ports(self):
        pass

    def boundingRect(self):
        return QRectF(0, 0, self._width, self._height)

    def paint(self, painter: QPainter, option, widget=None):
        print(f"绘制机架设备: {self.device_id}, 位置: {self.pos()}, 尺寸: {self._width}x{self._height}, U位: {self.start_u}")
        if self.device_type == "switch":
            color = QColor(100, 150, 200)
        elif self.device_type == "router":
            color = QColor(150, 180, 220)
        elif self.device_type == "server":
            color = QColor(200, 180, 160)
        elif self.device_type == "ac":
            color = QColor(180, 200, 150)
        elif self.device_type == "ap":
            color = QColor(200, 150, 180)
        else:
            color = QColor(120, 120, 120)
        
        # 更显眼的边框
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 50, 50), 3))
        else:
            painter.setPen(QPen(QColor(40, 40, 40), 2))
        painter.setBrush(QBrush(color))
        painter.drawRoundedRect(1, 1, int(self._width) - 2, int(self._height) - 2, 3, 3)
        
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.black))
        
        type_names = {"switch": "SW", "router": "R", "server": "SRV", "ac": "AC", "ap": "AP"}
        type_text = type_names.get(self.device_type, "DEV")
        display_text = f"{type_text}:{self.device_id}"
        painter.drawText(QRectF(5, 2, self._width - 10, self._height - 4),
                        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                        display_text)
        
        # 绘制U位信息
        font.setPointSize(6)
        painter.setFont(font)
        u_text = f"U{self.start_u}"
        if self.u_height > 1:
            u_text += f"-U{self.start_u + self.u_height - 1}"
        painter.drawText(QRectF(5, self._height - 12, self._width - 10, 10),
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom,
                        u_text)
        
        # 绘制端口（仅当设备高度足够时）
        if self._height >= 12:
            port_y = self._height / 2
            port_size = 4
            num_ports = min(8, max(2, self.u_height * 2))
            port_spacing = (self._width - 16) / (num_ports + 1)
            
            for i in range(num_ports):
                port_x = 8 + port_spacing * (i + 1)
                painter.setBrush(QBrush(QColor(0, 200, 0)))
                painter.setPen(QPen(QColor(20, 20, 20), 1))
                painter.drawRect(int(port_x - port_size/2), int(port_y - port_size/2),
                               port_size, port_size)

    def itemChange(self, change, value):
        return super().itemChange(change, value)

    def get_data(self):
        return {
            "id": self.device_id,
            "device_type": self.device_type,
            "u_height": self.u_height,
            "start_u": self.start_u
        }
