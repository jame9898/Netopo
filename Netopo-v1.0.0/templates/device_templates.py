from PySide6.QtGui import QColor

VENDOR_CISCO = "cisco"
VENDOR_HUAWEI = "huawei"
VENDOR_H3C = "h3c"
VENDOR_DELL = "dell"
VENDOR_NVIDIA = "nvidia"
VENDOR_LENONO = "lenovo"
VENDOR_GENERIC = "generic"

DEVICE_SWITCH = "switch"
DEVICE_ROUTER = "router"
DEVICE_FIREWALL = "firewall"
DEVICE_SERVER = "server"

VENDOR_COLORS = {
    VENDOR_CISCO: QColor(0, 100, 180),
    VENDOR_HUAWEI: QColor(200, 50, 50),
    VENDOR_H3C: QColor(0, 150, 100),
    VENDOR_DELL: QColor(0, 100, 150),
    VENDOR_NVIDIA: QColor(118, 185, 0),
    VENDOR_LENONO: QColor(200, 50, 50),
    VENDOR_GENERIC: QColor(128, 128, 128),
}

DEVICE_TEMPLATES = {
    "huawei_s5735_l24t4x": {
        "vendor": VENDOR_HUAWEI,
        "device_type": DEVICE_SWITCH,
        "name": "Huawei S5735-L24T4X-A1",
        "description": "24x GE RJ45 + 4x 10GE SFP+ Switch",
        "renderer_key": "huawei_s5735_l24t4x",
        "panel_width": 442,
        "panel_height": 43.6,
        "u_height": 1,
        "ports": [
            {"id": f"GE0/0/{i}", "type": "ethernet"} for i in range(1, 25)
        ] + [
            {"id": f"XG0/0/{i}", "type": "fiber"} for i in range(1, 5)
        ],
    },
    "generic_switch_8port": {
        "vendor": VENDOR_GENERIC,
        "device_type": DEVICE_SWITCH,
        "name": "Generic 8-Port Switch",
        "description": "8-port Ethernet Switch",
        "panel_width": 200,
        "panel_height": 44,
        "u_height": 1,
        "ports": [
            {"id": f"P{i}", "type": "ethernet"} for i in range(1, 9)
        ],
    },
    "generic_router_4port": {
        "vendor": VENDOR_GENERIC,
        "device_type": DEVICE_ROUTER,
        "name": "Generic 4-Port Router",
        "description": "4-port Router",
        "panel_width": 200,
        "panel_height": 44,
        "u_height": 1,
        "ports": [
            {"id": f"GE0/{i}", "type": "ethernet"} for i in range(4)
        ],
    },
}

VENDOR_NAMES = {
    VENDOR_CISCO: "Cisco",
    VENDOR_HUAWEI: "Huawei",
    VENDOR_H3C: "H3C",
    VENDOR_DELL: "Dell",
    VENDOR_NVIDIA: "NVIDIA",
    VENDOR_LENONO: "Lenovo",
    VENDOR_GENERIC: "Generic",
}

DEVICE_TYPE_NAMES = {
    DEVICE_SWITCH: "Switch",
    DEVICE_ROUTER: "Router",
    DEVICE_FIREWALL: "Firewall",
    DEVICE_SERVER: "Server",
}


def get_templates_by_vendor(vendor: str):
    return {k: v for k, v in DEVICE_TEMPLATES.items() if v["vendor"] == vendor}


def get_templates_by_type(device_type: str):
    return {k: v for k, v in DEVICE_TEMPLATES.items() if v["device_type"] == device_type}
