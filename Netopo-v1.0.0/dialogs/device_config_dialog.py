from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QSpinBox, QComboBox, QPushButton,
                                QGroupBox, QGridLayout, QDialogButtonBox,
                                QCheckBox, QAbstractSpinBox, QWidget, QRadioButton,
                                QScrollArea)
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QFont, QColor, QLinearGradient
from graphics.port_item import PORT_TYPE_ETHERNET, PORT_TYPE_FIBER, PORT_TYPE_CONSOLE, PORT_TYPE_USB
from graphics.node_item import (DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_ISP, DEVICE_ISP_DUAL, DEVICE_MODEM, 
                                 DEVICE_AC, DEVICE_AP, DEVICE_HOME_ROUTER, DEVICE_PC, 
                                 DEVICE_PHONE, DEVICE_NAS, DEVICE_SERVER)

DEVICE_TYPE_NAMES = {
    DEVICE_ISP: "单逻辑接口 ISP",
    DEVICE_ISP_DUAL: "双逻辑接口 ISP",
    DEVICE_ROUTER: "路由器",
    DEVICE_MODEM: "光猫",
    DEVICE_SWITCH: "交换机",
    DEVICE_AC: "无线控制器",
    DEVICE_AP: "无线接入点",
    DEVICE_HOME_ROUTER: "家用路由器",
    DEVICE_PC: "个人计算机",
    DEVICE_PHONE: "手机",
    DEVICE_NAS: "网络存储",
    DEVICE_SERVER: "服务器"
}

DEVICE_PORT_LIMITS = {
    DEVICE_ISP: {"ethernet_max": 0, "fiber_max": 1, "console_max": 0, "usb_max": 0, "wifi": False, "ethernet_default": 0, "fiber_default": 1},
    DEVICE_ISP_DUAL: {"ethernet_max": 0, "fiber_max": 2, "console_max": 0, "usb_max": 0, "wifi": False, "ethernet_default": 0, "fiber_default": 2},
    DEVICE_ROUTER: {"ethernet_max": 48, "fiber_max": 8, "console_max": 2, "usb_max": 2, "wifi": False, "ethernet_default": 4, "fiber_default": 2},
    DEVICE_MODEM: {"ethernet_max": 4, "fiber_max": 4, "console_max": 0, "usb_max": 1, "wifi": False, "ethernet_default": 2, "fiber_default": 1},
    DEVICE_SWITCH: {"ethernet_max": 48, "fiber_max": 8, "console_max": 2, "usb_max": 2, "wifi": False, "ethernet_default": 8, "fiber_default": 2},
    DEVICE_AC: {"ethernet_max": 48, "fiber_max": 8, "console_max": 2, "usb_max": 2, "wifi": False, "ethernet_default": 4, "fiber_default": 2},
    DEVICE_AP: {"ethernet_max": 2, "fiber_max": 2, "console_max": 0, "usb_max": 0, "wifi": True, "ethernet_default": 1, "fiber_default": 0},
    DEVICE_HOME_ROUTER: {"ethernet_max": 4, "fiber_max": 2, "console_max": 0, "usb_max": 2, "wifi": True, "ethernet_default": 4, "fiber_default": 0},
    DEVICE_PC: {"ethernet_max": 2, "fiber_max": 2, "console_max": 0, "usb_max": 4, "wifi": True, "ethernet_default": 1, "fiber_default": 0},
    DEVICE_PHONE: {"ethernet_max": 0, "fiber_max": 0, "console_max": 0, "usb_max": 0, "wifi": True, "ethernet_default": 0, "fiber_default": 0},
    DEVICE_NAS: {"ethernet_max": 4, "fiber_max": 4, "console_max": 0, "usb_max": 2, "wifi": False, "ethernet_default": 2, "fiber_default": 0},
    DEVICE_SERVER: {"ethernet_max": 48, "fiber_max": 8, "console_max": 2, "usb_max": 2, "wifi": False, "ethernet_default": 4, "fiber_default": 2}
}

PORT_TYPE_OPTIONS = {
    "E0": "E 0/0/X",
    "GE0": "GE 0/0/X",
    "10GE0": "10GE 0/0/X",
    "E1": "E 1/0/X",
    "GE1": "GE 1/0/X",
    "10GE1": "10GE 1/0/X"
}

FIBER_TYPE_OPTIONS = {
    "10GE0": "10GE 0/0/X",
    "10GE1": "10GE 1/0/X"
}

PORT_TYPE_COLORS = {
    PORT_TYPE_ETHERNET: QColor(100, 180, 100),
    PORT_TYPE_FIBER: QColor(100, 150, 200),
    PORT_TYPE_CONSOLE: QColor(180, 150, 100),
    PORT_TYPE_USB: QColor(180, 130, 180)
}

PORT_TYPE_NAMES = {
    PORT_TYPE_ETHERNET: "电口",
    PORT_TYPE_FIBER: "光口",
    PORT_TYPE_CONSOLE: "Console",
    PORT_TYPE_USB: "USB"
}

class PortGraphicsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ports = []
        self.sort_style = "z_shape"
        self.layout_mode = "single"
        self.min_height = 100
        self.setFixedHeight(self.min_height)
    
    def set_ports(self, ports, sort_style="z_shape", layout_mode="single"):
        self.ports = ports
        self.sort_style = sort_style
        self.layout_mode = layout_mode
        self._update_size()
        self.update()
    
    def _update_size(self):
        if not self.ports:
            self.setFixedHeight(self.min_height)
            return
        
        port_width = 28
        port_height = 20
        h_gap = 4
        v_gap = 4
        group_gap = 20
        
        if self.layout_mode == "single":
            total_width = len(self.ports) * (port_width + h_gap) + 20
            total_height = port_height + 60
        else:
            type_counts = self._get_port_type_counts()
            total_width = 20
            max_rows = 1
            
            for port_type in [PORT_TYPE_ETHERNET, PORT_TYPE_FIBER, PORT_TYPE_CONSOLE, PORT_TYPE_USB]:
                count = type_counts.get(port_type, 0)
                if count > 0:
                    cols = (count + 1) // 2
                    rows = 2
                    total_width += cols * (port_width + h_gap) + group_gap
                    max_rows = max(max_rows, rows)
            
            total_height = max_rows * (port_height + v_gap) + 60
        
        self.setMinimumWidth(total_width)
        self.setFixedHeight(max(self.min_height, total_height))
    
    def _get_port_type_counts(self):
        counts = {
            PORT_TYPE_ETHERNET: 0,
            PORT_TYPE_FIBER: 0,
            PORT_TYPE_CONSOLE: 0,
            PORT_TYPE_USB: 0
        }
        for port in self.ports:
            port_type = port.get("type", PORT_TYPE_ETHERNET)
            if port_type in counts:
                counts[port_type] += 1
        return counts
    
    def _get_n_shape_order(self, count, rows=2):
        order = []
        cols = (count + rows - 1) // rows
        
        for col in range(cols):
            for row in range(rows - 1, -1, -1):
                idx = col * rows + (rows - 1 - row)
                if idx < count:
                    order.append((idx, col, row))
        
        return order
    
    def _get_mirror_n_shape_order(self, count, rows=2):
        order = []
        cols = (count + rows - 1) // rows
        
        for col in range(cols):
            for row in range(rows):
                idx = col * rows + row
                if idx < count:
                    order.append((idx, col, row))
        
        return order
    
    def _get_z_shape_order(self, count, rows=2):
        order = []
        top_count = (count + 1) // 2
        bottom_count = count - top_count
        
        for i in range(top_count):
            order.append((i, i, 0))
        
        for i in range(bottom_count):
            order.append((top_count + i, i, 1))
        
        return order
    
    def _get_linear_order(self, count, rows=1):
        order = []
        cols = count
        
        for i in range(count):
            order.append((i, i, 0))
        
        return order
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if not self.ports:
            painter.setPen(QPen(QColor(128, 128, 128)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "无端口配置")
            return
        
        type_counts = self._get_port_type_counts()
        legend_y = 10
        legend_x = 10
        legend_item_width = 70
        
        font = QFont("Arial", 8)
        painter.setFont(font)
        
        legend_items = []
        for port_type, count in type_counts.items():
            if count > 0:
                legend_items.append((port_type, count))
        
        for i, (port_type, count) in enumerate(legend_items):
            x = legend_x + i * legend_item_width
            color = PORT_TYPE_COLORS.get(port_type, QColor(128, 128, 128))
            name = PORT_TYPE_NAMES.get(port_type, "未知")
            
            painter.setPen(QPen(QColor(60, 60, 60), 1))
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(int(x), int(legend_y), 12, 12, 2, 2)
            
            painter.setPen(QPen(QColor(40, 40, 40)))
            painter.drawText(int(x + 16), int(legend_y + 10), f"{name}")
        
        ports_by_type = {}
        for idx, port in enumerate(self.ports):
            port_type = port.get("type", PORT_TYPE_ETHERNET)
            if port_type not in ports_by_type:
                ports_by_type[port_type] = []
            ports_by_type[port_type].append((idx, port))
        
        port_width = 28
        port_height = 20
        h_gap = 4
        v_gap = 4
        group_gap = 20
        
        start_y = 35
        current_x = 10
        
        if self.layout_mode == "single":
            type_counters = {
                PORT_TYPE_ETHERNET: 0,
                PORT_TYPE_FIBER: 0,
                PORT_TYPE_CONSOLE: 0,
                PORT_TYPE_USB: 0
            }
            
            for idx, port in enumerate(self.ports):
                port_type = port.get("type", PORT_TYPE_ETHERNET)
                color = PORT_TYPE_COLORS.get(port_type, QColor(128, 128, 128))
                
                type_counters[port_type] += 1
                port_num = type_counters[port_type]
                
                x = current_x
                y = start_y
                
                gradient = QLinearGradient(x, y, x, y + port_height)
                gradient.setColorAt(0, color.lighter(120))
                gradient.setColorAt(1, color)
                
                painter.setPen(QPen(QColor(60, 60, 60), 1))
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(int(x), int(y), port_width, port_height, 3, 3)
                
                num_font = QFont("Arial", 9, QFont.Weight.Bold)
                painter.setFont(num_font)
                painter.setPen(QPen(QColor(255, 255, 255)))
                
                painter.drawText(QRectF(x, y, port_width, port_height), 
                               Qt.AlignmentFlag.AlignCenter, str(port_num))
                
                current_x += port_width + h_gap
        else:
            for port_type in [PORT_TYPE_ETHERNET, PORT_TYPE_FIBER, PORT_TYPE_CONSOLE, PORT_TYPE_USB]:
                if port_type not in ports_by_type:
                    continue
                
                ports_list = ports_by_type[port_type]
                count = len(ports_list)
                color = PORT_TYPE_COLORS.get(port_type, QColor(128, 128, 128))
                
                rows = 2
                if self.sort_style == "z_shape":
                    order = self._get_z_shape_order(count, 2)
                elif self.sort_style == "n_shape":
                    order = self._get_n_shape_order(count, 2)
                elif self.sort_style == "mirror_n":
                    order = self._get_mirror_n_shape_order(count, 2)
                else:
                    order = self._get_z_shape_order(count, 2)
                
                top_count = (count + 1) // 2
                cols = top_count
                
                for local_idx, col, row in order:
                    original_idx, port = ports_list[local_idx]
                    x = current_x + col * (port_width + h_gap)
                    y = start_y + row * (port_height + v_gap)
                    
                    gradient = QLinearGradient(x, y, x, y + port_height)
                    gradient.setColorAt(0, color.lighter(120))
                    gradient.setColorAt(1, color)
                    
                    painter.setPen(QPen(QColor(60, 60, 60), 1))
                    painter.setBrush(QBrush(gradient))
                    painter.drawRoundedRect(int(x), int(y), port_width, port_height, 3, 3)
                    
                    num_font = QFont("Arial", 9, QFont.Weight.Bold)
                    painter.setFont(num_font)
                    painter.setPen(QPen(QColor(255, 255, 255)))
                    
                    painter.drawText(QRectF(x, y, port_width, port_height), 
                                   Qt.AlignmentFlag.AlignCenter, str(local_idx + 1))
                
                current_x += cols * (port_width + h_gap) + group_gap


class DeviceConfigDialog(QDialog):
    def __init__(self, parent=None, device_data=None):
        super().__init__(parent)
        self.setWindowTitle("自定义设备添加")
        self.setMinimumWidth(450)
        self.setMinimumHeight(400)
        self.device_data = device_data or {}
        self._original_id = None
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        info_group = QGroupBox("基本信息")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("设备类型:"), 0, 0)
        self.type_combo = QComboBox()
        for device_type, name in DEVICE_TYPE_NAMES.items():
            self.type_combo.addItem(name, device_type)
        self.type_combo.currentIndexChanged.connect(self._on_device_type_changed)
        info_layout.addWidget(self.type_combo, 0, 1)
        
        info_layout.addWidget(QLabel("设备数量:"), 1, 0)
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 10)
        self.count_spin.setValue(1)
        self.count_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.count_spin.valueChanged.connect(self._on_device_count_changed)
        info_layout.addWidget(self.count_spin, 1, 1)
        
        self.u_size_label = QLabel("设备U数:")
        info_layout.addWidget(self.u_size_label, 2, 0)
        self.u_size_combo = QComboBox()
        for i in range(1, 9):
            self.u_size_combo.addItem(f"{i}U", i)
        self.u_size_combo.currentIndexChanged.connect(self._on_u_size_changed)
        info_layout.addWidget(self.u_size_combo, 2, 1)
        
        main_layout.addWidget(info_group)
        
        self.ports_group = QGroupBox("接口配置")
        self.ports_layout = QVBoxLayout(self.ports_group)
        
        self.ethernet_widget = QWidget()
        ethernet_layout = QHBoxLayout(self.ethernet_widget)
        ethernet_layout.setContentsMargins(0, 0, 0, 0)
        self.ethernet_label = QLabel("电口数量:")
        ethernet_layout.addWidget(self.ethernet_label)
        self.ethernet_spin = QSpinBox()
        self.ethernet_spin.setRange(0, 48)
        self.ethernet_spin.setValue(4)
        self.ethernet_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.ethernet_spin.valueChanged.connect(self._update_port_list)
        ethernet_layout.addWidget(self.ethernet_spin)
        
        ethernet_layout.addWidget(QLabel("接口类型:"))
        self.ethernet_type_combo = QComboBox()
        for type_key, type_name in PORT_TYPE_OPTIONS.items():
            self.ethernet_type_combo.addItem(type_name, type_key)
        self.ethernet_type_combo.setCurrentIndex(1)
        self.ethernet_type_combo.currentIndexChanged.connect(self._update_port_list)
        ethernet_layout.addWidget(self.ethernet_type_combo)
        
        ethernet_layout.addStretch()
        self.ports_layout.addWidget(self.ethernet_widget)
        
        self.fiber_widget = QWidget()
        fiber_layout = QHBoxLayout(self.fiber_widget)
        fiber_layout.setContentsMargins(0, 0, 0, 0)
        self.fiber_label = QLabel("光口数量:")
        fiber_layout.addWidget(self.fiber_label)
        self.fiber_spin = QSpinBox()
        self.fiber_spin.setRange(0, 8)
        self.fiber_spin.setValue(2)
        self.fiber_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.fiber_spin.valueChanged.connect(self._update_port_list)
        fiber_layout.addWidget(self.fiber_spin)
        
        fiber_layout.addWidget(QLabel("接口类型:"))
        self.fiber_type_combo = QComboBox()
        for type_key, type_name in FIBER_TYPE_OPTIONS.items():
            self.fiber_type_combo.addItem(type_name, type_key)
        self.fiber_type_combo.setCurrentIndex(0)
        self.fiber_type_combo.currentIndexChanged.connect(self._update_port_list)
        fiber_layout.addWidget(self.fiber_type_combo)
        
        fiber_layout.addStretch()
        self.ports_layout.addWidget(self.fiber_widget)
        
        self.console_widget = QWidget()
        console_layout = QHBoxLayout(self.console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)
        self.console_label = QLabel("Console口数量:")
        console_layout.addWidget(self.console_label)
        self.console_spin = QSpinBox()
        self.console_spin.setRange(0, 2)
        self.console_spin.setValue(1)
        self.console_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.console_spin.valueChanged.connect(self._update_port_list)
        console_layout.addWidget(self.console_spin)
        console_layout.addStretch()
        self.ports_layout.addWidget(self.console_widget)
        
        self.usb_widget = QWidget()
        usb_layout = QHBoxLayout(self.usb_widget)
        usb_layout.setContentsMargins(0, 0, 0, 0)
        self.usb_label = QLabel("USB口数量:")
        usb_layout.addWidget(self.usb_label)
        self.usb_spin = QSpinBox()
        self.usb_spin.setRange(0, 8)
        self.usb_spin.setValue(2)
        self.usb_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.usb_spin.valueChanged.connect(self._update_port_list)
        usb_layout.addWidget(self.usb_spin)
        usb_layout.addStretch()
        self.ports_layout.addWidget(self.usb_widget)
        
        self.wifi_widget = QWidget()
        wifi_layout = QHBoxLayout(self.wifi_widget)
        wifi_layout.setContentsMargins(0, 0, 0, 0)
        self.wifi_checkbox = QCheckBox("WiFi接入")
        wifi_layout.addWidget(self.wifi_checkbox)
        wifi_layout.addStretch()
        self.ports_layout.addWidget(self.wifi_widget)
        
        main_layout.addWidget(self.ports_group)
        
        self.layout_options_group = QGroupBox("接口选项")
        layout_options = QVBoxLayout(self.layout_options_group)
        
        self.layout_mode_widget = QWidget()
        layout_mode_layout = QHBoxLayout(self.layout_mode_widget)
        layout_mode_layout.setContentsMargins(0, 0, 0, 0)
        
        self.layout_single_radio = QRadioButton("一行排列")
        layout_mode_layout.addWidget(self.layout_single_radio)
        
        self.layout_double_radio = QRadioButton("两行排列")
        layout_mode_layout.addWidget(self.layout_double_radio)
        
        self.sort_style_widget = QWidget()
        sort_style_layout = QHBoxLayout(self.sort_style_widget)
        sort_style_layout.setContentsMargins(0, 0, 0, 0)
        
        self.sort_style_label = QLabel("排序方式:")
        sort_style_layout.addWidget(self.sort_style_label)
        
        self.sort_style_combo = QComboBox()
        self.sort_style_combo.addItem("Z字形", "z_shape")
        self.sort_style_combo.addItem("N字形", "n_shape")
        self.sort_style_combo.addItem("镜像N字形", "mirror_n")
        sort_style_layout.addWidget(self.sort_style_combo)
        
        layout_mode_layout.addStretch()
        layout_options.addWidget(self.layout_mode_widget)
        layout_options.addWidget(self.sort_style_widget)
        
        layout_options.addStretch()
        main_layout.addWidget(self.layout_options_group)
        
        self.port_list_label = QLabel("端口列表:")
        main_layout.addWidget(self.port_list_label)
        
        self.port_graphics_widget = PortGraphicsWidget()
        self.port_graphics_widget.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ccc; border-radius: 4px;")
        main_layout.addWidget(self.port_graphics_widget)
        
        self.total_label = QLabel()
        main_layout.addWidget(self.total_label)
        
        main_layout.addStretch()
        
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
        
        self._on_device_type_changed(0)
        
        self.layout_single_radio.toggled.connect(self._on_layout_mode_changed)
        self.layout_double_radio.toggled.connect(self._on_layout_mode_changed)
        self.sort_style_combo.currentIndexChanged.connect(self._on_sort_style_changed)
    
    def _get_device_prefix(self, device_type):
        prefix_map = {
            DEVICE_ISP: "ISP",
            DEVICE_ISP_DUAL: "ISP-Dual",
            DEVICE_ROUTER: "R",
            DEVICE_MODEM: "Modem",
            DEVICE_SWITCH: "SW",
            DEVICE_AC: "AC",
            DEVICE_AP: "AP",
            DEVICE_HOME_ROUTER: "HomeRouter",
            DEVICE_PC: "PC",
            DEVICE_PHONE: "Phone",
            DEVICE_NAS: "NAS",
            DEVICE_SERVER: "Server"
        }
        return prefix_map.get(device_type, "DEV")
    
    def _update_device_name(self):
        pass
    
    def _on_device_count_changed(self):
        self._update_device_name()
        self._update_port_list()
    
    def _on_u_size_changed(self):
        pass
    
    def _on_device_type_changed(self, index):
        device_type = self.type_combo.currentData()
        limits = DEVICE_PORT_LIMITS.get(device_type, DEVICE_PORT_LIMITS[DEVICE_SWITCH])
        
        self.ethernet_spin.setRange(0, limits["ethernet_max"])
        self.ethernet_spin.setValue(limits["ethernet_default"])
        self.ethernet_label.setText(f"电口数量 (0-{limits['ethernet_max']}):")
        
        self.fiber_spin.setRange(0, limits["fiber_max"])
        self.fiber_spin.setValue(limits["fiber_default"])
        self.fiber_label.setText(f"光口数量 (0-{limits['fiber_max']}):")
        
        self.console_spin.setRange(0, limits["console_max"])
        self.console_spin.setValue(0 if limits["console_max"] == 0 else 1)
        self.console_label.setText(f"Console口数量 (0-{limits['console_max']}):")
        
        self.usb_spin.setRange(0, limits["usb_max"])
        self.usb_spin.setValue(0)
        self.usb_label.setText(f"USB口数量 (0-{limits['usb_max']}):")
        
        self.wifi_checkbox.setChecked(limits["wifi"])
        self.wifi_checkbox.setEnabled(limits["wifi"])
        
        if limits["ethernet_max"] == 0:
            self.ethernet_widget.setVisible(False)
        else:
            self.ethernet_widget.setVisible(True)
            self.ethernet_spin.setEnabled(True)
            self.ethernet_type_combo.setEnabled(True)
        
        if limits["fiber_max"] == 0:
            self.fiber_widget.setVisible(False)
        else:
            self.fiber_widget.setVisible(True)
            self.fiber_spin.setEnabled(True)
            self.fiber_type_combo.setEnabled(True)
        
        if limits["console_max"] == 0:
            self.console_widget.setVisible(False)
        else:
            self.console_widget.setVisible(True)
            self.console_spin.setEnabled(True)
        
        if limits["usb_max"] == 0:
            self.usb_widget.setVisible(False)
        else:
            self.usb_widget.setVisible(True)
            self.usb_spin.setEnabled(True)
        
        if not limits["wifi"]:
            self.wifi_widget.setVisible(False)
        else:
            self.wifi_widget.setVisible(True)
        
        home_devices = [DEVICE_HOME_ROUTER, DEVICE_MODEM, DEVICE_NAS, DEVICE_PC, DEVICE_PHONE, DEVICE_AP]
        is_home_device = device_type in home_devices
        
        hidden_layout_options_devices = [
            DEVICE_ISP, DEVICE_ISP_DUAL, DEVICE_MODEM, 
            DEVICE_HOME_ROUTER, DEVICE_PC, DEVICE_PHONE
        ]
        should_hide_layout_options = device_type in hidden_layout_options_devices
        
        self.layout_options_group.setVisible(not should_hide_layout_options)
        
        u_size_devices = [DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_SERVER]
        show_u_size = device_type in u_size_devices
        self.u_size_label.setVisible(show_u_size)
        self.u_size_combo.setVisible(show_u_size)
        
        if is_home_device:
            self.layout_mode_widget.setVisible(False)
            self.sort_style_widget.setVisible(False)
            self.layout_single_radio.setChecked(True)
        else:
            self.layout_mode_widget.setVisible(True)
            self._update_sort_style_visibility()
        
        self._update_device_name()
        self._update_port_list()
    
    def _on_layout_mode_changed(self):
        self._update_sort_style_visibility()
        self._update_port_list()
    
    def _on_sort_style_changed(self):
        self._update_port_list()
    
    def _update_sort_style_visibility(self):
        if self.layout_double_radio.isChecked():
            self.sort_style_widget.setVisible(True)
        else:
            self.sort_style_widget.setVisible(False)
    
    def _update_port_list(self):
        ports = self._generate_ports()
        
        layout_mode = "double" if self.layout_double_radio.isChecked() else "single"
        sort_style = self.sort_style_combo.currentData()
        
        self.port_graphics_widget.set_ports(ports, sort_style, layout_mode)
        
        if not ports:
            self.total_label.setText("端口总数: 0")
        else:
            total = len(ports) + (1 if self.wifi_checkbox.isChecked() and self.wifi_checkbox.isEnabled() else 0)
            self.total_label.setText(f"端口总数: {total}")
    
    def _generate_ports(self):
        ports = []
        ethernet_type = self.ethernet_type_combo.currentData()
        fiber_type = self.fiber_type_combo.currentData()
        
        ethernet_count = self.ethernet_spin.value()
        for i in range(ethernet_count):
            port_id = self._make_port_id(ethernet_type, i + 1)
            ports.append({
                "id": port_id,
                "type": PORT_TYPE_ETHERNET
            })
        
        fiber_count = self.fiber_spin.value()
        for i in range(fiber_count):
            port_id = self._make_port_id(fiber_type, i + 1)
            ports.append({
                "id": port_id,
                "type": PORT_TYPE_FIBER
            })
        
        console_count = self.console_spin.value()
        for i in range(console_count):
            ports.append({
                "id": f"CON{i+1}",
                "type": PORT_TYPE_CONSOLE
            })
        
        usb_count = self.usb_spin.value()
        for i in range(usb_count):
            ports.append({
                "id": f"USB{i+1}",
                "type": PORT_TYPE_USB
            })
        
        return ports
    
    def _make_port_id(self, type_key, port_num):
        if type_key.startswith("10GE"):
            slot = type_key[4]
            return f"10GE{slot}/0/{port_num}"
        elif type_key.startswith("GE"):
            slot = type_key[2]
            return f"GE{slot}/0/{port_num}"
        elif type_key.startswith("E"):
            slot = type_key[1]
            return f"E{slot}/0/{port_num}"
        return f"{type_key}/0/{port_num}"

    def _load_data(self):
        if "id" in self.device_data:
            self._original_id = self.device_data["id"]
        
        if "device_type" in self.device_data:
            device_type = self.device_data["device_type"]
            index = self.type_combo.findData(device_type)
            if index >= 0:
                self.type_combo.blockSignals(True)
                self.type_combo.setCurrentIndex(index)
                self.type_combo.blockSignals(False)
                self._on_device_type_changed(index)
        
        if self._original_id:
            self.type_combo.setEnabled(False)
        
        if "port_config" in self.device_data:
            port_config = self.device_data.get("port_config", {})
            all_ports = port_config.get("ports", [])
            
            ethernet_count = 0
            fiber_count = 0
            console_count = 0
            usb_count = 0
            
            for port in all_ports:
                port_type = port.get("type", PORT_TYPE_ETHERNET)
                if port_type == PORT_TYPE_ETHERNET:
                    ethernet_count += 1
                elif port_type == PORT_TYPE_FIBER:
                    fiber_count += 1
                elif port_type == PORT_TYPE_CONSOLE:
                    console_count += 1
                elif port_type == PORT_TYPE_USB:
                    usb_count += 1
            
            device_type = self.type_combo.currentData()
            limits = DEVICE_PORT_LIMITS.get(device_type, DEVICE_PORT_LIMITS[DEVICE_SWITCH])
            
            self.ethernet_spin.setValue(min(ethernet_count, limits["ethernet_max"]))
            self.fiber_spin.setValue(min(fiber_count, limits["fiber_max"]))
            self.console_spin.setValue(min(console_count, limits["console_max"]))
            self.usb_spin.setValue(min(usb_count, limits["usb_max"]))
            
            if port_config.get("wifi", False) and limits["wifi"]:
                self.wifi_checkbox.setChecked(True)
            
            layout_mode = port_config.get("layout_mode", "single")
            sort_style = port_config.get("sort_style", "z_shape")
            
            if layout_mode == "double":
                self.layout_double_radio.setChecked(True)
            else:
                self.layout_single_radio.setChecked(True)
            
            sort_index = self.sort_style_combo.findData(sort_style)
            if sort_index >= 0:
                self.sort_style_combo.setCurrentIndex(sort_index)
            
            self._update_port_list()
        
        if "u_size" in self.device_data:
            u_size = self.device_data["u_size"]
            u_index = self.u_size_combo.findData(u_size)
            if u_index >= 0:
                self.u_size_combo.setCurrentIndex(u_index)
    
    def _validate_and_accept(self):
        device_type = self.type_combo.currentData()
        limits = DEVICE_PORT_LIMITS.get(device_type, DEVICE_PORT_LIMITS[DEVICE_SWITCH])
        
        total_ports = (self.ethernet_spin.value() + self.fiber_spin.value() + 
                       self.console_spin.value() + self.usb_spin.value())
        
        has_wifi = self.wifi_checkbox.isChecked() and self.wifi_checkbox.isEnabled()
        
        if total_ports == 0 and not has_wifi:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "验证错误", "至少需要配置一个端口或启用WiFi接入")
            return
        
        self.accept()

    def get_config(self):
        device_type = self.type_combo.currentData()
        
        ports = self._generate_ports()
        
        layout_mode = "double" if self.layout_double_radio.isChecked() else "single"
        sort_style = self.sort_style_combo.currentData()
        
        if self._original_id:
            device_id = self._original_id
        else:
            device_type = self.type_combo.currentData()
            count = self.count_spin.value()
            prefix = self._get_device_prefix(device_type)
            if count == 1:
                device_id = f"{prefix}1"
            else:
                device_id = f"{prefix}(1-{count})"
        
        config = {
            "id": device_id,
            "device_type": device_type,
            "device_count": self.count_spin.value(),
            "u_size": self.u_size_combo.currentData(),
            "port_config": {
                "ports": ports,
                "ethernet_type": self.ethernet_type_combo.currentData(),
                "fiber_type": self.fiber_type_combo.currentData(),
                "layout_mode": layout_mode,
                "sort_style": sort_style
            }
        }
        
        if self.wifi_checkbox.isChecked() and self.wifi_checkbox.isEnabled():
            config["port_config"]["wifi"] = True
        
        return config
