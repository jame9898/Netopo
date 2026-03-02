from PySide6.QtWidgets import QGraphicsScene, QGraphicsRectItem, QGraphicsSimpleTextItem
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPen, QBrush, QFont, QColor
from .rack_device import RACK_TOTAL_U, RACK_WIDTH_PX, U_HEIGHT_PX, RackDevice
from .u_slot import USlot


class RackScene(QGraphicsScene):
    def __init__(self):
        super().__init__()
        self._racks = []
        self._rack_counter = 0
        self.setSceneRect(0, 0, 800, 900)

    def add_rack(self, name=None):
        if name is None:
            self._rack_counter += 1
            name = f"Rack{self._rack_counter:02d}"
        
        rack = RackItem(name)
        x_offset = len(self._racks) * (RACK_WIDTH_PX + 80) + 50
        rack.setPos(x_offset, 30)
        self.addItem(rack)
        self._racks.append(rack)
        
        total_width = (len(self._racks) + 1) * (RACK_WIDTH_PX + 80)
        self.setSceneRect(0, 0, total_width, RACK_TOTAL_U * U_HEIGHT_PX + 100)
        
        return rack

    def get_all_devices(self):
        devices = []
        for rack in self._racks:
            devices.extend(rack.get_devices())
        return devices

    def get_available_u_positions(self, required_height: int):
        if not self._racks:
            return []
        return self._racks[0].get_available_u_positions(required_height)

    def add_device(self, device):
        if self._racks:
            self._racks[0].add_device(device)

    def remove_device(self, device):
        for rack in self._racks:
            if rack.has_device(device):
                rack.remove_device(device)
                break

    def get_rack_count(self):
        return len(self._racks)


class RackItem(QGraphicsRectItem):
    def __init__(self, rack_name, parent=None):
        label_width = 35
        rack_height = RACK_TOTAL_U * U_HEIGHT_PX
        super().__init__(0, 0, label_width + RACK_WIDTH_PX + label_width, rack_height + 40, parent)
        
        self.rack_name = rack_name
        self._u_slots = {}  # U位槽位字典：{u_number: USlot}
        self._devices = {}  # 设备字典：{device_id: RackDevice}
        
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(Qt.BrushStyle.NoBrush)
        
        self._setup_rack()
        print(f"机架 {rack_name} 创建完成，共 {len(self._u_slots)} 个U位槽位")

    def _setup_rack(self):
        label_width = 35
        rack_height = RACK_TOTAL_U * U_HEIGHT_PX
        
        title = QGraphicsSimpleTextItem(self.rack_name, self)
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setBrush(QColor(255, 200, 0))
        title.setPos((label_width + RACK_WIDTH_PX + label_width - title.boundingRect().width()) / 2, 5)
        
        rack_rect = QGraphicsRectItem(label_width, 25, RACK_WIDTH_PX, rack_height, self)
        rack_rect.setPen(QPen(QColor(80, 80, 80), 3))
        rack_rect.setBrush(Qt.BrushStyle.NoBrush)
        rack_rect.setZValue(0)
        
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        
        for u in range(RACK_TOTAL_U):
            u_number = u + 1
            y = 25 + (RACK_TOTAL_U - 1 - u) * U_HEIGHT_PX
            
            slot = USlot(u_number, self)
            slot.setPos(label_width + 10, y)
            self._u_slots[u_number] = slot
            
            label_left = QGraphicsSimpleTextItem(f"U{u_number}", self)
            label_left.setFont(font)
            label_left.setBrush(QColor(255, 200, 0))
            label_left.setPos(2, y + 3)
            
            label_right = QGraphicsSimpleTextItem(f"U{u_number}", self)
            label_right.setFont(font)
            label_right.setBrush(QColor(255, 200, 0))
            label_right.setPos(label_width + RACK_WIDTH_PX + 5, y + 3)

    def get_slot(self, u_number: int):
        return self._u_slots.get(u_number)

    def add_device(self, device_id: str, device_type: str, start_u: int, u_height: int = 1):
        print(f"尝试上架设备: {device_id}, 类型: {device_type}, U位: {start_u}, 高度: {u_height}")
        
        required_slots = list(range(start_u, start_u + u_height))
        
        for u in required_slots:
            slot = self.get_slot(u)
            if not slot:
                print(f"错误：U{u} 不存在！")
                return False
            if slot.is_occupied():
                print(f"错误：U{u} 已被设备 {slot.get_device_id()} 占用！")
                return False
        
        device_colors = {
            "switch": QColor(100, 150, 200),
            "router": QColor(150, 180, 220),
            "server": QColor(200, 180, 160),
            "ac": QColor(180, 200, 150),
            "ap": QColor(200, 150, 180)
        }
        device_color = device_colors.get(device_type, QColor(120, 120, 120))
        
        for u in required_slots:
            slot = self.get_slot(u)
            slot.occupy(device_id, device_type, device_color)
        
        label_width = 35
        y = 25 + (RACK_TOTAL_U - start_u - u_height + 1) * U_HEIGHT_PX
        device = RackDevice(device_id, device_type, u_height, start_u, self)
        device.setPos(label_width + 10, y)
        self._devices[device_id] = device
        
        print(f"设备 {device_id} 成功上架到 U{start_u}")
        
        self.update()
        scene = self.scene()
        if scene:
            scene.update()
            scene.update(scene.sceneRect())
        
        return True

    def remove_device(self, device_id: str):
        for u, slot in self._u_slots.items():
            if slot.get_device_id() == device_id:
                slot.release()
        
        if device_id in self._devices:
            device = self._devices[device_id]
            self.scene().removeItem(device)
            del self._devices[device_id]
        
        print(f"设备 {device_id} 已从机架移除")

    def get_devices(self):
        devices = {}
        for u, slot in self._u_slots.items():
            if slot.is_occupied():
                device_id = slot.get_device_id()
                if device_id not in devices:
                    devices[device_id] = {"id": device_id, "start_u": u}
        return list(devices.values())

    def has_device(self, device_id: str):
        for slot in self._u_slots.values():
            if slot.get_device_id() == device_id:
                return True
        return False

    def get_device_at_u(self, u_position: int):
        slot = self.get_slot(u_position)
        if slot and slot.is_occupied():
            return slot.get_device_id()
        return None

    def get_available_u_positions(self, required_height: int = 1):
        available = []
        sorted_u = sorted(self._u_slots.keys())
        
        for i in range(len(sorted_u) - required_height + 1):
            is_available = True
            start_u = sorted_u[i]
            
            for j in range(required_height):
                u = start_u + j
                slot = self.get_slot(u)
                if not slot or slot.is_occupied():
                    is_available = False
                    break
            
            if is_available:
                available.append(start_u)
        
        return available
    
    def get_move_positions(self, device_id: str, u_height: int, current_start_u: int):
        move_positions = []
        sorted_u = sorted(self._u_slots.keys())
        
        for i in range(len(sorted_u) - u_height + 1):
            start_u = sorted_u[i]
            
            if start_u == current_start_u:
                continue
            
            is_available = True
            for j in range(u_height):
                u = start_u + j
                slot = self.get_slot(u)
                if not slot:
                    is_available = False
                    break
                if slot.is_occupied() and slot.get_device_id() != device_id:
                    is_available = False
                    break
            
            if is_available:
                move_positions.append(start_u)
        
        return move_positions
    
    def get_available_u_count(self):
        return sum(1 for slot in self._u_slots.values() if not slot.is_occupied())
