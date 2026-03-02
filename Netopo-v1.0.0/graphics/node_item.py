from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QFont, QPainter, QColor
from .port_item import PortItem, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER, PORT_TYPE_CONSOLE
from templates import VENDOR_COLORS, DEVICE_TYPE_NAMES
from renderers import HuaweiS5735Renderer, PANEL_WIDTH_PX, U_HEIGHT_PX

DEVICE_SWITCH = "switch"
DEVICE_ROUTER = "router"
DEVICE_FIREWALL = "firewall"
DEVICE_SERVER = "server"
DEVICE_PC = "pc"
DEVICE_PHONE = "phone"
DEVICE_HOME_ROUTER = "home_router"
DEVICE_MODEM = "modem"
DEVICE_NAS = "nas"
DEVICE_AC = "ac"
DEVICE_AP = "ap"
DEVICE_ISP = "isp"
DEVICE_ISP_DUAL = "isp_dual"
DEVICE_SERVER = "server"

DEVICE_COLORS = {
    DEVICE_SWITCH: QColor(200, 200, 200),
    DEVICE_ROUTER: QColor(150, 180, 220),
    DEVICE_FIREWALL: QColor(255, 180, 150),
    DEVICE_SERVER: QColor(200, 180, 160),
    DEVICE_PC: QColor(100, 150, 200),
    DEVICE_PHONE: QColor(150, 150, 150),
    DEVICE_HOME_ROUTER: QColor(180, 180, 220),
    DEVICE_MODEM: QColor(220, 180, 180),
    DEVICE_NAS: QColor(180, 200, 180),
    DEVICE_AC: QColor(200, 180, 220),
    DEVICE_AP: QColor(180, 220, 200),
    DEVICE_ISP: QColor(255, 100, 100),
    DEVICE_ISP_DUAL: QColor(255, 100, 100),
}

DEVICE_TYPE_NAMES = {
    DEVICE_SWITCH: "交换机",
    DEVICE_ROUTER: "路由器",
    DEVICE_FIREWALL: "防火墙",
    DEVICE_SERVER: "服务器",
    DEVICE_PC: "PC",
    DEVICE_PHONE: "手机",
    DEVICE_HOME_ROUTER: "家用路由器",
    DEVICE_MODEM: "光猫",
    DEVICE_NAS: "NAS",
    DEVICE_AC: "AC",
    DEVICE_AP: "AP",
    DEVICE_ISP: "ISP",
    DEVICE_ISP_DUAL: "ISP(双接口)",
    DEVICE_SERVER: "服务器",
}

RJ45_WIDTH = 16
RJ45_HEIGHT = 12
SFP_WIDTH = 11
SFP_HEIGHT = 14
PORT_GAP_X = 3
PORT_GAP_Y = 2
GROUP_GAP = 10

RENDERER_MAP = {
    "huawei_s5735_l24t4x": HuaweiS5735Renderer,
}


class NodeItem(QGraphicsItem):
    def __init__(self, node_id: str, device_type: str = DEVICE_SWITCH, 
                 port_config: dict = None, x: float = 0, y: float = 0,
                 template_id: str = None, vendor: str = None,
                 renderer_key: str = None, label_config: dict = None,
                 u_size: int = 1):
        super().__init__()
        self.setZValue(0)
        self.node_id = node_id
        self.device_type = device_type
        self.template_id = template_id
        self.vendor = vendor
        self.renderer_key = renderer_key
        self.u_size = u_size
        self.ports = []
        self._port_map = {}
        self._is_fixed = False
        self._is_racked = False
        self._rack_name = None
        self._rack_start_u = None
        if port_config is None:
            port_config = {
                "ports": [
                    {"id": f"P{i+1}", "type": PORT_TYPE_ETHERNET} for i in range(8)
                ]
            }
        self.port_config = port_config
        self.label_config = label_config or {
            "text_color": "#323232",
            "font_size": 10,
            "font_family": "Arial",
            "position": "bottom_right",
            "custom_x": 0,
            "custom_y": 0
        }
        self._width = self._calculate_width()
        self._height = self._calculate_height()
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self._create_ports()
    
    def is_fixed(self):
        return self._is_fixed
    
    def set_fixed(self, fixed):
        self._is_fixed = fixed
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not fixed)
        self.update()
    
    def is_racked(self):
        return self._is_racked
    
    def set_racked(self, racked: bool, rack_name: str = None, start_u: int = None):
        self._is_racked = racked
        self._rack_name = rack_name if racked else None
        self._rack_start_u = start_u if racked else None
    
    def get_rack_info(self):
        if self._is_racked:
            return {"rack_name": self._rack_name, "start_u": self._rack_start_u}
        return None

    def _calculate_width(self):
        if self.device_type == DEVICE_PC:
            return 120
        elif self.device_type == DEVICE_PHONE:
            return 50
        elif self.device_type == DEVICE_HOME_ROUTER:
            return 180
        elif self.device_type == DEVICE_MODEM:
            return 200
        elif self.device_type == DEVICE_NAS:
            return 180
        elif self.device_type == DEVICE_AC:
            return PANEL_WIDTH_PX
        elif self.device_type == DEVICE_AP:
            return 100
        elif self.device_type == DEVICE_ISP:
            return 120
        elif self.device_type == DEVICE_ISP_DUAL:
            return 160
        elif self.device_type in [DEVICE_SERVER, DEVICE_SWITCH, DEVICE_ROUTER]:
            return PANEL_WIDTH_PX
        return PANEL_WIDTH_PX

    def _calculate_height(self):
        if self.device_type == DEVICE_PC:
            return 80
        elif self.device_type == DEVICE_PHONE:
            return 90
        elif self.device_type == DEVICE_HOME_ROUTER:
            return 60
        elif self.device_type == DEVICE_MODEM:
            return 50
        elif self.device_type == DEVICE_NAS:
            return 80
        elif self.device_type == DEVICE_AP:
            return 100
        elif self.device_type == DEVICE_ISP:
            return 80
        elif self.device_type == DEVICE_ISP_DUAL:
            return 80
        elif self.device_type in [DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_AC, DEVICE_SERVER]:
            return U_HEIGHT_PX * self.u_size
        return U_HEIGHT_PX

    def _create_ports(self):
        if self.renderer_key == "huawei_s5735_l24t4x":
            self._create_huawei_s5735_ports()
        elif self.device_type in [DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_PC, DEVICE_PHONE, DEVICE_HOME_ROUTER, DEVICE_MODEM, DEVICE_NAS, DEVICE_AC, DEVICE_AP, DEVICE_ISP, DEVICE_ISP_DUAL, DEVICE_SERVER]:
            self._create_special_device_ports()
        else:
            self._create_default_ports()
    
    def _create_special_device_ports(self):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        ports_config = self.port_config.get("ports", [])
        if not ports_config:
            return
        
        if self.device_type == DEVICE_SWITCH:
            self._create_switch_ports(ports_config)
        elif self.device_type == DEVICE_ROUTER:
            self._create_router_ports(ports_config)
        elif self.device_type == DEVICE_PC:
            self._create_pc_ports(ports_config)
        elif self.device_type == DEVICE_PHONE:
            self._create_phone_ports(ports_config)
        elif self.device_type == DEVICE_HOME_ROUTER:
            self._create_home_router_ports(ports_config)
        elif self.device_type == DEVICE_MODEM:
            self._create_modem_ports(ports_config)
        elif self.device_type == DEVICE_NAS:
            self._create_nas_ports(ports_config)
        elif self.device_type == DEVICE_AC:
            self._create_ac_ports(ports_config)
        elif self.device_type == DEVICE_AP:
            self._create_ap_ports(ports_config)
        elif self.device_type == DEVICE_ISP:
            self._create_isp_ports(ports_config)
        elif self.device_type == DEVICE_ISP_DUAL:
            self._create_isp_dual_ports(ports_config)
        elif self.device_type == DEVICE_SERVER:
            self._create_server_ports(ports_config)
        else:
            self._create_default_special_ports(ports_config)
    
    def _create_pc_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        host_x = 5
        host_y = 5
        host_w = 25
        host_h = 55
        
        for i, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{i+1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port_width = RJ45_WIDTH
            port_height = RJ45_HEIGHT
            
            port_x = host_x + 3
            port_y = host_y + 14 + i * (port_height + 2)
            
            port = PortItem(port_id, port_type, self)
            port.setPos(port_x + port_width / 2, port_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port
    
    def _sort_ports_by_type(self, ports_config, device_type=None):
        from .port_item import PORT_TYPE_ETHERNET, PORT_TYPE_FIBER, PORT_TYPE_CONSOLE, PORT_TYPE_USB
        
        if device_type == DEVICE_MODEM:
            type_order = {
                PORT_TYPE_FIBER: 0,
                "fiber": 0,
                "fiber_sc": 0,
                PORT_TYPE_ETHERNET: 1,
                "ethernet": 1,
                PORT_TYPE_CONSOLE: 2,
                "console": 2,
                PORT_TYPE_USB: 3,
                "usb": 3
            }
        else:
            type_order = {
                PORT_TYPE_ETHERNET: 0,
                "ethernet": 0,
                PORT_TYPE_FIBER: 1,
                "fiber": 1,
                "fiber_sc": 1,
                PORT_TYPE_CONSOLE: 2,
                "console": 2,
                PORT_TYPE_USB: 3,
                "usb": 3
            }
        return sorted(ports_config, key=lambda p: type_order.get(p.get("type", PORT_TYPE_ETHERNET), 99))

    def _create_switch_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_w = PANEL_WIDTH_PX - 10
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 5
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_id = port_cfg.get("id", "P")
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                if port_type == "fiber_sc":
                    port_type = PORT_TYPE_FIBER
                
                port_width = RJ45_WIDTH
                port_height = RJ45_HEIGHT
                
                port = PortItem(port_id, port_type, self)
                port.setPos(current_x + port_width / 2, ports_y + port_height / 2)
                self.ports.append(port)
                self._port_map[port_id] = port
                
                current_x += port_width + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row1_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row2_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _create_router_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_w = self._width - 10
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_id = port_cfg.get("id", "P")
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                if port_type == "fiber_sc":
                    port_type = PORT_TYPE_FIBER
                
                port_width = RJ45_WIDTH
                port_height = RJ45_HEIGHT
                
                port = PortItem(port_id, port_type, self)
                port.setPos(current_x + port_width / 2, ports_y + port_height / 2)
                self.ports.append(port)
                self._port_map[port_id] = port
                
                current_x += port_width + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row1_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row2_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _create_home_router_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        panel_w = 150
        panel_h = 30
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        ports_y = panel_y + (panel_h - RJ45_HEIGHT) // 2
        
        for i, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{i+1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port_width = RJ45_WIDTH
            port_height = RJ45_HEIGHT
            
            port_x = ports_start_x + i * (port_width + port_gap)
            
            port = PortItem(port_id, port_type, self)
            port.setPos(port_x + port_width / 2, ports_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port
    
    def _create_modem_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        panel_w = 180
        panel_h = 30
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        ports_y = panel_y + (panel_h - RJ45_HEIGHT) // 2
        
        current_x = ports_start_x
        for port_cfg in sorted_ports:
            port_id = port_cfg.get("id", "P")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port_width = RJ45_WIDTH
            port_height = RJ45_HEIGHT
            
            port = PortItem(port_id, port_type, self)
            port.setPos(current_x + port_width / 2, ports_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port
            
            current_x += port_width + port_gap
    
    def _create_nas_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        # 使用与_draw_nas_icon相同的面板尺寸
        panel_w = 150
        panel_h = 55
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_gap = PORT_GAP_X
        # 移动到右下角，与_draw_nas_ports保持一致
        margin = 4
        total_ports_width = len(ports_config) * RJ45_WIDTH + (len(ports_config) - 1) * port_gap
        port_x = panel_x + panel_w - margin - total_ports_width
        port_y = panel_y + panel_h - margin - RJ45_HEIGHT
        
        for i, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{i+1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port_width = RJ45_WIDTH if port_type == PORT_TYPE_ETHERNET else SFP_WIDTH
            port_height = RJ45_HEIGHT if port_type == PORT_TYPE_ETHERNET else SFP_HEIGHT
            
            px = port_x + i * (port_width + port_gap)
            
            port = PortItem(port_id, port_type, self)
            port.setPos(px + port_width / 2, port_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port
    
    def _create_ac_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_w = self._width - 10
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_id = port_cfg.get("id", "P")
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                if port_type == "fiber_sc":
                    port_type = PORT_TYPE_FIBER
                
                port_width = RJ45_WIDTH
                port_height = RJ45_HEIGHT
                
                port = PortItem(port_id, port_type, self)
                port.setPos(current_x + port_width / 2, ports_y + port_height / 2)
                self.ports.append(port)
                self._port_map[port_id] = port
                
                current_x += port_width + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row1_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row2_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _create_ap_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        # 使用与_draw_ap_icon相同的面板尺寸
        panel_w = 70
        panel_h = 70
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_width = RJ45_WIDTH
        port_height = RJ45_HEIGHT
        # 将逻辑接口放在WiFi图形正下方，与_draw_ap_ports保持一致
        cx = panel_x + panel_w // 2  # WiFi中心X坐标
        cy = panel_y + panel_h // 2  # WiFi中心Y坐标
        port_x = cx - port_width // 2  # 水平居中
        port_y = cy + 14  # WiFi底部下方适当间距
        
        for i, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{i+1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port = PortItem(port_id, port_type, self)
            port.setPos(port_x + port_width / 2, port_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port
    
    def _create_isp_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        cloud_w = 100
        cloud_h = 60
        cloud_x = (self._width - cloud_w) // 2
        cloud_y = 10
        
        port_width = RJ45_WIDTH
        port_height = RJ45_HEIGHT
        port_x = cloud_x + cloud_w // 2 - port_width // 2
        port_y = cloud_y + 40
        
        for i, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{i+1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port = PortItem(port_id, port_type, self)
            port.setPos(port_x + port_width / 2, port_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port
    
    def _create_isp_dual_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        cloud_w = 140
        cloud_h = 60
        cloud_x = (self._width - cloud_w) // 2
        cloud_y = 10
        
        port_width = RJ45_WIDTH
        port_height = RJ45_HEIGHT
        port_gap = 8
        
        total_width = 2 * port_width + port_gap
        start_x = cloud_x + cloud_w // 2 - total_width // 2
        port_y = cloud_y + 40
        
        for i, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{i+1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port_x = start_x + i * (port_width + port_gap)
            
            port = PortItem(port_id, port_type, self)
            port.setPos(port_x + port_width / 2, port_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port
    
    def _create_phone_ports(self, ports_config):
        pass
    
    def _create_server_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_w = self._width - 10
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_id = port_cfg.get("id", "P")
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                if port_type == "fiber_sc":
                    port_type = PORT_TYPE_FIBER
                
                port_width = RJ45_WIDTH
                port_height = RJ45_HEIGHT
                
                port = PortItem(port_id, port_type, self)
                port.setPos(current_x + port_width / 2, ports_y + port_height / 2)
                self.ports.append(port)
                self._port_map[port_id] = port
                
                current_x += port_width + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row1_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, row2_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_id = port_cfg.get("id", "P")
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    port = PortItem(port_id, port_type, self)
                    port.setPos(current_x + RJ45_WIDTH / 2, port_y + RJ45_HEIGHT / 2)
                    self.ports.append(port)
                    self._port_map[port_id] = port
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _create_default_special_ports(self, ports_config):
        from .port_item import PORT_TYPE_FIBER, PORT_TYPE_ETHERNET
        
        port_gap = PORT_GAP_X
        start_x = 10
        start_y = self._height - 12
        
        for i, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{i+1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            
            port_width = RJ45_WIDTH if port_type == PORT_TYPE_ETHERNET else SFP_WIDTH
            port_height = RJ45_HEIGHT if port_type == PORT_TYPE_ETHERNET else SFP_HEIGHT
            
            port_x = start_x + i * (port_width + port_gap)
            
            port = PortItem(port_id, port_type, self)
            port.setPos(port_x + port_width / 2, start_y + port_height / 2)
            self.ports.append(port)
            self._port_map[port_id] = port

    def _create_huawei_s5735_ports(self):
        rj45_width = 16
        rj45_height = 12
        rj45_gap_x = 3
        rj45_gap_y = 2
        group_gap = 10
        
        start_x = 8
        start_y = 5
        
        port_index = 1
        for col in range(12):
            col_x = start_x + col * (rj45_width + rj45_gap_x)
            if col > 0 and col % 4 == 0:
                col_x += group_gap - rj45_gap_x
            
            port = PortItem(f"GE0/0/{port_index}", PORT_TYPE_ETHERNET, self)
            port.setPos(col_x + rj45_width / 2, start_y + rj45_height / 2)
            self.ports.append(port)
            self._port_map[f"GE0/0/{port_index}"] = port
            port_index += 1
            
            port = PortItem(f"GE0/0/{port_index}", PORT_TYPE_ETHERNET, self)
            port.setPos(col_x + rj45_width / 2, start_y + rj45_height + rj45_gap_y + rj45_height / 2)
            self.ports.append(port)
            self._port_map[f"GE0/0/{port_index}"] = port
            port_index += 1
        
        rj45_total_width = 12 * rj45_width + 11 * rj45_gap_x + 2 * group_gap
        sfp_start_x = start_x + rj45_total_width + 10
        sfp_width = 11
        sfp_height = 14
        sfp_gap = 2
        
        for i in range(4):
            port_x = sfp_start_x + i * (sfp_width + sfp_gap)
            port = PortItem(f"XG0/0/{i + 1}", PORT_TYPE_FIBER, self)
            port.setPos(port_x + sfp_width / 2, start_y + 2 + sfp_height / 2)
            self.ports.append(port)
            self._port_map[f"XG0/0/{i + 1}"] = port

    def _create_default_ports(self):
        from .port_item import PORT_TYPE_ETHERNET, PORT_TYPE_FIBER, PORT_TYPE_CONSOLE, PORT_TYPE_USB
        
        ports_config = self.port_config.get("ports", [])
        
        port_width = RJ45_WIDTH
        port_height = RJ45_HEIGHT
        port_gap = PORT_GAP_X
        
        start_x = 10
        start_y = 5
        
        for idx, port_cfg in enumerate(ports_config):
            port_id = port_cfg.get("id", f"P{idx + 1}")
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            
            port = PortItem(port_id, port_type, self)
            pos_x = start_x + idx * (port_width + port_gap) + port_width / 2
            pos_y = start_y + port_height / 2
            port.setPos(pos_x, pos_y)
            
            self.ports.append(port)
            self._port_map[port_id] = port

    def boundingRect(self):
        font_size = self.label_config.get("font_size", 4)
        font_family = self.label_config.get("font_family", "Arial")
        font = QFont(font_family, font_size)
        from PySide6.QtGui import QFontMetrics
        font_metrics = QFontMetrics(font)
        text_height = font_metrics.height()
        text_width = font_metrics.horizontalAdvance(self.node_id)
        
        # 交换机、路由器、服务器、AC设备的标签在右下角外部
        if self.device_type in [DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_SERVER, DEVICE_AC]:
            label_font = QFont("微软雅黑", 10)
            label_metrics = QFontMetrics(label_font)
            label_width = label_metrics.horizontalAdvance(self.node_id)
            label_height = label_metrics.height()
            # 右侧和底部需要额外空间
            extra_right = label_width + 10
            extra_bottom = label_height + 5
            return QRectF(-2, -2, self._width + extra_right + 4, self._height + extra_bottom + 4)
        
        extra_left = max(text_width - int(self._width) + 8, 2)
        extra_bottom = text_height + 4
        
        return QRectF(-extra_left, -2, self._width + extra_left + 4, self._height + extra_bottom)

    def paint(self, painter: QPainter, option, widget=None):
        if self.renderer_key and self.renderer_key in RENDERER_MAP:
            renderer = RENDERER_MAP[self.renderer_key]
            renderer.draw_panel(painter, QRectF(0, 0, self._width, self._height), self.node_id)
            
            if self._is_fixed:
                painter.setPen(QPen(QColor(255, 200, 0), 3))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(-2, -2, int(self._width) + 4, int(self._height) + 4, 3, 3)
            
            if self.isSelected():
                painter.setPen(QPen(QColor(255, 100, 100), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(0, 0, int(self._width), int(self._height), 2, 2)
        elif self.device_type in [DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_PC, DEVICE_PHONE, DEVICE_HOME_ROUTER, DEVICE_MODEM, DEVICE_NAS, DEVICE_AC, DEVICE_AP, DEVICE_ISP, DEVICE_ISP_DUAL, DEVICE_SERVER]:
            self._paint_special_device(painter)
        else:
            self._paint_default(painter)

    def _paint_default(self, painter):
        from .port_item import PORT_TYPE_ETHERNET, PORT_TYPE_FIBER, PORT_TYPE_CONSOLE, PORT_TYPE_USB, PORT_COLORS
        
        if self.vendor and self.vendor in VENDOR_COLORS:
            base_color = VENDOR_COLORS[self.vendor]
        else:
            base_color = DEVICE_COLORS.get(self.device_type, QColor(160, 160, 160))
        
        painter.setPen(QPen(QColor(40, 40, 40), 0.5))
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRect(2, 2, int(self._width) - 4, int(self._height) - 4)
        
        self._draw_label(painter)
        
        if self._is_fixed:
            painter.setPen(QPen(QColor(255, 200, 0), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(-2, -2, int(self._width) + 4, int(self._height) + 4, 3, 3)
        
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 100, 100), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            if self.device_type == DEVICE_ISP:
                cloud_w = 100
                cloud_h = 60
                cloud_x = (self._width - cloud_w) // 2
                cloud_y = 10
                # 绘制云朵形状的选中框，稍微扩大一些
                from PySide6.QtGui import QPainterPath
                selection_path = QPainterPath()
                offset = 3
                selection_path.moveTo(cloud_x + 20 - offset, cloud_y + cloud_h + offset)
                selection_path.cubicTo(cloud_x - 10 - offset, cloud_y + cloud_h + offset,
                             cloud_x - 10 - offset, cloud_y + 20 - offset,
                             cloud_x + 15 - offset, cloud_y + 20 - offset)
                selection_path.cubicTo(cloud_x + 10 - offset, cloud_y - offset,
                             cloud_x + 30 - offset, cloud_y - 5 - offset,
                             cloud_x + 45 - offset, cloud_y + 10 - offset)
                selection_path.cubicTo(cloud_x + 50 - offset, cloud_y - offset,
                             cloud_x + 80 + offset, cloud_y - offset,
                             cloud_x + 85 + offset, cloud_y + 25 - offset)
                selection_path.cubicTo(cloud_x + cloud_w + 10 + offset, cloud_y + 25 - offset,
                             cloud_x + cloud_w + 10 + offset, cloud_y + cloud_h + offset,
                             cloud_x + 80 + offset, cloud_y + cloud_h + offset)
                selection_path.closeSubpath()
                painter.drawPath(selection_path)
            else:
                painter.drawRoundedRect(0, 0, int(self._width), int(self._height), 2, 2)
    
    def _draw_server_icon(self, painter):
        panel_w = self._width - 10
        panel_h = self._height - 2
        panel_x = 5
        panel_y = 1
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(200, 180, 160)))
        painter.drawRoundedRect(int(panel_x), int(panel_y), panel_w, panel_h, 2, 2)
        
        painter.setPen(QPen(QColor(50, 50, 50), 0.5))
        painter.setBrush(QBrush(QColor(180, 160, 140)))
        painter.drawRect(int(panel_x + 5), int(panel_y + 3), panel_w - 20, panel_h - 6)
        
        led_y = panel_y + 5
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 12), int(led_y), 3, 3)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 20), int(led_y), 3, 3)
        
        font = QFont("微软雅黑", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        text_x = int(self._width) + 5
        text_y = int(self._height) + 2
        painter.drawText(text_x, text_y, self.node_id)
    
    def _draw_default_special_device(self, painter):
        # 默认特殊设备绘制
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(DEVICE_COLORS.get(self.device_type, QColor(160, 160, 160))))
        painter.drawRoundedRect(5, 5, int(self._width) - 10, int(self._height) - 10, 2, 2)
    
    def _draw_port(self, painter, x, y, width, height, port_type):
        from .port_item import PORT_COLORS
        
        color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
        
        painter.setPen(QPen(QColor(30, 30, 30), 0.5))
        painter.setBrush(QBrush(color))
        painter.drawRect(int(x), int(y), int(width), int(height))
        
        painter.setPen(QPen(QColor(255, 255, 255, 50), 0.5))
        painter.drawLine(int(x + 2), int(y + 2), int(x + width - 2), int(y + 2))
    
    def _paint_special_device(self, painter):
        base_color = DEVICE_COLORS.get(self.device_type, QColor(160, 160, 160))
        
        if self.device_type == DEVICE_SWITCH:
            self._draw_switch_icon(painter)
        elif self.device_type == DEVICE_ROUTER:
            self._draw_router_icon(painter)
        elif self.device_type == DEVICE_PC:
            self._draw_pc_icon(painter)
        elif self.device_type == DEVICE_PHONE:
            self._draw_phone_icon(painter)
        elif self.device_type == DEVICE_HOME_ROUTER:
            self._draw_home_router_icon(painter)
        elif self.device_type == DEVICE_MODEM:
            self._draw_modem_icon(painter)
        elif self.device_type == DEVICE_NAS:
            self._draw_nas_icon(painter)
        elif self.device_type == DEVICE_AC:
            self._draw_ac_icon(painter)
        elif self.device_type == DEVICE_AP:
            self._draw_ap_icon(painter)
        elif self.device_type == DEVICE_ISP:
            self._draw_isp_icon(painter)
        elif self.device_type == DEVICE_ISP_DUAL:
            self._draw_isp_dual_icon(painter)
        elif self.device_type == DEVICE_SERVER:
            self._draw_server_icon(painter)
        else:
            self._draw_default_special_device(painter)
        
        self._draw_device_ports(painter)
        
        # 交换机、路由器、服务器、AC设备的标签在各自的 _draw_*_icon 方法中绘制
        if self.device_type not in [DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_SERVER, DEVICE_AC]:
            self._draw_label(painter)
        
        if self._is_fixed:
            painter.setPen(QPen(QColor(255, 200, 0), 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(-2, -2, int(self._width) + 4, int(self._height) + 4, 3, 3)
        
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 100, 100), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            if self.device_type == DEVICE_ISP:
                cloud_w = 100
                cloud_h = 60
                cloud_x = (self._width - cloud_w) // 2
                cloud_y = 10
                from PySide6.QtGui import QPainterPath
                selection_path = QPainterPath()
                offset = 3
                selection_path.moveTo(cloud_x + 20 - offset, cloud_y + cloud_h + offset)
                selection_path.cubicTo(cloud_x - 10 - offset, cloud_y + cloud_h + offset,
                             cloud_x - 10 - offset, cloud_y + 20 - offset,
                             cloud_x + 15 - offset, cloud_y + 20 - offset)
                selection_path.cubicTo(cloud_x + 10 - offset, cloud_y - offset,
                             cloud_x + 30 - offset, cloud_y - 5 - offset,
                             cloud_x + 45 - offset, cloud_y + 10 - offset)
                selection_path.cubicTo(cloud_x + 50 - offset, cloud_y - offset,
                             cloud_x + 80 + offset, cloud_y - offset,
                             cloud_x + 85 + offset, cloud_y + 25 - offset)
                selection_path.cubicTo(cloud_x + cloud_w + 10 + offset, cloud_y + 25 - offset,
                             cloud_x + cloud_w + 10 + offset, cloud_y + cloud_h + offset,
                             cloud_x + 80 + offset, cloud_y + cloud_h + offset)
                selection_path.closeSubpath()
                painter.drawPath(selection_path)
            elif self.device_type == DEVICE_ISP_DUAL:
                cloud_w = 140
                cloud_h = 60
                cloud_x = (self._width - cloud_w) // 2
                cloud_y = 10
                from PySide6.QtGui import QPainterPath
                selection_path = QPainterPath()
                offset = 3
                selection_path.moveTo(cloud_x + 20 - offset, cloud_y + cloud_h + offset)
                selection_path.cubicTo(cloud_x - 10 - offset, cloud_y + cloud_h + offset,
                             cloud_x - 10 - offset, cloud_y + 20 - offset,
                             cloud_x + 15 - offset, cloud_y + 20 - offset)
                selection_path.cubicTo(cloud_x + 10 - offset, cloud_y - offset,
                             cloud_x + 30 - offset, cloud_y - 5 - offset,
                             cloud_x + 45 - offset, cloud_y + 10 - offset)
                selection_path.cubicTo(cloud_x + 50 - offset, cloud_y - offset,
                             cloud_x + cloud_w - 20 + offset, cloud_y - offset,
                             cloud_x + cloud_w - 15 + offset, cloud_y + 25 - offset)
                selection_path.cubicTo(cloud_x + cloud_w + 10 + offset, cloud_y + 25 - offset,
                             cloud_x + cloud_w + 10 + offset, cloud_y + cloud_h + offset,
                             cloud_x + cloud_w - 20 + offset, cloud_y + cloud_h + offset)
                selection_path.closeSubpath()
                painter.drawPath(selection_path)
            elif self.device_type == DEVICE_MODEM:
                panel_w = 180
                panel_h = 30
                panel_x = (self._width - panel_w) // 2
                panel_y = 5
                painter.drawRoundedRect(int(panel_x - 2), int(panel_y - 2), panel_w + 4, panel_h + 4, 3, 3)
            elif self.device_type == DEVICE_PC:
                host_w = 25
                host_h = 55
                monitor_w = 40
                monitor_h = 28
                keyboard_w = 30
                keyboard_h = 6
                mouse_w = 6
                mouse_h = 10
                
                host_x = 5
                host_y = 5
                monitor_x = host_x + host_w + 8
                monitor_y = 6
                keyboard_x = monitor_x - 5
                keyboard_y = monitor_y + monitor_h + 10
                mouse_x = keyboard_x + keyboard_w + 4
                mouse_y = keyboard_y - 1
                
                total_w = max(host_x + host_w, monitor_x + monitor_w, keyboard_x + keyboard_w, mouse_x + mouse_w)
                total_h = max(host_y + host_h, monitor_y + monitor_h + 6, keyboard_y + keyboard_h, mouse_y + mouse_h)
                
                painter.drawRoundedRect(3, 3, int(total_w) - 3, int(total_h) - 3, 3, 3)
            elif self.device_type == DEVICE_PHONE:
                phone_w = 20
                phone_h = 45
                phone_x = (self._width - phone_w) // 2
                phone_y = 5
                painter.drawRoundedRect(int(phone_x - 3), int(phone_y - 3), phone_w + 6, phone_h + 6, 5, 5)
            elif self.device_type == DEVICE_HOME_ROUTER:
                panel_w = 150
                panel_h = 30
                panel_x = (self._width - panel_w) // 2
                panel_y = 5
                painter.drawRoundedRect(int(panel_x - 2), int(panel_y - 2), panel_w + 4, panel_h + 4, 3, 3)
            elif self.device_type == DEVICE_NAS:
                panel_w = 150
                panel_h = 55
                panel_x = (self._width - panel_w) // 2
                panel_y = 5
                painter.drawRoundedRect(int(panel_x - 2), int(panel_y - 2), panel_w + 4, panel_h + 4, 4, 4)
            elif self.device_type == DEVICE_AC:
                panel_x = 5
                panel_y = 2
                panel_w = self._width - 10
                panel_h = self._height - 4
                painter.drawRoundedRect(int(panel_x - 2), int(panel_y - 2), int(panel_w) + 4, int(panel_h) + 4, 3, 3)
            elif self.device_type == DEVICE_AP:
                panel_w = 70
                panel_h = 70
                panel_x = (self._width - panel_w) // 2
                panel_y = 5
                painter.drawEllipse(int(panel_x - 3), int(panel_y - 3), panel_w + 6, panel_h + 6)
            elif self.device_type == DEVICE_SWITCH:
                panel_x = 5
                panel_y = 2
                panel_w = PANEL_WIDTH_PX - 10
                panel_h = U_HEIGHT_PX * self.u_size - 4
                painter.drawRoundedRect(int(panel_x - 2), int(panel_y - 2), panel_w + 4, panel_h + 4, 3, 3)
            elif self.device_type == DEVICE_ROUTER:
                panel_x = 5
                panel_y = 2
                panel_w = self._width - 10
                panel_h = self._height - 4
                painter.drawRoundedRect(int(panel_x - 2), int(panel_y - 2), int(panel_w) + 4, int(panel_h) + 4, 3, 3)
            elif self.device_type == DEVICE_SERVER:
                panel_x = 5
                panel_y = 1
                panel_w = self._width - 10
                panel_h = self._height - 2
                painter.drawRoundedRect(int(panel_x - 2), int(panel_y - 2), int(panel_w) + 4, int(panel_h) + 4, 3, 3)
            else:
                painter.drawRoundedRect(0, 0, int(self._width), int(self._height), 2, 2)
    
    def _draw_device_ports(self, painter):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        ports_config = self.port_config.get("ports", [])
        if not ports_config:
            return
        
        if self.device_type == DEVICE_SWITCH:
            self._draw_switch_ports(painter, ports_config)
        elif self.device_type == DEVICE_ROUTER:
            self._draw_router_ports(painter, ports_config)
        elif self.device_type == DEVICE_PC:
            self._draw_pc_ports(painter, ports_config)
        elif self.device_type == DEVICE_PHONE:
            pass
        elif self.device_type == DEVICE_HOME_ROUTER:
            self._draw_home_router_ports(painter, ports_config)
        elif self.device_type == DEVICE_MODEM:
            self._draw_modem_ports(painter, ports_config)
        elif self.device_type == DEVICE_NAS:
            self._draw_nas_ports(painter, ports_config)
        elif self.device_type == DEVICE_AC:
            self._draw_ac_ports(painter, ports_config)
        elif self.device_type == DEVICE_AP:
            self._draw_ap_ports(painter, ports_config)
        elif self.device_type == DEVICE_ISP:
            self._draw_isp_ports(painter, ports_config)
        elif self.device_type == DEVICE_ISP_DUAL:
            self._draw_isp_dual_ports(painter, ports_config)
        else:
            self._draw_default_ports(painter, ports_config)
    
    def _draw_label(self, painter):
        text_color = self.label_config.get("text_color", "#323232")
        font_size = self.label_config.get("font_size", 4)
        font_family = self.label_config.get("font_family", "Arial")
        position = self.label_config.get("position", "bottom_right")
        custom_x = self.label_config.get("custom_x", 0)
        custom_y = self.label_config.get("custom_y", 0)
        
        painter.setPen(QPen(QColor(text_color), 0.5))
        font = QFont(font_family, font_size)
        painter.setFont(font)
        
        text_width = painter.fontMetrics().horizontalAdvance(self.node_id)
        text_height = painter.fontMetrics().height()
        
        if position == "bottom_right":
            text_x = int(self._width) - text_width - 3
            text_y = int(self._height) - 3
        elif position == "bottom_left":
            text_x = 3
            text_y = int(self._height) - 3
        elif position == "top_right":
            text_x = int(self._width) - text_width - 3
            text_y = text_height + 3
        elif position == "top_left":
            text_x = 3
            text_y = text_height + 3
        elif position == "center":
            text_x = (int(self._width) - text_width) // 2
            text_y = (int(self._height) + text_height) // 2
        elif position == "custom":
            text_x = int(self._width) - text_width - 3 + custom_x
            text_y = int(self._height) - 3 + custom_y
        else:
            text_x = int(self._width) - text_width - 3
            text_y = int(self._height) - 3
        
        # 设备特定的位置调整
        if self.device_type == DEVICE_MODEM:
            text_y += 5
        elif self.device_type == DEVICE_PC:
            text_x -= 14
            text_y -= 5
        elif self.device_type == DEVICE_ISP:
            text_y += 9
        elif self.device_type == DEVICE_ISP_DUAL:
            text_y += 9
        elif self.device_type == DEVICE_HOME_ROUTER:
            text_y -= 5
        elif self.device_type == DEVICE_PHONE:
            text_y -= 15
        
        painter.drawText(text_x, text_y, self.node_id)
    
    def _draw_pc_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        host_x = 5
        host_y = 5
        host_w = 25
        host_h = 55
        
        for i, port_cfg in enumerate(ports_config):
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
            port_width = RJ45_WIDTH
            port_height = RJ45_HEIGHT
            
            port_x = host_x + 3
            port_y = host_y + 14 + i * (port_height + 2)
            
            painter.setPen(QPen(QColor(30, 30, 30), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(port_x), int(port_y), port_width, port_height)
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
            painter.drawLine(int(port_x + 1), int(port_y + 1), 
                           int(port_x + port_width - 1), int(port_y + 1))
    
    def _draw_switch_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_w = PANEL_WIDTH_PX - 10
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 5
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                
                port_width = RJ45_WIDTH
                port_height = RJ45_HEIGHT
                
                painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                painter.setBrush(QBrush(color))
                painter.drawRect(int(current_x), int(ports_y), port_width, port_height)
                
                painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                painter.drawLine(int(current_x + 1), int(ports_y + 1), 
                               int(current_x + port_width - 1), int(ports_y + 1))
                
                current_x += port_width + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row1_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row1_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row1_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row2_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row2_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row2_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _draw_router_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_w = self._width - 10
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                if port_type == "fiber_sc":
                    port_type = PORT_TYPE_FIBER
                color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                
                painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                painter.setBrush(QBrush(color))
                painter.drawRect(int(current_x), int(ports_y), RJ45_WIDTH, RJ45_HEIGHT)
                
                painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                painter.drawLine(int(current_x + 1), int(ports_y + 1), 
                               int(current_x + RJ45_WIDTH - 1), int(ports_y + 1))
                
                current_x += RJ45_WIDTH + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row1_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row1_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row1_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row2_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row2_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row2_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    if port_type == "fiber_sc":
                        port_type = PORT_TYPE_FIBER
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _draw_home_router_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        panel_w = 150
        panel_h = 30
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        ports_y = panel_y + (panel_h - RJ45_HEIGHT) // 2
        
        for i, port_cfg in enumerate(ports_config):
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
            
            port_width = RJ45_WIDTH
            port_height = RJ45_HEIGHT
            port_x = ports_start_x + i * (port_width + port_gap)
            port_y = ports_y
            
            painter.setPen(QPen(QColor(30, 30, 30), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(port_x), int(port_y), port_width, port_height)
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
            painter.drawLine(int(port_x + 1), int(port_y + 1), 
                           int(port_x + port_width - 1), int(port_y + 1))
    
    def _draw_modem_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        panel_w = 180
        panel_h = 30
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        ports_y = panel_y + (panel_h - RJ45_HEIGHT) // 2
        
        current_x = ports_start_x
        for port_cfg in sorted_ports:
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
            
            port_width = RJ45_WIDTH
            port_height = RJ45_HEIGHT
            
            painter.setPen(QPen(QColor(30, 30, 30), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(current_x), int(ports_y), port_width, port_height)
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
            painter.drawLine(int(current_x + 1), int(ports_y + 1), 
                           int(current_x + port_width - 1), int(ports_y + 1))
            
            current_x += port_width + port_gap
    
    def _draw_nas_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        # 使用与_draw_nas_icon相同的面板尺寸
        panel_w = 150
        panel_h = 55
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_gap = PORT_GAP_X
        # 移动到选中框右下角，保持适当边距
        margin = 4
        # 从右向左排列端口
        total_ports_width = len(ports_config) * RJ45_WIDTH + (len(ports_config) - 1) * port_gap
        port_x = panel_x + panel_w - margin - total_ports_width
        port_y = panel_y + panel_h - margin - RJ45_HEIGHT
        
        for i, port_cfg in enumerate(ports_config):
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
            port_width = RJ45_WIDTH if port_type == PORT_TYPE_ETHERNET else SFP_WIDTH
            port_height = RJ45_HEIGHT if port_type == PORT_TYPE_ETHERNET else SFP_HEIGHT
            
            px = port_x + i * (port_width + port_gap)
            
            painter.setPen(QPen(QColor(30, 30, 30), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(px), int(port_y), port_width, port_height)
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
            painter.drawLine(int(px + 1), int(port_y + 1), 
                           int(px + port_width - 1), int(port_y + 1))
    
    def _draw_ac_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_w = self._width - 10
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                
                painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                painter.setBrush(QBrush(color))
                painter.drawRect(int(current_x), int(ports_y), RJ45_WIDTH, RJ45_HEIGHT)
                
                painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                painter.drawLine(int(current_x + 1), int(ports_y + 1), 
                               int(current_x + RJ45_WIDTH - 1), int(ports_y + 1))
                
                current_x += RJ45_WIDTH + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row1_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row1_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row1_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row2_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row2_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row2_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _draw_ap_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        # 使用与_draw_ap_icon相同的面板尺寸
        panel_w = 70
        panel_h = 70
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        port_width = RJ45_WIDTH
        port_height = RJ45_HEIGHT
        # 将逻辑接口放在WiFi图形正下方，保持垂直对齐
        cx = panel_x + panel_w // 2  # WiFi中心X坐标
        cy = panel_y + panel_h // 2  # WiFi中心Y坐标
        port_x = cx - port_width // 2  # 水平居中
        port_y = cy + 14  # WiFi底部下方适当间距
        
        for i, port_cfg in enumerate(ports_config):
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
            
            painter.setPen(QPen(QColor(30, 30, 30), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(port_x), int(port_y), port_width, port_height)
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
            painter.drawLine(int(port_x + 1), int(port_y + 1), 
                           int(port_x + port_width - 1), int(port_y + 1))
    
    def _draw_isp_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        cloud_w = 100
        cloud_h = 60
        cloud_x = (self._width - cloud_w) // 2
        cloud_y = 10
        
        port_width = RJ45_WIDTH
        port_height = RJ45_HEIGHT
        port_x = cloud_x + cloud_w // 2 - port_width // 2
        port_y = cloud_y + 40
        
        for i, port_cfg in enumerate(ports_config):
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
            
            painter.setPen(QPen(QColor(30, 30, 30), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(port_x), int(port_y), port_width, port_height)
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
            painter.drawLine(int(port_x + 1), int(port_y + 1), 
                           int(port_x + port_width - 1), int(port_y + 1))
    
    def _draw_isp_dual_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET, PORT_TYPE_FIBER
        
        cloud_w = 140
        cloud_h = 60
        cloud_x = (self._width - cloud_w) // 2
        cloud_y = 10
        
        port_width = RJ45_WIDTH
        port_height = RJ45_HEIGHT
        port_gap = 8
        
        total_width = 2 * port_width + port_gap
        start_x = cloud_x + cloud_w // 2 - total_width // 2
        port_y = cloud_y + 40
        
        for i, port_cfg in enumerate(ports_config):
            port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
            if port_type == "fiber_sc":
                port_type = PORT_TYPE_FIBER
            color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
            
            port_x = start_x + i * (port_width + port_gap)
            
            painter.setPen(QPen(QColor(30, 30, 30), 0.5))
            painter.setBrush(QBrush(color))
            painter.drawRect(int(port_x), int(port_y), port_width, port_height)
            
            painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
            painter.drawLine(int(port_x + 1), int(port_y + 1), 
                           int(port_x + port_width - 1), int(port_y + 1))
    
    def _draw_default_ports(self, painter, ports_config):
        from .port_item import PORT_COLORS, PORT_TYPE_ETHERNET
        
        sorted_ports = self._sort_ports_by_type(ports_config, self.device_type)
        
        layout_mode = self.port_config.get("layout_mode", "single")
        sort_style = self.port_config.get("sort_style", "linear")
        
        panel_x = 5
        panel_y = 2
        
        port_gap = PORT_GAP_X
        ports_start_x = panel_x + 10
        
        if layout_mode == "single":
            ports_y = panel_y + (self._height - RJ45_HEIGHT) // 2
            
            current_x = ports_start_x
            for port_cfg in sorted_ports:
                port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                
                painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                painter.setBrush(QBrush(color))
                painter.drawRect(int(current_x), int(ports_y), RJ45_WIDTH, RJ45_HEIGHT)
                
                painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                painter.drawLine(int(current_x + 1), int(ports_y + 1), 
                               int(current_x + RJ45_WIDTH - 1), int(ports_y + 1))
                
                current_x += RJ45_WIDTH + port_gap
        else:
            row_gap = 4
            total_height = RJ45_HEIGHT * 2 + row_gap
            row1_y = (self._height - total_height) // 2
            row2_y = row1_y + RJ45_HEIGHT + row_gap
            
            if sort_style == "linear":
                half = (len(sorted_ports) + 1) // 2
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[:half]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row1_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row1_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row1_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
                
                current_x = ports_start_x
                for port_cfg in sorted_ports[half:]:
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(row2_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(row2_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(row2_y + 1))
                    
                    current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "n_shape":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row2_y
                    else:
                        port_y = row1_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
            
            elif sort_style == "mirror_n":
                current_x = ports_start_x
                for i, port_cfg in enumerate(sorted_ports):
                    port_type = port_cfg.get("type", PORT_TYPE_ETHERNET)
                    color = PORT_COLORS.get(port_type, QColor(0, 150, 0))
                    
                    if i % 2 == 0:
                        port_y = row1_y
                    else:
                        port_y = row2_y
                    
                    painter.setPen(QPen(QColor(30, 30, 30), 0.5))
                    painter.setBrush(QBrush(color))
                    painter.drawRect(int(current_x), int(port_y), RJ45_WIDTH, RJ45_HEIGHT)
                    
                    painter.setPen(QPen(QColor(255, 255, 255, 100), 0.5))
                    painter.drawLine(int(current_x + 1), int(port_y + 1), 
                                   int(current_x + RJ45_WIDTH - 1), int(port_y + 1))
                    
                    if i % 2 == 1:
                        current_x += RJ45_WIDTH + port_gap
    
    def _draw_pc_icon(self, painter):
        host_w = 25
        host_h = 55
        monitor_w = 40
        monitor_h = 28
        keyboard_w = 30
        keyboard_h = 6
        mouse_w = 6
        mouse_h = 10
        
        host_x = 5
        host_y = 5
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawRect(host_x, host_y, host_w, host_h)
        
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.drawRect(host_x + 2, host_y + 2, host_w - 4, 10)
        
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(host_x + 4, host_y + 15, 2, 2)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(host_x + 4, host_y + 20, 2, 2)
        
        for i in range(3):
            painter.setBrush(QBrush(QColor(80, 80, 80)))
            painter.drawRect(host_x + 4, host_y + 25 + i * 3, 12, 2)
        
        monitor_x = host_x + host_w + 8
        monitor_y = 6
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawRect(monitor_x, monitor_y, monitor_w, monitor_h)
        
        painter.setBrush(QBrush(QColor(100, 150, 200)))
        painter.drawRect(monitor_x + 2, monitor_y + 2, monitor_w - 4, monitor_h - 4)
        
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        stand_w = 6
        stand_h = 4
        painter.drawRect(monitor_x + (monitor_w - stand_w) // 2, monitor_y + monitor_h, stand_w, stand_h)
        painter.drawRect(monitor_x + (monitor_w - 16) // 2, monitor_y + monitor_h + stand_h, 16, 2)
        
        keyboard_x = monitor_x - 5
        keyboard_y = monitor_y + monitor_h + 10
        
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawRect(keyboard_x, keyboard_y, keyboard_w, keyboard_h)
        
        painter.setPen(QPen(QColor(100, 100, 100), 0.5))
        for row in range(2):
            for col in range(7):
                key_x = keyboard_x + 2 + col * 4
                key_y = keyboard_y + 1 + row * 2
                painter.drawRect(key_x, key_y, 3, 2)
        
        mouse_x = keyboard_x + keyboard_w + 4
        mouse_y = keyboard_y - 1
        
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawRoundedRect(mouse_x, mouse_y, mouse_w, mouse_h, 2, 2)
        
        painter.setPen(QPen(QColor(60, 60, 60), 0.5))
        painter.drawLine(mouse_x + mouse_w // 2, mouse_y, mouse_x + mouse_w // 2, mouse_y + 3)
    
    def _draw_phone_icon(self, painter):
        phone_w = 20
        phone_h = 45
        screen_w = 16
        screen_h = 34
        
        phone_x = (self._width - phone_w) // 2
        phone_y = 5
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawRoundedRect(int(phone_x), int(phone_y), phone_w, phone_h, 3, 3)
        
        painter.setBrush(QBrush(QColor(20, 20, 20)))
        painter.drawRoundedRect(int(phone_x + 2), int(phone_y + 5), screen_w, screen_h, 2, 2)
        
        painter.setBrush(QBrush(QColor(150, 200, 255)))
        painter.drawRect(int(phone_x + 3), int(phone_y + 6), screen_w - 2, screen_h - 2)
        
        painter.setBrush(QBrush(QColor(80, 80, 80)))
        painter.drawEllipse(int(phone_x + phone_w // 2 - 2), int(phone_y + 2), 4, 2)
        
        painter.setBrush(QBrush(QColor(50, 50, 50)))
        painter.drawEllipse(int(phone_x + phone_w // 2 - 1), int(phone_y + phone_h - 3), 2, 2)
        
        wifi_x = phone_x + phone_w + 2
        wifi_y = phone_y + 5
        
        painter.setPen(QPen(QColor(100, 200, 100), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        painter.drawArc(int(wifi_x), int(wifi_y), 10, 6, 0, 180 * 16)
        painter.drawArc(int(wifi_x + 2), int(wifi_y + 2), 6, 4, 0, 180 * 16)
        painter.drawArc(int(wifi_x + 4), int(wifi_y + 4), 2, 2, 0, 180 * 16)
        
        painter.setBrush(QBrush(QColor(100, 200, 100)))
        painter.drawEllipse(int(wifi_x + 4), int(wifi_y + 7), 2, 2)
    
    def _draw_router_icon(self, painter):
        panel_w = self._width - 10
        panel_h = self._height - 4
        panel_x = 5
        panel_y = 2
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(150, 180, 220)))
        painter.drawRoundedRect(int(panel_x), int(panel_y), int(panel_w), int(panel_h), 2, 2)
        
        painter.setPen(QPen(QColor(50, 50, 50), 0.5))
        painter.setBrush(QBrush(QColor(130, 160, 200)))
        painter.drawRect(int(panel_x + 5), int(panel_y + 3), int(panel_w - 20), int(panel_h - 6))
        
        led_y = panel_y + 5
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 12), int(led_y), 3, 3)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 20), int(led_y), 3, 3)
        
        font = QFont("微软雅黑", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        text_x = int(self._width) + 5
        text_y = int(self._height) + 2
        painter.drawText(text_x, text_y, self.node_id)
    
    def _draw_home_router_icon(self, painter):
        panel_w = 150
        panel_h = 30
        
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(220, 220, 230)))
        painter.drawRoundedRect(int(panel_x), int(panel_y), panel_w, panel_h, 3, 3)
        
        painter.setPen(QPen(QColor(50, 50, 50), 0.5))
        painter.setBrush(QBrush(QColor(200, 200, 210)))
        painter.drawRect(int(panel_x + 5), int(panel_y + 5), panel_w - 10, panel_h - 10)
        
        led_y = panel_y + 7
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 12), int(led_y), 3, 3)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 20), int(led_y), 3, 3)
        
        wifi_x = panel_x + panel_w - 30
        wifi_y = led_y + 5
        painter.setPen(QPen(QColor(100, 200, 100), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(wifi_x), int(wifi_y), 8, 5, 0, 180 * 16)
        painter.drawArc(int(wifi_x + 2), int(wifi_y + 2), 4, 3, 0, 180 * 16)
        painter.setBrush(QBrush(QColor(100, 200, 100)))
        painter.drawEllipse(int(wifi_x + 3), int(wifi_y + 5), 2, 2)
    
    def _draw_switch_icon(self, painter):
        panel_w = PANEL_WIDTH_PX - 10
        panel_h = U_HEIGHT_PX * self.u_size - 4
        
        panel_x = 5
        panel_y = 2
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawRoundedRect(int(panel_x), int(panel_y), panel_w, panel_h, 2, 2)
        
        painter.setPen(QPen(QColor(50, 50, 50), 0.5))
        painter.setBrush(QBrush(QColor(180, 180, 180)))
        painter.drawRect(int(panel_x + 3), int(panel_y + 3), panel_w - 6, panel_h - 6)
        
        led_y = panel_y + 5
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 10), int(led_y), 3, 3)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 18), int(led_y), 3, 3)
        
        font = QFont("微软雅黑", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        text_x = int(self._width) + 5
        text_y = int(self._height) + 2
        painter.drawText(text_x, text_y, self.node_id)
    
    def _draw_modem_icon(self, painter):
        panel_w = 180
        panel_h = 30
        
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawRoundedRect(int(panel_x), int(panel_y), panel_w, panel_h, 2, 2)
        
        painter.setPen(QPen(QColor(50, 50, 50), 0.5))
        painter.setBrush(QBrush(QColor(220, 220, 220)))
        painter.drawRect(int(panel_x + 3), int(panel_y + 3), panel_w - 6, panel_h - 6)
        
        led_y = panel_y + 5
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 12), int(led_y), 4, 4)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 20), int(led_y), 4, 4)
    
    def _draw_nas_icon(self, painter):
        panel_w = 150
        panel_h = 55
        
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.drawRoundedRect(int(panel_x), int(panel_y), panel_w, panel_h, 3, 3)
        
        painter.setPen(QPen(QColor(50, 50, 50), 0.5))
        painter.setBrush(QBrush(QColor(40, 40, 40)))
        painter.drawRect(int(panel_x + 3), int(panel_y + 3), panel_w - 6, panel_h - 6)
        
        bay_w = 32
        bay_h = 7
        bay_gap = 3
        bay_x = panel_x + 8
        bay_start_y = panel_y + 8
        
        for i in range(4):
            bay_y = bay_start_y + i * (bay_h + bay_gap)
            painter.setPen(QPen(QColor(80, 80, 80), 0.5))
            painter.setBrush(QBrush(QColor(30, 30, 30)))
            painter.drawRect(int(bay_x), int(bay_y), bay_w, bay_h)
            
            painter.setPen(QPen(QColor(100, 100, 100), 0.5))
            painter.drawLine(int(bay_x + 2), int(bay_y + bay_h // 2), int(bay_x + bay_w - 2), int(bay_y + bay_h // 2))
        

        led_x = panel_x + panel_w - 22
        led_y = panel_y + 8
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(int(led_x), int(led_y), 3, 3)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(int(led_x + 6), int(led_y), 3, 3)
        painter.setBrush(QBrush(QColor(0, 150, 200)))
        painter.drawEllipse(int(led_x + 12), int(led_y), 3, 3)
    
    def _draw_ac_icon(self, painter):
        # 无线控制器使用路由器样式
        panel_w = self._width - 10
        panel_h = self._height - 4
        panel_x = 5
        panel_y = 2
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(200, 180, 220)))  # 浅紫色
        painter.drawRoundedRect(int(panel_x), int(panel_y), int(panel_w), int(panel_h), 2, 2)
        
        painter.setPen(QPen(QColor(50, 50, 50), 0.5))
        painter.setBrush(QBrush(QColor(180, 160, 200)))
        painter.drawRect(int(panel_x + 5), int(panel_y + 3), int(panel_w - 20), int(panel_h - 6))
        
        # 绘制指示灯
        led_y = panel_y + 5
        painter.setBrush(QBrush(QColor(0, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 12), int(led_y), 3, 3)
        painter.setBrush(QBrush(QColor(200, 200, 0)))
        painter.drawEllipse(int(panel_x + panel_w - 20), int(led_y), 3, 3)
        
        # 绘制设备名称（右下角外部）
        font = QFont("微软雅黑", 10)
        painter.setFont(font)
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        text_x = int(self._width) + 5
        text_y = int(self._height) + 2
        painter.drawText(text_x, text_y, self.node_id)
    
    def _draw_ap_icon(self, painter):
        panel_w = 70
        panel_h = 70
        
        panel_x = (self._width - panel_w) // 2
        panel_y = 5
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(240, 240, 240)))
        painter.drawEllipse(int(panel_x), int(panel_y), panel_w, panel_h)
        
        painter.setPen(QPen(QColor(200, 200, 200), 0.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(int(panel_x + 8), int(panel_y + 8), panel_w - 16, panel_h - 16)
        
        painter.setPen(QPen(QColor(100, 200, 100), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        cx = panel_x + panel_w // 2
        cy = panel_y + panel_h // 2
        
        painter.drawArc(int(cx - 20), int(cy - 12), 40, 24, 0, 180 * 16)
        painter.drawArc(int(cx - 14), int(cy - 8), 28, 18, 0, 180 * 16)
        painter.drawArc(int(cx - 8), int(cy - 4), 16, 10, 0, 180 * 16)
        
        painter.setBrush(QBrush(QColor(100, 200, 100)))
        painter.drawEllipse(int(cx - 2), int(cy + 4), 4, 4)
    
    def _draw_isp_icon(self, painter):
        cloud_w = 100
        cloud_h = 60
        
        cloud_x = (self._width - cloud_w) // 2
        cloud_y = 10
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(200, 220, 255)))
        
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        
        path.moveTo(cloud_x + 20, cloud_y + cloud_h)
        path.cubicTo(cloud_x - 10, cloud_y + cloud_h,
                     cloud_x - 10, cloud_y + 20,
                     cloud_x + 15, cloud_y + 20)
        path.cubicTo(cloud_x + 10, cloud_y,
                     cloud_x + 30, cloud_y - 5,
                     cloud_x + 45, cloud_y + 10)
        path.cubicTo(cloud_x + 50, cloud_y,
                     cloud_x + 80, cloud_y,
                     cloud_x + 85, cloud_y + 25)
        path.cubicTo(cloud_x + cloud_w + 10, cloud_y + 25,
                     cloud_x + cloud_w + 10, cloud_y + cloud_h,
                     cloud_x + 80, cloud_y + cloud_h)
        path.closeSubpath()
        
        painter.drawPath(path)
        
        painter.setPen(QPen(QColor(50, 50, 150), 2))
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        text_x = cloud_x + cloud_w // 2 - 12
        text_y = cloud_y + cloud_h // 2 + 5
        painter.drawText(int(text_x), int(text_y), "ISP")
    
    def _draw_isp_dual_icon(self, painter):
        cloud_w = 140
        cloud_h = 60
        
        cloud_x = (self._width - cloud_w) // 2
        cloud_y = 10
        
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(QBrush(QColor(200, 220, 255)))
        
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        
        path.moveTo(cloud_x + 20, cloud_y + cloud_h)
        path.cubicTo(cloud_x - 10, cloud_y + cloud_h,
                     cloud_x - 10, cloud_y + 20,
                     cloud_x + 15, cloud_y + 20)
        path.cubicTo(cloud_x + 10, cloud_y,
                     cloud_x + 30, cloud_y - 5,
                     cloud_x + 45, cloud_y + 10)
        path.cubicTo(cloud_x + 50, cloud_y,
                     cloud_x + cloud_w - 20, cloud_y,
                     cloud_x + cloud_w - 15, cloud_y + 25)
        path.cubicTo(cloud_x + cloud_w + 10, cloud_y + 25,
                     cloud_x + cloud_w + 10, cloud_y + cloud_h,
                     cloud_x + cloud_w - 20, cloud_y + cloud_h)
        path.closeSubpath()
        
        painter.drawPath(path)
        
        painter.setPen(QPen(QColor(50, 50, 150), 2))
        font = QFont("Arial", 8, QFont.Weight.Bold)
        painter.setFont(font)
        text_x = cloud_x + cloud_w // 2 - 12
        text_y = cloud_y + cloud_h // 2 + 5
        painter.drawText(int(text_x), int(text_y), "ISP")

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.prepareGeometryChange()
            self._update_connections()
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, 'contextMenuEvent'):
            scene.contextMenuEvent(event)
        else:
            super().contextMenuEvent(event)

    def _update_connections(self):
        scene = self.scene()
        if scene:
            for conn in scene.get_all_connections():
                if conn.source_port.parentItem() == self or conn.target_port.parentItem() == self:
                    conn.update_path()

    def get_port_by_id(self, port_id: str):
        return self._port_map.get(port_id)

    def get_data(self):
        data = {
            "id": self.node_id,
            "device_type": self.device_type,
            "port_config": self.port_config,
            "template_id": self.template_id,
            "vendor": self.vendor,
            "renderer_key": self.renderer_key,
            "label_config": self.label_config,
            "u_size": self.u_size,
            "x": self.pos().x(),
            "y": self.pos().y(),
            "is_racked": self._is_racked
        }
        if self._is_racked:
            data["rack_name"] = self._rack_name
            data["rack_start_u"] = self._rack_start_u
        return data
