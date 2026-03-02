from PySide6.QtGui import QColor
from graphics.node_item import PANEL_WIDTH_PX, U_HEIGHT_PX

DEVICE_SPECS = {
    "pc": {
        "name": "PC",
        "name_cn": "个人计算机",
        "width": 86,
        "height": 68,
        "ports": [
            {"id": "GE0/0/1", "type": "ethernet", "speed": "1G"}
        ],
        "port_configurable": True,
        "max_ports": 2,
        "description": "个人计算机，默认1个网络接口（可配置）",
        "visual": {
            "host": {"width": 25, "height": 55},
            "monitor": {"width": 40, "height": 28},
            "keyboard": {"width": 30, "height": 6},
            "mouse": {"width": 6, "height": 10}
        }
    },
    "phone": {
        "name": "Mobile Phone",
        "name_cn": "手机",
        "width": 35,
        "height": 62,
        "ports": [],
        "wifi_only": True,
        "description": "移动终端，仅WiFi连接",
        "visual": {
            "body": {"width": 30, "height": 60},
            "screen": {"width": 26, "height": 50}
        }
    },
    "home_router": {
        "name": "Home Router",
        "name_cn": "家用路由器",
        "width": 164,
        "height": 40,
        "ports": [
            {"id": "GE0/0/1", "type": "ethernet", "speed": "1G"},
            {"id": "GE0/0/2", "type": "ethernet", "speed": "1G"},
            {"id": "GE0/0/3", "type": "ethernet", "speed": "1G"},
            {"id": "GE0/0/4", "type": "ethernet", "speed": "1G"}
        ],
        "description": "家用路由器，默认4个GE端口",
        "visual": {
            "panel": {"width": 150, "height": 30}
        }
    },
    "modem": {
        "name": "Optical Modem",
        "name_cn": "光猫",
        "width": 190,
        "height": 40,
        "ports": [
            {"id": "SC-IN", "type": "fiber_sc", "speed": "1G"},
            {"id": "GE0/0/1", "type": "ethernet", "speed": "2.5G"},
            {"id": "GE0/0/2", "type": "ethernet", "speed": "2.5G"},
            {"id": "GE0/0/3", "type": "ethernet", "speed": "2.5G"},
            {"id": "GE0/0/4", "type": "ethernet", "speed": "2.5G"}
        ],
        "description": "光猫，SC光纤输入+4个2.5G电口",
        "visual": {
            "panel": {"width": 180, "height": 30}
        }
    },
    "nas": {
        "name": "NAS",
        "name_cn": "网络存储",
        "width": 164,
        "height": 68,
        "ports": [
            {"id": "GE0/0/1", "type": "ethernet", "speed": "1G"},
            {"id": "GE0/0/2", "type": "ethernet", "speed": "1G"}
        ],
        "port_options": ["1G", "2.5G", "10G_Fiber"],
        "description": "NAS存储，默认2个GE端口，可选2.5G或10G光口",
        "visual": {
            "panel": {"width": 160, "height": 60},
            "drive_bays": 4
        }
    },
    "ac": {
        "name": "AC",
        "name_cn": "无线控制器",
        "width": PANEL_WIDTH_PX,
        "height": U_HEIGHT_PX,
        "ports": [
            {"id": f"GE0/0/{i}", "type": "ethernet", "speed": "1G"} for i in range(1, 17)
        ],
        "description": "无线控制器，16口（上8下8）",
        "visual": {
            "panel": {"width": PANEL_WIDTH_PX - 10, "height": U_HEIGHT_PX - 4}
        }
    },
    "ap": {
        "name": "AP",
        "name_cn": "无线接入点",
        "width": 86,
        "height": 92,
        "ports": [
            {"id": "GE0/0/1", "type": "ethernet", "speed": "1G", "poe": True}
        ],
        "description": "无线接入点，单POE接口",
        "visual": {
            "panel": {"width": 80, "height": 80}
        }
    },
    "isp": {
        "name": "ISP",
        "name_cn": "运营商网络(单接口)",
        "width": 120,
        "height": 80,
        "ports": [
            {"id": "FIBER-OUT", "type": "fiber_sc", "speed": "10G"}
        ],
        "description": "ISP外部网络边界，云形状+单光纤连接",
        "visual": {
            "cloud": {"width": 100, "height": 60}
        }
    },
    "isp_dual": {
        "name": "ISP Dual",
        "name_cn": "运营商网络 (双接口)",
        "width": 160,
        "height": 80,
        "ports": [
            {"id": "FIBER-OUT1", "type": "fiber_sc", "speed": "10G"},
            {"id": "FIBER-OUT2", "type": "fiber_sc", "speed": "10G"}
        ],
        "description": "ISP 外部网络边界，云形状 + 双光纤连接",
        "visual": {
            "cloud": {"width": 140, "height": 60}
        }
    },
    "server": {
        "name": "Server",
        "name_cn": "服务器",
        "width": PANEL_WIDTH_PX,
        "height": U_HEIGHT_PX,
        "ports": [
            {"id": "GE0/0/1", "type": "ethernet", "speed": "1G"},
            {"id": "GE0/0/2", "type": "ethernet", "speed": "1G"}
        ],
        "port_configurable": True,
        "max_ports": 4,
        "description": "服务器，默认 2 个 GE 端口（可配置）",
        "rack_mountable": True,
        "u_height": 1,
        "visual": {
            "panel": {"width": PANEL_WIDTH_PX - 20, "height": U_HEIGHT_PX - 4}
        }
    }
}

PORT_TYPE_COLORS = {
    "ethernet": QColor(0, 150, 0),
    "fiber_sc": QColor(0, 180, 200),
    "fiber_lc": QColor(0, 200, 220),
    "wifi": QColor(150, 100, 200)
}

PORT_SPEED_COLORS = {
    "100M": QColor(200, 200, 0),
    "1G": QColor(0, 200, 0),
    "2.5G": QColor(0, 200, 100),
    "10G": QColor(0, 200, 200),
    "10G_Fiber": QColor(100, 200, 255)
}
