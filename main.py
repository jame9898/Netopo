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
        file_menu.addAction("导出为PNG...", self.export_png)
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
        """PDF导出 - 使用QImage中间层方案"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出PDF", "", FILTER_PDF)
        
        if not filepath:
            return
        
        if not filepath.endswith('.pdf'):
            filepath += '.pdf'
        
        nodes = self.topology_scene.get_all_nodes()
        if not nodes:
            QMessageBox.warning(self, "导出失败", "没有网络拓扑数据可导出")
            return
        
        try:
            from PySide6.QtPrintSupport import QPrinter
            from PySide6.QtGui import QImage, QPainter, QColor, QPageSize, QPageLayout, QFont, QPen, QBrush
            from PySide6.QtCore import QSize, QRectF
            
            # 创建打印机
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filepath)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            
            painter = QPainter(printer)
            if not painter.isActive():
                QMessageBox.warning(self, "导出失败", "无法创建PDF文件")
                return
            
            page_rect = printer.pageRect(QPrinter.Unit.DevicePixel)
            page_width = page_rect.width()
            page_height = page_rect.height()
            
            # 字体设置
            title_font = QFont()
            title_font.setPointSize(16)
            title_font.setBold(True)
            
            header_font = QFont()
            header_font.setPointSize(11)
            header_font.setBold(True)
            
            cell_font = QFont()
            cell_font.setPointSize(10)
            
            # ===== 第一页：网络拓扑图 =====
            # 标题位置调整：增加顶部边距，确保完整显示
            title_y = 80
            painter.setFont(title_font)
            painter.drawText(int(page_width * 0.4), title_y, "网络拓扑图")
            
            # 渲染拓扑场景到QImage（关键：使用与PNG相同的方法）
            scene_rect = self.topology_scene.sceneRect()
            margin = 50
            img_width = int(scene_rect.width() + 2 * margin)
            img_height = int(scene_rect.height() + 2 * margin)
            
            # 创建QImage
            topo_image = QImage(QSize(img_width, img_height), QImage.Format.Format_ARGB32)
            topo_image.fill(QColor(255, 255, 255))
            
            # 渲染场景到QImage
            img_painter = QPainter(topo_image)
            img_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            img_painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            img_painter.translate(margin, margin)
            self.topology_scene.render(img_painter, source=scene_rect)
            img_painter.end()
            
            # 计算缩放以适应PDF页面（调整可用高度，为标题留出空间）
            available_width = page_width - 100
            available_height = page_height - 200  # 增加顶部空间
            
            scale_x = available_width / img_width
            scale_y = available_height / img_height
            scale = min(scale_x, scale_y)
            
            # 绘制QImage到PDF（调整起始位置，确保与标题有间距）
            target_width = int(img_width * scale)
            target_height = int(img_height * scale)
            target_x = 50
            target_y = title_y + 40  # 标题下方40像素
            
            painter.drawImage(QRectF(target_x, target_y, target_width, target_height), topo_image)
            
            # ===== 第二页：设备清单 =====
            printer.newPage()
            
            # 标题位置与第一页保持一致
            painter.setFont(title_font)
            painter.drawText(int(page_width * 0.45), title_y, "设备清单")
            
            # 表格参数优化：根据页面宽度动态调整列宽
            available_width = page_width - 200  # 左右各留100像素边距
            col_widths = [
                int(available_width * 0.15),  # 设备名称 15%
                int(available_width * 0.12),  # 设备类型 12%
                int(available_width * 0.25),  # 源接口 25%
                int(available_width * 0.25),  # 目的接口 25%
                int(available_width * 0.23)   # 位置 23%
            ]
            
            # 表格居中：计算起始X坐标
            table_width = sum(col_widths)
            table_x = int((page_width - table_width) / 2)  # 居中
            col_x = [table_x]
            for w in col_widths[:-1]:
                col_x.append(col_x[-1] + w)
            
            row_height = 600  # 行高600像素（400的1.5倍）
            y_pos = title_y + 50  # 与第一页保持一致的间距
            
            # 调整字体大小以匹配表格
            header_font_large = QFont()
            header_font_large.setPointSize(24)  # 表头字体
            header_font_large.setBold(True)
            
            cell_font_large = QFont()
            cell_font_large.setPointSize(16)  # 内容字体（20的0.8倍）
            
            # 表头样式优化
            painter.setPen(QPen(QColor(0, 0, 0), 3))
            painter.setBrush(QBrush(QColor(70, 130, 180)))  # 深蓝色背景
            painter.drawRect(col_x[0], y_pos, table_width, row_height)
            
            # 表头文字（白色，居中）
            painter.setFont(header_font_large)
            painter.setPen(QPen(QColor(255, 255, 255), 1))  # 白色文字
            headers = ["设备名称", "设备类型", "源接口", "目的接口", "位置"]
            for i, header in enumerate(headers):
                # 计算每列的中心位置
                col_center_x = col_x[i] + col_widths[i] // 2
                # 使用文字宽度居中
                text_width = painter.fontMetrics().horizontalAdvance(header)
                text_x = col_center_x - text_width // 2
                painter.drawText(text_x, y_pos + 350, header)  # 文字在600像素行高中居中
            
            y_pos += row_height
            
            # 绘制表头下方的分隔线
            painter.setPen(QPen(QColor(0, 0, 0), 3))
            painter.drawLine(col_x[0], y_pos, col_x[0] + table_width, y_pos)
            
            # 收集连接信息 - 每条物理线路生成两条记录（双向）
            connections = self.topology_scene.get_all_connections()
            connection_rows = []
            
            for conn in connections:
                source_node = conn.source_port.parentItem()
                target_node = conn.target_port.parentItem()
                
                if source_node and target_node:
                    # 第一条记录：源设备 → 目标设备（输出线路）
                    connection_rows.append({
                        'device_name': source_node.node_id,
                        'device_type': source_node.device_type,
                        'source_port': conn.source_port.port_id,
                        'target_port': f"{conn.target_port.port_id}→{target_node.node_id}",
                        'direction': '输出',
                        'node': source_node
                    })
                    
                    # 第二条记录：目标设备 ← 源设备（输入线路）
                    connection_rows.append({
                        'device_name': target_node.node_id,
                        'device_type': target_node.device_type,
                        'source_port': conn.target_port.port_id,
                        'target_port': f"{conn.source_port.port_id}←{source_node.node_id}",
                        'direction': '输入',
                        'node': target_node
                    })
            
            # 数据行样式优化
            painter.setFont(cell_font_large)
            for row_data in connection_rows:
                if y_pos > page_height - 100:
                    printer.newPage()
                    y_pos = title_y + 50
                    
                    # 重复表头
                    painter.setPen(QPen(QColor(0, 0, 0), 3))
                    painter.setBrush(QBrush(QColor(70, 130, 180)))
                    painter.drawRect(col_x[0], y_pos, table_width, row_height)
                    
                    painter.setFont(header_font_large)
                    painter.setPen(QPen(QColor(255, 255, 255), 1))
                    for i, header in enumerate(headers):
                        col_center_x = col_x[i] + col_widths[i] // 2
                        text_width = painter.fontMetrics().horizontalAdvance(header)
                        text_x = col_center_x - text_width // 2
                        painter.drawText(text_x, y_pos + 350, header)
                    
                    y_pos += row_height
                    painter.setPen(QPen(QColor(0, 0, 0), 3))
                    painter.drawLine(col_x[0], y_pos, col_x[0] + table_width, y_pos)
                
                # 绘制单元格背景（交替颜色）
                if connection_rows.index(row_data) % 2 == 0:
                    painter.setBrush(QBrush(QColor(255, 255, 255)))
                else:
                    painter.setBrush(QBrush(QColor(245, 245, 245)))
                
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                painter.drawRect(col_x[0], y_pos, table_width, row_height)
                
                # 绘制垂直网格线
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                for x in col_x[1:]:
                    painter.drawLine(x, y_pos, x, y_pos + row_height)
                
                # 绘制水平网格线
                painter.setPen(QPen(QColor(200, 200, 200), 1))
                painter.drawLine(col_x[0], y_pos + row_height, col_x[0] + table_width, y_pos + row_height)
                
                # 绘制文字（调整垂直位置，确保在单元格内）
                painter.setPen(QPen(QColor(0, 0, 0), 1))
                text_y = y_pos + 350  # 文字在600像素行高中居中
                
                # 设备名称（居中）
                text = row_data['device_name']
                text_width = painter.fontMetrics().horizontalAdvance(text)
                text_x = col_x[0] + col_widths[0] // 2 - text_width // 2
                painter.drawText(text_x, text_y, text)
                
                # 设备类型（居中）
                text = row_data['device_type'] or "未知"
                text_width = painter.fontMetrics().horizontalAdvance(text)
                text_x = col_x[1] + col_widths[1] // 2 - text_width // 2
                painter.drawText(text_x, text_y, text)
                
                # 源接口（居中）
                text = row_data['source_port']
                text_width = painter.fontMetrics().horizontalAdvance(text)
                text_x = col_x[2] + col_widths[2] // 2 - text_width // 2
                painter.drawText(text_x, text_y, text)
                
                # 目的接口（居中）
                text = row_data['target_port']
                text_width = painter.fontMetrics().horizontalAdvance(text)
                text_x = col_x[3] + col_widths[3] // 2 - text_width // 2
                painter.drawText(text_x, text_y, text)
                
                # 位置（居中）
                node = row_data['node']
                rack_info = node.get_rack_info() if hasattr(node, 'get_rack_info') else None
                if rack_info:
                    text = f"{rack_info.get('rack_name', '')} U{rack_info.get('start_u', '')}"
                else:
                    text = "未上架"
                text_width = painter.fontMetrics().horizontalAdvance(text)
                text_x = col_x[4] + col_widths[4] // 2 - text_width // 2
                painter.drawText(text_x, text_y, text)
                
                y_pos += row_height
            
            painter.end()
            QMessageBox.information(self, "导出成功", f"PDF已保存到：{filepath}")
            
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "导出失败", f"PDF导出失败：{str(e)}\n{traceback.format_exc()}")
    
    def export_png(self):
        from PySide6.QtGui import QImage, QPainter, QColor
        from PySide6.QtCore import QSize
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "导出PNG", "", "PNG图片 (*.png)")
        
        if not filepath:
            return
        
        if not filepath.endswith('.png'):
            filepath += '.png'
        
        nodes = self.topology_scene.get_all_nodes()
        if not nodes:
            QMessageBox.warning(self, "导出失败", "没有网络拓扑数据可导出")
            return
        
        scene_rect = self.topology_scene.sceneRect()
        margin = 50
        width = int(scene_rect.width() + 2 * margin)
        height = int(scene_rect.height() + 2 * margin)
        
        image = QImage(QSize(width, height), QImage.Format.Format_ARGB32)
        image.fill(QColor(255, 255, 255))
        
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        
        painter.translate(margin, margin)
        self.topology_scene.render(painter, source=scene_rect)
        
        painter.end()
        
        if image.save(filepath):
            QMessageBox.information(self, "导出成功", f"PNG已保存到：{filepath}")
        else:
            QMessageBox.warning(self, "导出失败", "PNG文件保存失败")

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
