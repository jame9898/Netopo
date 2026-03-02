from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QTreeWidget, QTreeWidgetItem, 
                                QPushButton, QGroupBox, QGridLayout, 
                                QDialogButtonBox, QSplitter, QFrame)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from templates import (DEVICE_TEMPLATES, VENDOR_COLORS, VENDOR_NAMES, DEVICE_TYPE_NAMES,
                       VENDOR_CISCO, VENDOR_HUAWEI, VENDOR_H3C, VENDOR_DELL,
                       VENDOR_NVIDIA, VENDOR_LENONO, VENDOR_GENERIC)


class TemplateSelectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Device Template Selection")
        self.setMinimumSize(700, 500)
        self.selected_template = None
        self._setup_ui()
        self._load_templates()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(QLabel("Templates:"))
        self.template_tree = QTreeWidget()
        self.template_tree.setHeaderLabels(["Device", "Type"])
        self.template_tree.itemClicked.connect(self._on_template_selected)
        left_layout.addWidget(self.template_tree)
        splitter.addWidget(left_frame)
        
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(QLabel("Details:"))
        self.detail_group = QGroupBox("Template Info")
        detail_grid = QGridLayout(self.detail_group)
        
        detail_grid.addWidget(QLabel("Name:"), 0, 0)
        self.name_label = QLabel("-")
        detail_grid.addWidget(self.name_label, 0, 1)
        
        detail_grid.addWidget(QLabel("Vendor:"), 1, 0)
        self.vendor_label = QLabel("-")
        detail_grid.addWidget(self.vendor_label, 1, 1)
        
        detail_grid.addWidget(QLabel("Type:"), 2, 0)
        self.type_label = QLabel("-")
        detail_grid.addWidget(self.type_label, 2, 1)
        
        detail_grid.addWidget(QLabel("Description:"), 3, 0)
        self.desc_label = QLabel("-")
        self.desc_label.setWordWrap(True)
        detail_grid.addWidget(self.desc_label, 3, 1)
        
        detail_grid.addWidget(QLabel("U Height:"), 4, 0)
        self.uheight_label = QLabel("-")
        detail_grid.addWidget(self.uheight_label, 4, 1)
        
        detail_grid.addWidget(QLabel("Total Ports:"), 5, 0)
        self.total_ports_label = QLabel("-")
        detail_grid.addWidget(self.total_ports_label, 5, 1)
        
        detail_grid.addWidget(QLabel("Port Types:"), 6, 0)
        self.port_types_label = QLabel("-")
        detail_grid.addWidget(self.port_types_label, 6, 1)
        
        right_layout.addWidget(self.detail_group)
        right_layout.addStretch()
        splitter.addWidget(right_frame)
        
        splitter.setSizes([300, 400])
        layout.addWidget(splitter)
        
        btn_layout = QHBoxLayout()
        self.custom_btn = QPushButton("Custom Device...")
        self.custom_btn.clicked.connect(self._on_custom_device)
        btn_layout.addWidget(self.custom_btn)
        btn_layout.addStretch()
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        btn_layout.addWidget(buttons)
        layout.addLayout(btn_layout)

    def _load_templates(self):
        vendors = {}
        for template_id, template in DEVICE_TEMPLATES.items():
            vendor = template["vendor"]
            if vendor not in vendors:
                vendor_item = QTreeWidgetItem([VENDOR_NAMES.get(vendor, vendor), ""])
                vendor_item.setData(0, Qt.ItemDataRole.UserRole, None)
                self.template_tree.addTopLevelItem(vendor_item)
                vendors[vendor] = vendor_item
            else:
                vendor_item = vendors[vendor]
            
            device_item = QTreeWidgetItem([template["name"], DEVICE_TYPE_NAMES.get(template["device_type"], template["device_type"])])
            device_item.setData(0, Qt.ItemDataRole.UserRole, template_id)
            color = VENDOR_COLORS.get(vendor, QColor(128, 128, 128))
            device_item.setForeground(0, color)
            vendor_item.addChild(device_item)
        
        self.template_tree.expandAll()

    def _on_template_selected(self, item, column):
        template_id = item.data(0, Qt.ItemDataRole.UserRole)
        if template_id and template_id in DEVICE_TEMPLATES:
            self.selected_template = template_id
            template = DEVICE_TEMPLATES[template_id]
            
            self.name_label.setText(template["name"])
            self.vendor_label.setText(VENDOR_NAMES.get(template["vendor"], template["vendor"]))
            self.type_label.setText(DEVICE_TYPE_NAMES.get(template["device_type"], template["device_type"]))
            self.desc_label.setText(template.get("description", "-"))
            self.uheight_label.setText(f"{template.get('u_height', 1)}U")
            
            total_ports = 0
            port_types = set()
            
            if "ports" in template:
                total_ports = len(template["ports"])
                for port in template["ports"]:
                    port_types.add(port.get("type", "ethernet"))
            elif "port_config" in template:
                left_ports = len(template["port_config"].get("left", []))
                right_ports = len(template["port_config"].get("right", []))
                total_ports = left_ports + right_ports
                
                for port in template["port_config"].get("left", []):
                    port_types.add(port.get("type", "ethernet"))
                for port in template["port_config"].get("right", []):
                    port_types.add(port.get("type", "ethernet"))
            
            self.total_ports_label.setText(str(total_ports))
            port_types_str = ", ".join(sorted(port_types)) if port_types else "-"
            self.port_types_label.setText(port_types_str)

    def _on_custom_device(self):
        self.selected_template = None
        self.done(2)

    def _on_accept(self):
        if self.selected_template:
            self.accept()
        else:
            self.reject()

    def get_selected_template(self):
        return self.selected_template
