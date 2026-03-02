import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                                QMenuBar, QToolBar, QFileDialog, QMessageBox,
                                QInputDialog, QMenu, QTabWidget, QWidget)
from PySide6.QtGui import QPainter, QAction, QIcon
from PySide6.QtCore import Qt
from graphics import TopologyScene, NodeItem, DEVICE_SWITCH, DEVICE_ROUTER, DEVICE_SERVER, ConnectionItem
from graphics.node_item import (DEVICE_PC, DEVICE_PHONE, DEVICE_HOME_ROUTER, 
                                 DEVICE_MODEM, DEVICE_NAS, DEVICE_AC, DEVICE_AP, 
                                 DEVICE_ISP, DEVICE_ISP_DUAL, DEVICE_SERVER)
from file_io import FileHandler
from dialogs import DeviceConfigDialog, RackDeviceDialog, TemplateSelectionDialog, CableTagTableDialog
from rack import RackScene, U_HEIGHT_OPTIONS
from templates import DEVICE_TEMPLATES

FILTER_TOPO = "Topology Files (*.topo)"
FILTER_PDF = "PDF Files (*.pdf)"
FILTER_ALL = "All Files (*.*)"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("拓扑编辑器")
        self.setGeometry(100, 100, 1200, 800)
        self._create_tab_widget()
        self._create_menu()
        self._create_toolbar()
        self.file_handler = FileHandler(self.topology_scene)
        self.current_file = None
        # self._add_sample_topology()
        # self._add_sample_rack()
        
        self.topology_scene.set_context_menu_callback(self._handle_context_menu_action)

    def _create_tab_widget(self):
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)
        
        self.topology_scene = TopologyScene(self)
        self.topology_view = QGraphicsView(self.topology_scene)
        self.topology_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.topology_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.tab_widget.addTab(self.topology_view, "拓扑界面")
        
        self.rack_scene = RackScene()
        self.rack_view = QGraphicsView(self.rack_scene)
        self.rack_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.rack_view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.tab_widget.addTab(self.rack_view, "机架界面")
    
    def _handle_context_menu_action(self, action, device_name, data):
        if action == "show_cable_tags":
            dialog = CableTagTableDialog(device_name, data, self)
            dialog.exec()
        elif action == "get_rack_info":
            return self._get_rack_info(data)
        elif action == "add_to_rack_position":
            self._add_device_to_rack_position(device_name, data)
        elif action == "move_rack_position":
            self._move_device_rack_position(device_name, data)

    def _get_rack_info(self, node):
        HOME_DEVICES = [DEVICE_MODEM, DEVICE_HOME_ROUTER, DEVICE_PC, DEVICE_PHONE, DEVICE_NAS]
        
        device_type = node.device_type if hasattr(node, 'device_type') else None
        can_add_to_rack = device_type not in HOME_DEVICES
        u_size = getattr(node, 'u_size', 1)
        
        is_racked = node.is_racked()
        
        print(f"获取机架信息 - 设备: {node.node_id}, 类型: {device_type}, U数: {u_size}, 可上架: {can_add_to_rack}, 已上架: {is_racked}")
        print(f"当前机架数量: {len(self.rack_scene._racks)}")
        
        rack_list = []
        for rack in self.rack_scene._racks:
            if is_racked:
                rack_info = node.get_rack_info()
                current_u = rack_info["start_u"] if rack_info else None
                move_positions = rack.get_move_positions(node.node_id, u_size, current_u)
                rack_list.append((rack.rack_name, move_positions))
            else:
                available_positions = rack.get_available_u_positions(u_size)
                rack_list.append((rack.rack_name, available_positions))
        
        has_racks = len(self.rack_scene._racks) > 0
        
        return (has_racks, rack_list, can_add_to_rack, is_racked)

    def _add_device_to_rack_position(self, device_name, data):
        node = data["node"]
        rack_name = data["rack_name"]
        start_u = data["start_u"]
        
        rack = None
        for r in self.rack_scene._racks:
            if r.rack_name == rack_name:
                rack = r
                break
        
        if not rack:
            QMessageBox.warning(self, "错误", f"找不到机架：{rack_name}")
            return
        
        u_height = getattr(node, 'u_size', 1)
        
        required_slots = list(range(start_u, start_u + u_height))
        for u in required_slots:
            slot = rack.get_slot(u)
            if not slot:
                QMessageBox.warning(self, "错误", f"U{u:02d} 不存在！")
                return
            if slot.is_occupied():
                occupied_by = slot.get_device_id()
                QMessageBox.warning(self, "U 位已被占用", 
                    f"U{u:02d} 已被设备 {occupied_by} 占用！\n请选择其他 U 位。")
                return
        
        device_type = node.device_type if hasattr(node, 'device_type') else "switch"
        if device_type == "isp" or device_type == "isp_dual":
            device_type = "router"
        elif device_type not in ["switch", "router", "server", "ac", "ap"]:
            device_type = "switch"
        
        print(f"准备上架设备：{device_name}, 类型：{device_type}, U 位：{start_u}, 高度：{u_height}U")
        
        success = rack.add_device(device_name, device_type, start_u, u_height)
        
        if not success:
            QMessageBox.warning(self, "上架失败", f"无法将设备 {device_name} 上架到 U{start_u:02d}，该位置可能已被占用。")
            return
        
        node.set_racked(True, rack_name, start_u)
        
        self.rack_scene.update()
        self.rack_view.viewport().update()
        self.rack_view.repaint()
        
        # 切换到机架界面
        self.tab_widget.setCurrentIndex(1)
        
        if u_height == 1:
            position_text = f"U{start_u:02d}"
        else:
            position_text = f"U{start_u:02d}-U{start_u + u_height - 1:02d}"
        QMessageBox.information(self, "成功", f"设备 {device_name} 已上架到 {rack_name} 的 {position_text} 位置")

    def _move_device_rack_position(self, device_name, data):
        node = data["node"]
        rack_name = data["rack_name"]
        new_start_u = data["start_u"]
        
        rack_info = node.get_rack_info()
        if not rack_info:
            QMessageBox.warning(self, "错误", "设备未上架")
            return
        
        old_rack_name = rack_info["rack_name"]
        old_start_u = rack_info["start_u"]
        
        if old_rack_name != rack_name:
            QMessageBox.warning(self, "错误", "只能在同一机架内移动设备")
            return
        
        if old_start_u == new_start_u:
            return
        
        rack = None
        for r in self.rack_scene._racks:
            if r.rack_name == rack_name:
                rack = r
                break
        
        if not rack:
            QMessageBox.warning(self, "错误", f"找不到机架：{rack_name}")
            return
        
        u_height = getattr(node, 'u_size', 1)
        
        rack.remove_device(device_name)
        
        required_slots = list(range(new_start_u, new_start_u + u_height))
        for u in required_slots:
            slot = rack.get_slot(u)
            if not slot:
                rack.add_device(device_name, node.device_type, old_start_u, u_height)
                QMessageBox.warning(self, "错误", f"U{u:02d} 不存在！")
                return
            if slot.is_occupied():
                rack.add_device(device_name, node.device_type, old_start_u, u_height)
                QMessageBox.warning(self, "U 位已被占用", 
                    f"U{u:02d} 已被设备 {slot.get_device_id()} 占用！\n请选择其他 U 位。")
                return
        
        device_type = node.device_type if hasattr(node, 'device_type') else "switch"
        if device_type == "isp" or device_type == "isp_dual":
            device_type = "router"
        elif device_type not in ["switch", "router", "server", "ac", "ap"]:
            device_type = "switch"
        
        success = rack.add_device(device_name, device_type, new_start_u, u_height)
        
        if not success:
            rack.add_device(device_name, device_type, old_start_u, u_height)
            QMessageBox.warning(self, "移动失败", f"无法将设备 {device_name} 移动到 U{new_start_u:02d}")
            return
        
        node.set_racked(True, rack_name, new_start_u)
        
        self.rack_scene.update()
        self.rack_view.viewport().update()
        self.rack_view.repaint()
        
        self.tab_widget.setCurrentIndex(1)
        
        if u_height == 1:
            position_text = f"U{new_start_u:02d}"
        else:
            position_text = f"U{new_start_u:02d}-U{new_start_u + u_height - 1:02d}"
        QMessageBox.information(self, "成功", f"设备 {device_name} 已移动到 {rack_name} 的 {position_text} 位置")

    def _create_menu(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("新建", self.new_file)
        file_menu.addAction("打开...", self.open_file)
        file_menu.addAction("保存", self.save_file)
        file_menu.addAction("另存为...", self.save_file_as)
        file_menu.addSeparator()
        file_menu.addAction("导出为PDF...", self.export_pdf)
        file_menu.addSeparator()
        file_menu.addAction("退出", self.close)
        


    def _create_toolbar(self):
        toolbar = QToolBar("工具栏")
        self.addToolBar(toolbar)
        
        quick_add_menu = QMenu("快速添加", self)
        
        quick_add_menu.addAction("添加机架（47U）", self.add_rack)
        
        quick_add_menu.addSeparator()
        
        isp_menu = quick_add_menu.addMenu("运营商网络")
        isp_menu.addAction("单逻辑接口 ISP", lambda: self.add_topology_device(DEVICE_ISP))
        isp_menu.addAction("双逻辑接口 ISP", lambda: self.add_topology_device(DEVICE_ISP_DUAL))
        
        quick_add_menu.addSeparator()
        
        layer3_menu = quick_add_menu.addMenu("添加三层设备")
        layer3_menu.addAction("路由器", lambda: self.add_topology_device(DEVICE_ROUTER))
        layer3_menu.addAction("光猫", lambda: self.add_topology_device(DEVICE_MODEM))
        
        layer2_menu = quick_add_menu.addMenu("添加二层设备")
        layer2_menu.addAction("交换机", lambda: self.add_topology_device(DEVICE_SWITCH))
        layer2_menu.addAction("无线控制器", lambda: self.add_topology_device(DEVICE_AC))
        layer2_menu.addAction("无线接入点", lambda: self.add_topology_device(DEVICE_AP))
        layer2_menu.addAction("家用路由器", lambda: self.add_topology_device(DEVICE_HOME_ROUTER))
        
        terminal_menu = quick_add_menu.addMenu("添加终端设备")
        terminal_menu.addAction("个人计算机", lambda: self.add_topology_device(DEVICE_PC))
        terminal_menu.addAction("手机", lambda: self.add_topology_device(DEVICE_PHONE))
        terminal_menu.addAction("网络存储", lambda: self.add_topology_device(DEVICE_NAS))
        terminal_menu.addAction("服务器", lambda: self.add_topology_device(DEVICE_SERVER))
        
        quick_add_btn = toolbar.addAction("快速添加")
        quick_add_btn.setMenu(quick_add_menu)
        
        toolbar.addAction("自定义设备添加...", self.add_custom_topology_device)
        
        connection_menu = QMenu("线缆连接", self)
        
        self.connection_action = QAction("连接 ON", self)
        self.connection_action.setCheckable(True)
        self.connection_action.setChecked(True)
        self.connection_action.triggered.connect(self.toggle_connection_mode)
        connection_menu.addAction(self.connection_action)
        
        self.tag_visibility_action = QAction("标签显示 OFF", self)
        self.tag_visibility_action.setCheckable(True)
        self.tag_visibility_action.setChecked(False)
        self.tag_visibility_action.triggered.connect(self.toggle_tag_visibility)
        connection_menu.addAction(self.tag_visibility_action)
        
        self.tag_freeze_action = QAction("标签冻结 OFF", self)
        self.tag_freeze_action.setCheckable(True)
        self.tag_freeze_action.setChecked(False)
        self.tag_freeze_action.triggered.connect(self.toggle_tag_freeze)
        connection_menu.addAction(self.tag_freeze_action)
        
        connection_btn = toolbar.addAction("线缆连接")
        connection_btn.setMenu(connection_menu)
        
        delete_menu = QMenu("删除", self)
        delete_menu.addAction("删除选中", self.delete_selected)
        delete_menu.addSeparator()
        remove_all_cables_action = QAction("拆除所有线缆", self)
        remove_all_cables_action.triggered.connect(self.remove_all_connections)
        delete_menu.addAction(remove_all_cables_action)
        remove_all_devices_action = QAction("删除所有设备", self)
        remove_all_devices_action.triggered.connect(self.remove_all_devices)
        delete_menu.addAction(remove_all_devices_action)
        delete_btn = toolbar.addAction("删除")
        delete_btn.setMenu(delete_menu)
        
        zoom_menu = QMenu("缩放", self)
        zoom_menu.addAction("放大", self.zoom_in)
        zoom_menu.addAction("缩小", self.zoom_out)
        zoom_menu.addAction("重置缩放", self.zoom_reset)
        zoom_btn = toolbar.addAction("缩放")
        zoom_btn.setMenu(zoom_menu)

    def _add_sample_topology(self):
        node1 = NodeItem("SW-Core1", DEVICE_SWITCH, x=100, y=150, vendor="cisco")
        node2 = NodeItem("R-Edge1", DEVICE_ROUTER, x=350, y=150, vendor="huawei")
        self.topology_scene.addItem(node1)
        self.topology_scene.addItem(node2)

    def _add_sample_rack(self):
        dev1 = RackDevice("SW-Core1", "switch", 1, 1)
        dev2 = RackDevice("R-Edge1", "router", 1, 3)
        dev3 = RackDevice("SRV-Web1", "server", 2, 5)
        self.rack_scene.add_device(dev1)
        self.rack_scene.add_device(dev2)
        self.rack_scene.add_device(dev3)

    def add_rack(self):
        rack = self.rack_scene.add_rack()
        self.tab_widget.setCurrentIndex(1)
        QMessageBox.information(self, "成功", f"已添加机架: {rack.rack_name}")

    def toggle_connection_mode(self, checked):
        if checked:
            self.connection_action.setText("连接 ON")
            self.topology_scene.set_connection_mode(True)
        else:
            self.connection_action.setText("连接 OFF")
            self.topology_scene.set_connection_mode(False)

    def toggle_tag_visibility(self, checked):
        if checked:
            self.tag_visibility_action.setText("标签显示 ON")
        else:
            self.tag_visibility_action.setText("标签显示 OFF")
        
        self.topology_scene.set_tags_enabled(checked)

    def toggle_tag_freeze(self, checked):
        if checked:
            self.tag_freeze_action.setText("标签冻结 ON")
        else:
            self.tag_freeze_action.setText("标签冻结 OFF")
        
        self.topology_scene.set_tags_fixed(checked)

    def new_file(self):
        self._clear_topology()
        self._clear_rack()
        self.current_file = None
        self.setWindowTitle("拓扑编辑器 - 新建文件")

    def open_file(self):
        filter_str = FILTER_TOPO + ";;" + FILTER_ALL
        filepath, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", filter_str)
        if filepath:
            if self.file_handler.load(filepath):
                self.current_file = filepath
                self.setWindowTitle(f"拓扑编辑器 - {filepath}")

    def save_file(self):
        if self.current_file:
            self.file_handler.save(self.current_file)
        else:
            self.save_file_as()

    def save_file_as(self):
        filter_str = FILTER_TOPO + ";;" + FILTER_ALL
        filepath, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "untitled.topo", filter_str)
        if filepath:
            if not filepath.endswith('.topo'):
                filepath += '.topo'
            print(f"尝试保存文件到: {filepath}")
            try:
                if self.file_handler.save(filepath):
                    self.current_file = filepath
                    self.setWindowTitle(f"拓扑编辑器 - {filepath}")
                    QMessageBox.information(self, "保存成功", f"文件已保存到：{filepath}")
            except Exception as e:
                QMessageBox.warning(self, "保存失败", f"无法保存文件：{str(e)}")

    def export_pdf(self):
        from PySide6.QtPrintSupport import QPrinter, QPrintDialog
        from PySide6.QtGui import QPainter
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出PDF", "", FILTER_PDF)
        
        if not filepath:
            return
        
        if not filepath.endswith('.pdf'):
            filepath += '.pdf'
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        printer.setPageSize(QPrinter.PageSize.A4)
        printer.setPageOrientation(QPrinter.PageOrientation.Landscape)
        
        painter = QPainter(printer)
        if not painter.isActive():
            QMessageBox.warning(self, "导出失败", "无法创建PDF文件")
            return
        
        page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
        page_width = page_rect.width()
        page_height = page_rect.height()
        
        title_font = painter.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(int(page_width * 0.4), 50, "网络拓扑图")
        
        topo_scene_rect = self.topology_scene.sceneRect()
        if topo_scene_rect.width() > 0 and topo_scene_rect.height() > 0:
            scale_x = (page_width - 100) / topo_scene_rect.width()
            scale_y = (page_height - 150) / topo_scene_rect.height()
            scale = min(scale_x, scale_y)
            
            painter.save()
            painter.translate(50, 70)
            painter.scale(scale, scale)
            self.topology_scene.render(painter, target=None, source=topo_scene_rect)
            painter.restore()
        
        printer.newPage()
        
        painter.setFont(title_font)
        painter.drawText(int(page_width * 0.4), 50, "机架布局")
        
        rack_scene_rect = self.rack_scene.sceneRect()
        if rack_scene_rect.width() > 0 and rack_scene_rect.height() > 0:
            scale_x = (page_width - 100) / rack_scene_rect.width()
            scale_y = (page_height - 150) / rack_scene_rect.height()
            scale = min(scale_x, scale_y)
            
            painter.save()
            painter.translate(50, 70)
            painter.scale(scale, scale)
            self.rack_scene.render(painter, target=None, source=rack_scene_rect)
            painter.restore()
        
        printer.newPage()
        
        painter.setFont(title_font)
        painter.drawText(50, 50, "设备清单")
        
        normal_font = painter.font()
        normal_font.setPointSize(10)
        normal_font.setBold(False)
        painter.setFont(normal_font)
        
        y_pos = 80
        line_height = 25
        
        painter.drawText(50, y_pos, "设备名称")
        painter.drawText(200, y_pos, "设备类型")
        painter.drawText(350, y_pos, "端口数量")
        painter.drawText(500, y_pos, "位置")
        y_pos += line_height
        
        painter.drawLine(50, y_pos - 5, page_width - 50, y_pos - 5)
        
        for node in self.topology_scene.get_all_nodes():
            if y_pos > page_height - 100:
                printer.newPage()
                y_pos = 50
            
            painter.drawText(50, y_pos, node.node_id)
            painter.drawText(200, y_pos, node.device_type or "未知")
            port_count = len(node._ports) if hasattr(node, '_ports') else 0
            painter.drawText(350, y_pos, str(port_count))
            
            rack_info = node.get_rack_info() if hasattr(node, 'get_rack_info') else None
            if rack_info:
                painter.drawText(500, y_pos, f"{rack_info.get('rack_name', '')} U{rack_info.get('start_u', '')}")
            else:
                painter.drawText(500, y_pos, "未上架")
            
            y_pos += line_height
        
        painter.end()
        QMessageBox.information(self, "导出成功", f"PDF已保存到：{filepath}")

    def add_from_template(self):
        dialog = TemplateSelectionDialog(self)
        result = dialog.exec()
        
        if result == 1:
            template_id = dialog.get_selected_template()
            if template_id and template_id in DEVICE_TEMPLATES:
                template = DEVICE_TEMPLATES[template_id]
                existing_ids = [n.node_id for n in self.topology_scene.get_all_nodes()]
                base_name = template["name"].replace(" ", "_")[:10]
                counter = 1
                device_name = f"{base_name}_{counter}"
                while device_name in existing_ids:
                    counter += 1
                    device_name = f"{base_name}_{counter}"
                
                node = NodeItem(
                    device_name,
                    template["device_type"],
                    {"ports": template.get("ports", [])},
                    x=200, y=200,
                    template_id=template_id,
                    vendor=template["vendor"],
                    renderer_key=template.get("renderer_key")
                )
                self.topology_scene.addItem(node)
        elif result == 2:
            self.add_custom_topology_device()

    def add_topology_device(self, device_type):
        from config.device_specs import DEVICE_SPECS
        
        device_spec = DEVICE_SPECS.get(device_type, {})
        device_name_cn = device_spec.get("name_cn", device_type)
        
        if device_type == DEVICE_PC:
            default_name = "PC"
        elif device_type == DEVICE_PHONE:
            default_name = "Phone"
        elif device_type == DEVICE_HOME_ROUTER:
            default_name = "HomeRouter"
        elif device_type == DEVICE_MODEM:
            default_name = "Modem"
        elif device_type == DEVICE_NAS:
            default_name = "NAS"
        elif device_type == DEVICE_AC:
            default_name = "AC"
        elif device_type == DEVICE_AP:
            default_name = "AP"
        elif device_type == DEVICE_ISP:
            default_name = "ISP"
        elif device_type == DEVICE_ISP_DUAL:
            default_name = "ISP-Dual"
        elif device_type == DEVICE_SWITCH:
            default_name = "SW"
        elif device_type == DEVICE_ROUTER:
            default_name = "R"
        elif device_type == DEVICE_SERVER:
            default_name = "Server "
        else:
            default_name = "DEV"
        
        existing_ids = [n.node_id for n in self.topology_scene.get_all_nodes()]
        counter = 1
        while f"{default_name}{counter}" in existing_ids:
            counter += 1
        name = f"{default_name}{counter}"
        
        port_config = {"ports": device_spec.get("ports", [])} if device_spec else None
        
        node = NodeItem(name, device_type, port_config, x=200, y=200)
        self.topology_scene.addItem(node)

    def add_custom_topology_device(self):
        dialog = DeviceConfigDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            if not config["id"]:
                QMessageBox.warning(self, "Error", "Device name cannot be empty")
                return
            
            device_count = config.get("device_count", 1)
            device_type = config["device_type"]
            port_config = config["port_config"]
            
            existing_ids = [n.node_id for n in self.topology_scene.get_all_nodes()]
            
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
            prefix = prefix_map.get(device_type, "DEV")
            
            start_x = 200
            start_y = 200
            offset_x = 250
            offset_y = 150
            cols = 4
            
            added_count = 0
            for i in range(device_count):
                counter = 1
                while f"{prefix}{counter}" in existing_ids:
                    counter += 1
                
                name = f"{prefix}{counter}"
                existing_ids.append(name)
                
                row = added_count // cols
                col = added_count % cols
                x = start_x + col * offset_x
                y = start_y + row * offset_y
                
                node = NodeItem(name, device_type, port_config, x=x, y=y,
                               label_config=config.get("label_config"),
                               u_size=config.get("u_size", 1))
                self.topology_scene.addItem(node)
                added_count += 1

    def add_rack_device(self, device_type, u_height):
        default_name = {"switch": "SW", "router": "R", "server": "SRV"}.get(device_type, "DEV")
        existing_ids = [d.device_id for d in self.rack_scene.get_all_devices()]
        counter = 1
        while f"{default_name}{counter}" in existing_ids:
            counter += 1
        name = f"{default_name}{counter}"
        
        available = self.rack_scene.get_available_u_positions(u_height)
        if not available:
            QMessageBox.warning(self, "Error", f"No available position for {u_height}U device")
            return
        
        device = RackDevice(name, device_type, u_height, available[0])
        self.rack_scene.add_device(device)

    def add_custom_rack_device(self):
        available = self.rack_scene.get_available_u_positions(1)
        dialog = RackDeviceDialog(self, available_positions=available)
        if dialog.exec():
            config = dialog.get_config()
            if not config["id"]:
                QMessageBox.warning(self, "Error", "Device name cannot be empty")
                return
            
            existing_ids = [d.device_id for d in self.rack_scene.get_all_devices()]
            if config["id"] in existing_ids:
                QMessageBox.warning(self, "Error", "Device name already exists")
                return
            
            device = RackDevice(config["id"], config["device_type"], 
                               config["u_height"], config["start_u"])
            self.rack_scene.add_device(device)

    def edit_selected_device(self):
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:
            selected = [item for item in self.topology_scene.selectedItems() 
                        if isinstance(item, NodeItem)]
            if not selected:
                QMessageBox.information(self, "Info", "Please select a device first")
                return
            node = selected[0]
            dialog = DeviceConfigDialog(self, node.get_data())
            if dialog.exec():
                config = dialog.get_config()
                if config["id"] != node.node_id:
                    existing_ids = [n.node_id for n in self.topology_scene.get_all_nodes()]
                    if config["id"] in existing_ids:
                        QMessageBox.warning(self, "Error", "Device name already exists")
                        return
                self._replace_topology_node(node, config)
        else:
            selected = [item for item in self.rack_scene.selectedItems() 
                        if isinstance(item, RackDevice)]
            if not selected:
                QMessageBox.information(self, "Info", "Please select a device first")
                return
            device = selected[0]
            available = self.rack_scene.get_available_u_positions(device.u_height)
            if device.start_u not in available:
                available.append(device.start_u)
            dialog = RackDeviceDialog(self, device.get_data(), available)
            if dialog.exec():
                config = dialog.get_config()
                self.rack_scene.remove_device(device)
                new_device = RackDevice(config["id"], config["device_type"],
                                       config["u_height"], config["start_u"])
                self.rack_scene.add_device(new_device)

    def _replace_topology_node(self, old_node, config):
        pos = old_node.pos()
        self.topology_scene.removeItem(old_node)
        new_node = NodeItem(config["id"], config["device_type"],
                           config["port_config"], x=pos.x(), y=pos.y(),
                           label_config=config.get("label_config"),
                           u_size=config.get("u_size", 1))
        self.topology_scene.addItem(new_node)

    def delete_selected(self):
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:
            for item in self.topology_scene.selectedItems():
                if isinstance(item, NodeItem):
                    self.topology_scene.remove_node(item)
                elif isinstance(item, ConnectionItem):
                    self.topology_scene.remove_connection(item)
        else:
            for item in self.rack_scene.selectedItems():
                if isinstance(item, RackDevice):
                    self.rack_scene.remove_device(item)
    
    def remove_all_connections(self):
        reply = QMessageBox.question(
            self, 
            "确认拆除", 
            "确定要拆除所有线缆吗？\n此操作将删除所有连接线和标签。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.topology_scene.remove_all_connections()
    
    def remove_all_devices(self):
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            "确定要删除所有设备吗？\n此操作将删除所有设备和关联的线缆。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.topology_scene.remove_all_connections()
            for node in self.topology_scene.get_all_nodes():
                self.topology_scene.removeItem(node)

    def _clear_topology(self):
        self.topology_scene.remove_all_connections()
        for item in list(self.topology_scene.items()):
            self.topology_scene.removeItem(item)

    def _clear_rack(self):
        for rack in list(self.rack_scene._racks):
            self.rack_scene.removeItem(rack)
        self.rack_scene._racks = []
        self.rack_scene._rack_counter = 0
    
    def zoom_in(self):
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:
            self.topology_view.scale(1.2, 1.2)
        else:
            self.rack_view.scale(1.2, 1.2)
    
    def zoom_out(self):
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:
            self.topology_view.scale(1/1.2, 1/1.2)
        else:
            self.rack_view.scale(1/1.2, 1/1.2)
    
    def zoom_reset(self):
        current_tab = self.tab_widget.currentIndex()
        if current_tab == 0:
            self.topology_view.resetTransform()
        else:
            self.rack_view.resetTransform()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
