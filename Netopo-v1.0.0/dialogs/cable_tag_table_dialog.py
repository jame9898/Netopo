from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableView, 
                                QPushButton, QLineEdit, QLabel, QHeaderView,
                                QAbstractItemView)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PySide6.QtGui import QColor


class CableTagTableModel(QAbstractTableModel):
    def __init__(self, data=None, parent=None):
        super().__init__(parent)
        self._data = data or []
        self._headers = ["源设备端口", "目的设备端口", "源IP地址", "目的IP地址"]
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()
        
        if row >= len(self._data):
            return None
        
        if role == Qt.ItemDataRole.DisplayRole:
            item = self._data[row]
            if col == 0:
                return item.get("source_port", "")
            elif col == 1:
                return item.get("target_port", "")
            elif col == 2:
                return item.get("source_ip", "")
            elif col == 3:
                return item.get("target_ip", "")
        
        return None
    
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self._headers[section]
        return None
    
    def set_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()


class CableTagTableDialog(QDialog):
    def __init__(self, device_name: str, connections: list, parent=None):
        super().__init__(parent)
        self._device_name = device_name
        self._connections = connections
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        self.setWindowTitle(f"设备线缆标签 - {self._device_name}")
        self.setMinimumSize(700, 400)
        self.resize(800, 500)
        
        layout = QVBoxLayout(self)
        
        search_layout = QHBoxLayout()
        search_label = QLabel("搜索:")
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("输入关键字筛选...")
        self._search_input.textChanged.connect(self._apply_filter)
        search_layout.addWidget(search_label)
        search_layout.addWidget(self._search_input)
        layout.addLayout(search_layout)
        
        self._table_view = QTableView()
        self._table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)
        
        self._model = CableTagTableModel()
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._proxy_model.setFilterKeyColumn(-1)
        
        self._table_view.setModel(self._proxy_model)
        
        header = self._table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self._table_view)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_data(self):
        table_data = []
        
        sorted_connections = sorted(self._connections, key=lambda conn: self._get_source_port_number(conn))
        
        for conn in sorted_connections:
            conn_data = conn.get_data()
            
            source_node = conn.source_port.parentItem()
            target_node = conn.target_port.parentItem()
            
            source_device = source_node.node_id if source_node else "?"
            target_device = target_node.node_id if target_node else "?"
            source_port = conn_data.get('source_port', '?')
            target_port = conn_data.get('target_port', '?')
            
            source_port_display = f"{source_device} {source_port}"
            target_port_display = f"{target_device} {target_port}"
            
            table_data.append({
                "source_port": source_port_display,
                "target_port": target_port_display,
                "source_ip": conn_data.get("source_ip", "-"),
                "target_ip": conn_data.get("target_ip", "-")
            })
        
        self._model.set_data(table_data)
    
    def _get_source_port_number(self, conn):
        try:
            port_id = conn.source_port.port_id
            if port_id.startswith("GE0/0/"):
                return int(port_id.replace("GE0/0/", ""))
            elif port_id.startswith("XG0/0/"):
                return int(port_id.replace("XG0/0/", "")) + 100
            elif port_id.startswith("CON"):
                return int(port_id.replace("CON", "")) + 200
            elif port_id.startswith("USB"):
                return int(port_id.replace("USB", "")) + 300
            else:
                return 999
        except:
            return 999
    
    def _apply_filter(self, text):
        self._proxy_model.setFilterFixedString(text)
