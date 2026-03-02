from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QSpinBox, QComboBox, QPushButton,
                                QGroupBox, QGridLayout, QDialogButtonBox)
from PySide6.QtCore import Qt
from rack import U_HEIGHT_OPTIONS, RACK_TOTAL_U

DEVICE_TYPES = {
    "switch": "Switch (1U)",
    "router": "Router (1U)",
    "server": "Server (2U/4U/6U/8U)"
}


class RackDeviceDialog(QDialog):
    def __init__(self, parent=None, device_data=None, available_positions=None):
        super().__init__(parent)
        self.setWindowTitle("Rack Device Config")
        self.setMinimumWidth(300)
        self.device_data = device_data or {}
        self.available_positions = available_positions or list(range(1, RACK_TOTAL_U + 1))
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        info_group = QGroupBox("Device Info")
        info_layout = QGridLayout(info_group)
        
        info_layout.addWidget(QLabel("Device Name:"), 0, 0)
        self.name_edit = QLineEdit()
        info_layout.addWidget(self.name_edit, 0, 1)
        
        info_layout.addWidget(QLabel("Device Type:"), 1, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Switch", "Router", "Server"])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        info_layout.addWidget(self.type_combo, 1, 1)
        
        layout.addWidget(info_group)
        
        size_group = QGroupBox("Size & Position")
        size_layout = QGridLayout(size_group)
        
        size_layout.addWidget(QLabel("U Height:"), 0, 0)
        self.height_combo = QComboBox()
        self.height_combo.addItems([f"{u}U" for u in U_HEIGHT_OPTIONS])
        size_layout.addWidget(self.height_combo, 0, 1)
        
        size_layout.addWidget(QLabel("Start U:"), 1, 0)
        self.start_u_spin = QSpinBox()
        self.start_u_spin.setRange(1, RACK_TOTAL_U)
        size_layout.addWidget(self.start_u_spin, 1, 1)
        
        layout.addWidget(size_group)
        
        self.pos_label = QLabel("Available positions will be shown here")
        self.pos_label.setWordWrap(True)
        layout.addWidget(self.pos_label)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self._update_available_positions()

    def _on_type_changed(self, index):
        if index == 2:
            self.height_combo.setEnabled(True)
            self.height_combo.setCurrentIndex(1)
        else:
            self.height_combo.setCurrentIndex(0)
            self.height_combo.setEnabled(False)
        self._update_available_positions()

    def _update_available_positions(self):
        u_height = U_HEIGHT_OPTIONS[self.height_combo.currentIndex()]
        available = []
        for start_u in range(1, RACK_TOTAL_U - u_height + 2):
            if start_u in self.available_positions or start_u == self.device_data.get("start_u"):
                available.append(start_u)
        
        if available:
            self.pos_label.setText(f"Available positions: {', '.join(map(str, available[:10]))}...")
            self.start_u_spin.setRange(min(available), max(available))
        else:
            self.pos_label.setText("No available positions for this size")
        
        self._available = available

    def _load_data(self):
        if "id" in self.device_data:
            self.name_edit.setText(self.device_data["id"])
        
        device_type = self.device_data.get("device_type", "switch")
        type_index = {"switch": 0, "router": 1, "server": 2}.get(device_type, 0)
        self.type_combo.setCurrentIndex(type_index)
        
        u_height = self.device_data.get("u_height", 1)
        if u_height in U_HEIGHT_OPTIONS:
            self.height_combo.setCurrentIndex(U_HEIGHT_OPTIONS.index(u_height))
        
        start_u = self.device_data.get("start_u", 1)
        self.start_u_spin.setValue(start_u)

    def get_config(self):
        type_map = {0: "switch", 1: "router", 2: "server"}
        return {
            "id": self.name_edit.text(),
            "device_type": type_map[self.type_combo.currentIndex()],
            "u_height": U_HEIGHT_OPTIONS[self.height_combo.currentIndex()],
            "start_u": self.start_u_spin.value()
        }
