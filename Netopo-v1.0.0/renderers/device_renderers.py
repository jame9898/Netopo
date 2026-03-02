from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPainterPath

RACK_WIDTH_MM = 482.6
RACK_U_HEIGHT_MM = 44.45
SCALE_PX_PER_MM = 1.0

PANEL_WIDTH_PX = int(RACK_WIDTH_MM * SCALE_PX_PER_MM)
U_HEIGHT_PX = int(RACK_U_HEIGHT_MM * SCALE_PX_PER_MM)

RJ45_WIDTH_MM = 16
RJ45_HEIGHT_MM = 21
RJ45_WIDTH_PX = int(RJ45_WIDTH_MM * SCALE_PX_PER_MM)
RJ45_HEIGHT_PX = int(RJ45_HEIGHT_MM * SCALE_PX_PER_MM * 0.4)


class DevicePanelRenderer:
    
    @staticmethod
    def draw_rj45_port(painter, x, y, width=16, height=12):
        painter.setPen(QPen(QColor(30, 30, 30), 0.8))
        painter.setBrush(QBrush(QColor(160, 160, 160)))
        painter.drawRect(int(x), int(y), int(width), int(height))
        
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        gap_width = width * 0.6
        gap_height = height * 0.3
        gap_x = x + (width - gap_width) / 2
        gap_y = y + height * 0.15
        painter.drawRect(int(gap_x), int(gap_y), int(gap_width), int(gap_height))
        
        painter.setPen(QPen(QColor(220, 180, 0), 0.6))
        pin_width = width * 0.06
        pin_height = height * 0.3
        for i in range(8):
            pin_x = x + width * 0.15 + i * width * 0.095
            pin_y = y + height * 0.55
            painter.drawRect(int(pin_x), int(pin_y), int(pin_width), int(pin_height))
    
    @staticmethod
    def draw_sfp_port(painter, x, y, width=12, height=16):
        painter.setPen(QPen(QColor(30, 30, 30), 0.8))
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRoundedRect(int(x), int(y), int(width), int(height), 1, 1)
        
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawRect(int(x + 2), int(y + 2), int(width - 4), int(height - 4))
        
        painter.setPen(QPen(QColor(15, 15, 15), 0.5))
        painter.drawLine(int(x + 3), int(y + height * 0.7), int(x + width - 3), int(y + height * 0.7))
    
    @staticmethod
    def draw_console_port(painter, x, y, width=14, height=12):
        painter.setPen(QPen(QColor(30, 30, 30), 0.8))
        painter.setBrush(QBrush(QColor(40, 90, 150)))
        painter.drawRoundedRect(int(x), int(y), int(width), int(height), 1, 1)
        
        painter.setPen(QPen(QColor(20, 20, 20), 0.5))
        for i in range(4):
            pin_x = x + 2 + i * 2.5
            painter.drawLine(int(pin_x), int(y + 2), int(pin_x), int(y + height - 2))


class HuaweiS5735Renderer(DevicePanelRenderer):
    MODEL = "Huawei S5735-L24T4X-A1"
    VENDOR = "huawei"
    PANEL_WIDTH = 442
    PANEL_HEIGHT = 43.6
    
    @classmethod
    def draw_panel(cls, painter, rect, device_name=""):
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        
        painter.setPen(QPen(QColor(50, 50, 50), 1.5))
        painter.setBrush(QBrush(QColor(25, 25, 25)))
        painter.drawRoundedRect(int(x), int(y), int(w), int(h), 2, 2)
        
        painter.setPen(QPen(QColor(40, 40, 40), 0.5))
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        inner_margin = 2
        painter.drawRect(int(x + inner_margin), int(y + inner_margin), 
                        int(w - 2 * inner_margin), int(h - 2 * inner_margin))
        
        rj45_width = 16
        rj45_height = 12
        rj45_gap_x = 3
        rj45_gap_y = 2
        group_gap = 10
        
        start_x = x + 8
        start_y = y + 5
        
        for col in range(12):
            col_x = start_x + col * (rj45_width + rj45_gap_x)
            if col > 0 and col % 4 == 0:
                col_x += group_gap - rj45_gap_x
            
            cls.draw_rj45_port(painter, col_x, start_y, rj45_width, rj45_height)
            cls.draw_rj45_port(painter, col_x, start_y + rj45_height + rj45_gap_y, rj45_width, rj45_height)
        
        rj45_total_width = 12 * rj45_width + 11 * rj45_gap_x + 2 * group_gap
        sfp_start_x = start_x + rj45_total_width + 10
        sfp_width = 11
        sfp_height = 14
        sfp_gap = 2
        
        for i in range(4):
            port_x = sfp_start_x + i * (sfp_width + sfp_gap)
            cls.draw_sfp_port(painter, port_x, start_y + 2, sfp_width, sfp_height)
        
        console_x = sfp_start_x + 4 * (sfp_width + sfp_gap) + 6
        cls.draw_console_port(painter, console_x, start_y + 4, 10, 8)
        
        cls._draw_leds(painter, x + w - 45, y + 3)
        
        cls._draw_label(painter, x + 4, y + h - 5, device_name)
    
    @classmethod
    def _draw_leds(cls, painter, x, y):
        leds = [
            (QColor(0, 160, 0), "PWR"),
            (QColor(0, 160, 0), "SYS"),
            (QColor(190, 160, 0), "ALM"),
        ]
        
        for i, (color, label) in enumerate(leds):
            led_x = x + i * 12
            led_y = y
            
            painter.setPen(QPen(QColor(40, 40, 40), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawEllipse(int(led_x), int(led_y), 4, 4)
            
            painter.setPen(QPen(QColor(120, 120, 120), 0.5))
            font = QFont()
            font.setPointSize(3)
            font.setFamily("Arial")
            painter.setFont(font)
            painter.drawText(int(led_x - 2), int(led_y + 8), label)
    
    @classmethod
    def _draw_label(cls, painter, x, y, device_name):
        painter.setPen(QPen(QColor(140, 140, 140), 0.5))
        font = QFont("Arial", 4)
        painter.setFont(font)
        
        if not device_name:
            device_name = "S5735-L24T4X-A1"
        painter.drawText(int(x), int(y), device_name)
    
    @classmethod
    def get_port_positions(cls, rect):
        x, y = rect.x(), rect.y()
        ports = []
        
        rj45_width = 16
        rj45_height = 12
        rj45_gap_x = 3
        rj45_gap_y = 2
        group_gap = 10
        
        start_x = x + 8
        start_y = y + 5
        
        port_index = 1
        for col in range(12):
            col_x = start_x + col * (rj45_width + rj45_gap_x)
            if col > 0 and col % 4 == 0:
                col_x += group_gap - rj45_gap_x
            
            ports.append({
                "id": f"GE0/0/{port_index}",
                "type": "ethernet",
                "pos": (col_x + rj45_width / 2, start_y + rj45_height / 2)
            })
            port_index += 1
            
            ports.append({
                "id": f"GE0/0/{port_index}",
                "type": "ethernet", 
                "pos": (col_x + rj45_width / 2, start_y + rj45_height + rj45_gap_y + rj45_height / 2)
            })
            port_index += 1
        
        rj45_total_width = 12 * rj45_width + 11 * rj45_gap_x + 2 * group_gap
        sfp_start_x = start_x + rj45_total_width + 10
        sfp_width = 11
        sfp_height = 14
        sfp_gap = 2
        
        for i in range(4):
            port_x = sfp_start_x + i * (sfp_width + sfp_gap)
            ports.append({
                "id": f"XG0/0/{i + 1}",
                "type": "fiber",
                "pos": (port_x + sfp_width / 2, start_y + 2 + sfp_height / 2)
            })
        
        return ports
