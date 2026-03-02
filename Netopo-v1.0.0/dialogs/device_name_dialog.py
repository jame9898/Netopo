from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QSpinBox, QComboBox, QPushButton,
                                QGroupBox, QGridLayout, QDialogButtonBox, QFrame,
                                QColorDialog, QWidget)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

TEXT_POSITIONS = [
    ("bottom_right", "右下角"),
    ("bottom_left", "左下角"),
    ("top_right", "右上角"),
    ("top_left", "左上角"),
    ("center", "中心"),
    ("custom", "自定义位置"),
]


class DeviceNameDialog(QDialog):
    def __init__(self, parent=None, device_data=None):
        super().__init__(parent)
        self.setWindowTitle("设备名称设置")
        self.setMinimumWidth(400)
        self.device_data = device_data or {}
        self._setup_ui()
        self._load_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        name_group = QGroupBox("设备名称")
        name_layout = QHBoxLayout(name_group)
        name_layout.addWidget(QLabel("名称:"))
        self.name_edit = QLineEdit()
        name_layout.addWidget(self.name_edit)
        main_layout.addWidget(name_group)
        
        label_group = QGroupBox("标签显示设置")
        label_layout = QGridLayout(label_group)
        
        label_layout.addWidget(QLabel("文字颜色:"), 0, 0)
        color_layout = QHBoxLayout()
        self.color_preview = QFrame()
        self.color_preview.setFixedSize(30, 20)
        self.color_preview.setStyleSheet("background-color: #323232; border: 1px solid #666;")
        self.text_color = "#323232"
        color_layout.addWidget(self.color_preview)
        self.color_btn = QPushButton("选择颜色")
        self.color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(self.color_btn)
        color_layout.addStretch()
        label_layout.addLayout(color_layout, 0, 1)
        
        label_layout.addWidget(QLabel("字号大小:"), 1, 0)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(4, 24)
        self.font_size_spin.setValue(4)
        label_layout.addWidget(self.font_size_spin, 1, 1)
        
        label_layout.addWidget(QLabel("标签位置:"), 2, 0)
        self.position_combo = QComboBox()
        for pos_key, pos_name in TEXT_POSITIONS:
            self.position_combo.addItem(pos_name, pos_key)
        self.position_combo.currentIndexChanged.connect(self._on_position_changed)
        label_layout.addWidget(self.position_combo, 2, 1)
        
        self.custom_pos_widget = QWidget()
        custom_pos_layout = QHBoxLayout(self.custom_pos_widget)
        custom_pos_layout.setContentsMargins(0, 0, 0, 0)
        custom_pos_layout.addWidget(QLabel("X偏移:"))
        self.custom_x_spin = QSpinBox()
        self.custom_x_spin.setRange(-200, 200)
        self.custom_x_spin.setValue(0)
        custom_pos_layout.addWidget(self.custom_x_spin)
        custom_pos_layout.addWidget(QLabel("Y偏移:"))
        self.custom_y_spin = QSpinBox()
        self.custom_y_spin.setRange(-200, 200)
        self.custom_y_spin.setValue(0)
        custom_pos_layout.addWidget(self.custom_y_spin)
        custom_pos_layout.addStretch()
        self.custom_pos_widget.setVisible(False)
        label_layout.addWidget(self.custom_pos_widget, 3, 0, 1, 2)
        
        main_layout.addWidget(label_group)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)
    
    def _choose_color(self):
        color = QColorDialog.getColor(QColor(self.text_color), self, "选择文字颜色")
        if color.isValid():
            self.text_color = color.name()
            self.color_preview.setStyleSheet(f"background-color: {self.text_color}; border: 1px solid #666;")
    
    def _on_position_changed(self, index):
        pos_key = self.position_combo.currentData()
        self.custom_pos_widget.setVisible(pos_key == "custom")
    
    def _load_data(self):
        if "id" in self.device_data:
            self.name_edit.setText(self.device_data["id"])
        
        if "label_config" in self.device_data:
            label_config = self.device_data["label_config"]
            if "text_color" in label_config:
                self.text_color = label_config["text_color"]
                self.color_preview.setStyleSheet(f"background-color: {self.text_color}; border: 1px solid #666;")
            if "font_size" in label_config:
                self.font_size_spin.setValue(label_config["font_size"])
            if "position" in label_config:
                for i, (pos_key, _) in enumerate(TEXT_POSITIONS):
                    if pos_key == label_config["position"]:
                        self.position_combo.setCurrentIndex(i)
                        break
            if "custom_x" in label_config:
                self.custom_x_spin.setValue(label_config["custom_x"])
            if "custom_y" in label_config:
                self.custom_y_spin.setValue(label_config["custom_y"])

    def get_config(self):
        return {
            "id": self.name_edit.text(),
            "label_config": {
                "text_color": self.text_color,
                "font_size": self.font_size_spin.value(),
                "font_family": "微软雅黑",
                "position": self.position_combo.currentData(),
                "custom_x": self.custom_x_spin.value(),
                "custom_y": self.custom_y_spin.value()
            }
        }
