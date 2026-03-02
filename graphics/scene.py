from PySide6.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsItem, QMenu, QInputDialog, QMessageBox
from PySide6.QtCore import Qt, QTimer, QPoint, QPointF
from PySide6.QtGui import QPen, QColor, QTransform
from .node_item import NodeItem
from .connection_item import ConnectionItem, CableTagItem, CableAnchorPoint
from .port_item import PortItem


class TopologyScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.temp_line = None
        self.source_port = None
        self._connections = []
        self._connection_mode = True
        self._tags_enabled = False
        self._tags_fixed = False
        self._context_menu_callback = None
        self._last_selected_node = None
        self._last_mouse_pos = None
        
        from PySide6.QtGui import QBrush, QColor
        self.setBackgroundBrush(QBrush(QColor(255, 255, 255)))

    def set_connection_mode(self, enabled):
        self._connection_mode = enabled
        if not enabled:
            self._clear_selection()

    def is_connection_mode(self):
        return self._connection_mode
    
    def set_tags_enabled(self, enabled):
        self._tags_enabled = enabled
        for conn in self._connections:
            conn.set_tags_enabled(enabled)
    
    def set_tags_fixed(self, fixed):
        self._tags_fixed = fixed
        for conn in self._connections:
            conn.set_tags_fixed(fixed)

    def _clear_selection(self):
        if self.source_port:
            self.source_port.stop_flash()
            self.source_port = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = event.scenePos()
            items_at_pos = self.items(scene_pos)
            
            node_item = self._find_node_at_position(items_at_pos)
            
            if node_item and not self._connection_mode:
                self._last_selected_node = node_item
                self._last_mouse_pos = scene_pos
            
            self.clearSelection()
            if node_item:
                node_item.setSelected(True)
        
        super().mousePressEvent(event)
    
    def _find_node_at_position(self, items):
        for item in items:
            if isinstance(item, NodeItem):
                return item
            if isinstance(item, PortItem):
                parent = item.parentItem()
                if isinstance(parent, NodeItem):
                    return parent
        return None
    
    def _find_connection_at_position(self, items):
        for item in items:
            if isinstance(item, ConnectionItem):
                return item
            if isinstance(item, (CableTagItem, CableAnchorPoint)):
                if hasattr(item, '_connection'):
                    return item._connection
                if hasattr(item, '_tag_item') and hasattr(item._tag_item, '_connection'):
                    return item._tag_item._connection
        return None

    def contextMenuEvent(self, event):
        scene_pos = event.scenePos()
        
        items_at_pos = self.items(scene_pos)
        
        node_item = self._find_node_at_position(items_at_pos)
        
        if self._connection_mode:
            port_item = None
            for item in items_at_pos:
                if isinstance(item, PortItem):
                    port_item = item
                    break
            
            if port_item:
                if port_item.is_connected():
                    super().contextMenuEvent(event)
                    return
                
                if not self.source_port:
                    self.source_port = port_item
                    port_item.start_flash()
                else:
                    if port_item == self.source_port:
                        self.source_port.stop_flash()
                        self.source_port = None
                    else:
                        self._create_connection(port_item)
                event.accept()
                return
            else:
                if node_item:
                    self.clearSelection()
                    node_item.setSelected(True)
                    self._show_node_context_menu(node_item, event.screenPos(), scene_pos)
                    event.accept()
                else:
                    super().contextMenuEvent(event)
        else:
            if node_item:
                self.clearSelection()
                node_item.setSelected(True)
                self._last_selected_node = node_item
                self._show_node_context_menu(node_item, event.screenPos(), scene_pos)
                event.accept()
            else:
                connection = self._find_connection_at_position(items_at_pos)
                if connection:
                    source_node = connection.source_port.parentItem()
                    
                    if source_node:
                        self.clearSelection()
                        source_node.setSelected(True)
                        self._last_selected_node = source_node
                        self._show_node_context_menu(source_node, event.screenPos(), scene_pos)
                        event.accept()
                    else:
                        super().contextMenuEvent(event)
                else:
                    super().contextMenuEvent(event)
    
    def _show_node_context_menu(self, node, screen_pos, scene_pos):
        menu = QMenu()
        
        rename_action = menu.addAction("自定义设备名称")
        edit_device_action = menu.addAction("编辑设备")
        view_tags_action = menu.addAction("查看设备线缆标签")
        
        menu.addSeparator()
        
        if node.is_fixed():
            fix_action = menu.addAction("解除固定设备不动")
        else:
            fix_action = menu.addAction("固定设备不动")
        
        menu.addSeparator()
        
        rack_menu_actions = {}
        
        if self._context_menu_callback:
            rack_info = self._context_menu_callback("get_rack_info", node.node_id, node)
            if rack_info:
                has_racks, rack_list, can_add_to_rack, is_racked = rack_info
                
                if is_racked:
                    rack_submenu = menu.addMenu("移动U位")
                    for rack_name, available_positions in rack_list:
                        for pos in available_positions:
                            action = rack_submenu.addAction(f"U{pos:02d}")
                            rack_menu_actions[action] = ('move', rack_name, pos)
                else:
                    if can_add_to_rack and has_racks:
                        rack_submenu = menu.addMenu("添加到机架")
                        for rack_name, available_positions in rack_list:
                            for pos in available_positions:
                                action = rack_submenu.addAction(f"U{pos:02d}")
                                rack_menu_actions[action] = ('add', rack_name, pos)
        
        action = menu.exec(screen_pos)
        
        if action == rename_action:
            self._rename_node(node)
        elif action == edit_device_action:
            self._config_ports(node)
        elif action == view_tags_action:
            self._show_node_cable_tags(node)
        elif action == fix_action:
            self._toggle_node_fixed(node)
        elif action in rack_menu_actions:
            mode, rack_name, pos = rack_menu_actions[action]
            if mode == 'move':
                self._move_device_to_u_position(node, rack_name, pos)
            else:
                self._add_device_to_u_position(node, rack_name, pos)
    
    def _add_device_to_u_position(self, node, rack_name, selected_u):
        if self._context_menu_callback:
            self._context_menu_callback("add_to_rack_position", node.node_id, {
                "node": node, 
                "rack_name": rack_name, 
                "start_u": selected_u
            })
    
    def _move_device_to_u_position(self, node, rack_name, selected_u):
        rack_info = node.get_rack_info()
        current_u = rack_info.get("start_u", "未知") if rack_info else "未知"
        
        if selected_u == current_u:
            return
        
        if self._context_menu_callback:
            self._context_menu_callback("move_rack_position", node.node_id, {
                "node": node, 
                "rack_name": rack_name, 
                "start_u": selected_u
            })
    
    def _rename_node(self, node):
        from dialogs import DeviceNameDialog
        
        dialog = DeviceNameDialog(None, node.get_data())
        if dialog.exec():
            config = dialog.get_config()
            if not config["id"]:
                QMessageBox.warning(None, "错误", "设备名称不能为空")
                return
            
            existing_ids = [n.node_id for n in self.get_all_nodes() if n != node]
            if config["id"] in existing_ids:
                QMessageBox.warning(None, "错误", "设备名称已存在，请使用其他名称")
                return
            
            node.node_id = config["id"]
            node.label_config = config.get("label_config", node.label_config)
            node.update()
            
            for conn in self._connections:
                if conn.source_port.parentItem() == node or conn.target_port.parentItem() == node:
                    conn._update_tag_texts()
    
    def _config_ports(self, node):
        from dialogs import DeviceConfigDialog
        
        dialog = DeviceConfigDialog(None, node.get_data())
        if dialog.exec():
            config = dialog.get_config()
            if not config["id"]:
                QMessageBox.warning(None, "错误", "设备名称不能为空")
                return
            
            existing_ids = [n.node_id for n in self.get_all_nodes() if n != node]
            if config["id"] in existing_ids:
                QMessageBox.warning(None, "错误", "设备名称已存在，请使用其他名称")
                return
            
            for port in node.ports:
                if port.scene():
                    self.removeItem(port)
            
            node.node_id = config["id"]
            node.device_type = config["device_type"]
            node.port_config = config["port_config"]
            node.u_size = config.get("u_size", 1)
            node.ports = []
            node._port_map = {}
            node.prepareGeometryChange()
            node._width = node._calculate_width()
            node._height = node._calculate_height()
            node._create_ports()
            node.update()
    
    def _show_node_cable_tags(self, node):
        related_connections = []
        for conn in self._connections:
            if conn.source_port.parentItem() == node or conn.target_port.parentItem() == node:
                related_connections.append(conn)
        
        if not related_connections:
            QMessageBox.information(None, "提示", f"设备 {node.node_id} 没有任何线缆连接")
            return
        
        if self._context_menu_callback:
            self._context_menu_callback("show_cable_tags", node.node_id, related_connections)
    
    def _toggle_node_fixed(self, node):
        current_state = node.is_fixed()
        node.set_fixed(not current_state)
    
    def _add_node_to_rack(self, node):
        if self._context_menu_callback:
            self._context_menu_callback("add_to_rack", node.node_id, node)
    
    def set_context_menu_callback(self, callback):
        self._context_menu_callback = callback

    def _create_connection(self, target_port):
        if not self.source_port or not target_port:
            return
        
        if self.source_port.is_connected():
            self.source_port.stop_flash()
            self.source_port = None
            return
        
        if target_port.is_connected():
            self.source_port.stop_flash()
            self.source_port = None
            return
        
        source_node = self.source_port.parentItem()
        target_node = target_port.parentItem()
        
        if source_node == target_node:
            self.source_port.stop_flash()
            self.source_port = None
            return
        
        from graphics.port_item import PORT_TYPE_FIBER
        source_is_sc = self.source_port.port_type == PORT_TYPE_FIBER
        target_is_sc = target_port.port_type == PORT_TYPE_FIBER
        
        if source_is_sc != target_is_sc:
            QMessageBox.warning(None, "连接错误", "SC光纤端口只能与SC光纤端口相连")
            self.source_port.stop_flash()
            self.source_port = None
            return
        
        target_port.start_flash()
        
        QTimer.singleShot(500, lambda: self._finalize_connection(target_port))

    def _finalize_connection(self, target_port):
        if not self.source_port or not target_port:
            return
        
        if self.source_port.is_connected() or target_port.is_connected():
            self.source_port.stop_flash()
            target_port.stop_flash()
            self.source_port = None
            return
        
        source_node = self.source_port.parentItem()
        target_node = target_port.parentItem()
        if source_node == target_node:
            self.source_port.stop_flash()
            target_port.stop_flash()
            self.source_port = None
            return
        
        self.source_port.stop_flash()
        target_port.stop_flash()
        
        connection = ConnectionItem(self.source_port, target_port)
        self.addItem(connection)
        connection.add_tags_to_scene(self)
        self._connections.append(connection)
        
        connection.set_tags_enabled(self._tags_enabled)
        connection.set_tags_fixed(self._tags_fixed)
        
        self.source_port = None

    def get_all_nodes(self):
        return [item for item in self.items() if isinstance(item, NodeItem)]

    def get_all_connections(self):
        return self._connections

    def get_node_by_id(self, node_id: str):
        for node in self.get_all_nodes():
            if node.node_id == node_id:
                return node
        return None

    def remove_connection(self, connection):
        if connection in self._connections:
            connection.remove_tags_from_scene(self)
            connection.disconnect()
            self._connections.remove(connection)
            self.removeItem(connection)
    
    def remove_node(self, node):
        connections_to_remove = []
        for conn in self._connections:
            if conn.source_port.parentItem() == node or conn.target_port.parentItem() == node:
                connections_to_remove.append(conn)
        
        for conn in connections_to_remove:
            self.remove_connection(conn)
        
        self.removeItem(node)
    
    def remove_all_connections(self):
        connections_copy = self._connections.copy()
        for conn in connections_copy:
            self.remove_connection(conn)
        self._connections.clear()
