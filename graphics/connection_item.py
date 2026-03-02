from PySide6.QtWidgets import QGraphicsPathItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsItem, QGraphicsEllipseItem
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtGui import QPen, QPainterPath, QFont, QColor, QBrush

CABLE_COLORS = [
    QColor(0, 128, 0),
    QColor(0, 100, 200),
    QColor(200, 100, 0),
    QColor(150, 0, 150),
    QColor(0, 150, 150),
    QColor(200, 0, 0),
    QColor(100, 100, 0),
    QColor(0, 100, 100),
]


class CableAnchorPoint(QGraphicsEllipseItem):
    def __init__(self, tag_item, connection_item, parent=None):
        super().__init__(0, 0, 12, 12, parent)
        self._tag_item = tag_item
        self._connection = connection_item
        self.setBrush(QBrush(QColor(255, 0, 0)))
        self.setPen(QPen(QColor(200, 0, 0), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setZValue(99)
        self._is_dragging = False
        self.setVisible(True)
    
    def set_anchor_visible(self, visible):
        self.setVisible(visible)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._is_dragging and self.flags() & QGraphicsItem.GraphicsItemFlag.ItemIsMovable:
            new_pos = event.scenePos()
            self._tag_item._handle_anchor_drag(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def contextMenuEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, 'contextMenuEvent'):
            scene.contextMenuEvent(event)
        else:
            event.ignore()
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            if self._is_dragging:
                return self.pos()
        return super().itemChange(change, value)
    
    def update_position_from_path(self, scene_pos):
        self.setPos(scene_pos.x() - self.rect().width() / 2, 
                    scene_pos.y() - self.rect().height() / 2)


class CableTagItem(QGraphicsRectItem):
    def __init__(self, label_text: str, connection_item, parent=None):
        self._small_size = (30, 12)
        self._large_size = (80, 32)
        super().__init__(0, 0, self._small_size[0], self._small_size[1], parent)
        self._label_text = label_text
        self._connection = connection_item
        
        self._enabled = False
        self._fixed = False
        self._expanded = False
        self._direction = "right"
        self._position_on_path = 0.5
        self._text_item = None
        self._anchor_point = None
        
        self.setBrush(QBrush(QColor(255, 220, 0, 180)))
        self.setPen(QPen(QColor(180, 150, 0), 2))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setZValue(100)
        self.setVisible(False)
        
        self._is_dragging = False
        self._drag_start_pos = None
        self._has_moved = False
        self._last_click_time = 0
        self._last_click_pos = None
        
        self._create_anchor_point()
    
    def _create_anchor_point(self):
        self._anchor_point = CableAnchorPoint(self, self._connection)
    
    def show_anchor_after_delay(self):
        QTimer.singleShot(800, self._show_anchor_point)
    
    def _show_anchor_point(self):
        if self._enabled and self._anchor_point:
            if self._anchor_point.scene():
                self._anchor_point.set_anchor_visible(True)
    
    def _handle_anchor_drag(self, scene_pos):
        if not self._connection:
            return
        
        path = self._connection.path()
        if path.isEmpty():
            return
        
        nearest_point, nearest_t = self._find_nearest_point_on_path(path, scene_pos)
        self._position_on_path = nearest_t
        self._update_position()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_pos = event.pos()
            self._has_moved = False
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def contextMenuEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, 'contextMenuEvent'):
            scene.contextMenuEvent(event)
        else:
            event.ignore()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
            self._drag_start_pos = None
            
            if not self._has_moved:
                from PySide6.QtCore import QElapsedTimer
                current_time = QElapsedTimer()
                current_time.start()
                elapsed_ms = current_time.msecsSinceReference() - self._last_click_time if self._last_click_time > 0 else 1000
                
                click_pos = event.pos()
                if self._last_click_pos is not None:
                    distance = (click_pos - self._last_click_pos).manhattanLength()
                else:
                    distance = 100
                
                if elapsed_ms < 400 and distance < 10:
                    self._double_click_action()
                    self._last_click_time = 0
                    self._last_click_pos = None
                else:
                    self._last_click_time = current_time.msecsSinceReference()
                    self._last_click_pos = click_pos
                    self._single_click_action()
            
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def mouseMoveEvent(self, event):
        if self._is_dragging and not self._fixed:
            if self._drag_start_pos is not None:
                move_distance = (event.pos() - self._drag_start_pos).manhattanLength()
                if move_distance > 5:
                    self._has_moved = True
                    
                    new_pos = event.scenePos()
                    self._handle_tag_drag(new_pos)
                    event.accept()
                    return
        super().mouseMoveEvent(event)
    
    def _handle_tag_drag(self, scene_pos):
        if not self._connection:
            return
        
        path = self._connection.path()
        if path.isEmpty():
            return
        
        nearest_point, nearest_t = self._find_nearest_point_on_path(path, scene_pos)
        self._position_on_path = nearest_t
        self._update_position()
    
    def _single_click_action(self):
        if self._expanded:
            self._collapse()
        else:
            self.set_fixed(not self._fixed)
            self._update_fixed_appearance()
    
    def _update_fixed_appearance(self):
        if self._fixed:
            self.setPen(QPen(QColor(100, 100, 0), 2))
        else:
            self.setPen(QPen(QColor(180, 150, 0), 1))
    
    def _double_click_action(self):
        if not self._expanded:
            self._expand()
    
    def _expand(self):
        self._expanded = True
        self.setRect(0, 0, self._large_size[0], self._large_size[1])
        self._update_text()
    
    def _collapse(self):
        self._expanded = False
        self.setRect(0, 0, self._small_size[0], self._small_size[1])
        self._remove_text()
    
    def _toggle_direction(self):
        if not self._connection:
            return
        
        source_pos = self._connection.source_port.get_global_pos()
        target_pos = self._connection.target_port.get_global_pos()
        
        dx = target_pos.x() - source_pos.x()
        dy = target_pos.y() - source_pos.y()
        is_horizontal = abs(dx) > abs(dy)
        
        if is_horizontal:
            if self._direction == "top":
                self._direction = "bottom"
            else:
                self._direction = "top"
        else:
            if self._direction == "left":
                self._direction = "right"
            else:
                self._direction = "left"
        
        self._update_position()
    
    def _update_text(self):
        if self._text_item:
            if self._text_item.scene():
                self._text_item.scene().removeItem(self._text_item)
            self._text_item = None
        
        if not self._label_text:
            return
        
        lines = self._label_text.split(" To: ")
        if len(lines) < 2:
            return
        
        from_part = lines[0].replace("From: ", "")
        to_part = lines[1]
        
        from_parts = from_part.split()
        if len(from_parts) >= 2:
            from_device = from_parts[0]
            from_port = from_parts[1]
        else:
            from_device = from_parts[0] if from_parts else "?"
            from_port = "?"
        
        to_parts = to_part.split()
        if len(to_parts) >= 2:
            to_device = to_parts[0]
            to_port = to_parts[1]
        else:
            to_device = to_parts[0] if to_parts else "?"
            to_port = "?"
        
        line1 = f"From:{from_device} {from_port}"
        line2 = f"To:{to_device} {to_port}"
        
        formatted_text = f"{line1}\n{line2}"
        
        self._text_item = QGraphicsTextItem(formatted_text, self)
        font = QFont("Arial", 5, QFont.Weight.Bold)
        self._text_item.setFont(font)
        self._text_item.setDefaultTextColor(QColor(0, 0, 100))
        
        label_width = self.rect().width()
        label_height = self.rect().height()
        text_width = label_width - 4
        
        self._text_item.setTextWidth(text_width)
        
        text_rect = self._text_item.boundingRect()
        
        text_x = max(2, (label_width - text_rect.width()) / 2)
        text_y = max(1, (label_height - text_rect.height()) / 2)
        
        self._text_item.setPos(text_x, text_y)
        self._text_item.setZValue(101)
    
    def _remove_text(self):
        if self._text_item:
            self._text_item.setParentItem(None)
            self._text_item = None
    
    def set_enabled(self, enabled):
        self._enabled = enabled
        self.setVisible(enabled)
        if self._text_item:
            self._text_item.setVisible(enabled)
        if self._anchor_point:
            self._anchor_point.setVisible(enabled)
    
    def is_enabled(self):
        return self._enabled
    
    def set_fixed(self, fixed):
        self._fixed = fixed
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not fixed)
        if self._anchor_point:
            self._anchor_point.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self._update_fixed_appearance()
    
    def set_direction(self, direction):
        if direction in ["left", "right", "top", "bottom"]:
            self._direction = direction
            self._update_position()
    
    def set_position_on_path(self, position):
        self._position_on_path = max(0.0, min(1.0, position))
        self._update_position()
    
    def _update_position(self):
        if not self._connection:
            return
        
        path = self._connection.path()
        if path.isEmpty():
            return
        
        t = self._position_on_path
        path_point = path.pointAtPercent(t)
        
        rect_width = self.rect().width()
        rect_height = self.rect().height()
        
        if t < 0.01:
            tangent = self._calculate_tangent_at_percent(path, 0.01)
        elif t > 0.99:
            tangent = self._calculate_tangent_at_percent(path, 0.99)
        else:
            tangent = self._calculate_tangent_at_percent(path, t)
        
        is_horizontal = abs(tangent.x()) > abs(tangent.y())
        
        if is_horizontal:
            if self._direction == "top":
                offset_x = 0
                offset_y = -rect_height - 5
            elif self._direction == "bottom":
                offset_x = 0
                offset_y = 5
            else:
                self._direction = "top"
                offset_x = 0
                offset_y = -rect_height - 5
        else:
            if self._direction == "left":
                offset_x = -rect_width - 5
                offset_y = 0
            elif self._direction == "right":
                offset_x = 5
                offset_y = 0
            else:
                self._direction = "left"
                offset_x = -rect_width - 5
                offset_y = 0
        
        self.setPos(path_point.x() + offset_x, path_point.y() + offset_y)
        
        if self._anchor_point:
            if not self._anchor_point.scene() and self.scene():
                self.scene().addItem(self._anchor_point)
            
            self._anchor_point.update_position_from_path(path_point)
    
    def _calculate_tangent_at_percent(self, path, t):
        epsilon = 0.01
        t1 = max(0.0, t - epsilon)
        t2 = min(1.0, t + epsilon)
        
        p1 = path.pointAtPercent(t1)
        p2 = path.pointAtPercent(t2)
        
        return QPointF(p2.x() - p1.x(), p2.y() - p1.y())
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSceneChange:
            old_scene = self.scene()
            new_scene = value
            if old_scene and self._anchor_point and self._anchor_point.scene() == old_scene:
                old_scene.removeItem(self._anchor_point)
        return super().itemChange(change, value)
    
    def _constrain_to_cable(self, new_pos):
        if not self._connection:
            return new_pos
        
        path = self._connection.path()
        if path.isEmpty():
            return new_pos
        
        nearest_point, nearest_t = self._find_nearest_point_on_path(path, new_pos)
        
        self._position_on_path = nearest_t
        return nearest_point
    
    def _find_nearest_point_on_path(self, path, point):
        min_distance = float('inf')
        nearest_point = QPointF()
        nearest_t = 0.5
        
        samples = 50
        for i in range(samples + 1):
            t = i / samples
            path_point = path.pointAtPercent(t)
            dx = path_point.x() - point.x()
            dy = path_point.y() - point.y()
            distance = dx * dx + dy * dy
            
            if distance < min_distance:
                min_distance = distance
                nearest_point = path_point
                nearest_t = t
        
        return nearest_point, nearest_t
    
    def set_label_text(self, text):
        self._label_text = text
        if self._expanded:
            self._update_text()


class ConnectionItem(QGraphicsPathItem):
    _color_index = 0
    
    def __init__(self, source_port, target_port):
        super().__init__()
        self.source_port = source_port
        self.target_port = target_port
        self._source_tag = None
        self._target_tag = None
        self._color = self._get_next_color()
        self._original_pen = QPen(self._color, 2)
        self._selected_pen = QPen(self._color, 2, Qt.PenStyle.DashLine)
        self.setPen(self._original_pen)
        self.setZValue(50)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self._create_tags()
        self.update_path()
        
        self.source_port.set_connected(True, self)
        self.target_port.set_connected(True, self)

    @classmethod
    def _get_next_color(cls):
        color = CABLE_COLORS[cls._color_index % len(CABLE_COLORS)]
        cls._color_index += 1
        return color
    
    @classmethod
    def reset_color_index(cls):
        cls._color_index = 0

    def _create_tags(self):
        source_node = self.source_port.parentItem()
        target_node = self.target_port.parentItem()
        
        source_node_name = source_node.node_id if source_node else "?"
        target_node_name = target_node.node_id if target_node else "?"
        source_port_name = self.source_port.port_id
        target_port_name = self.target_port.port_id
        
        source_text = f"From: {source_node_name} {source_port_name} To: {target_node_name} {target_port_name}"
        target_text = f"From: {target_node_name} {target_port_name} To: {source_node_name} {source_port_name}"
        
        self._source_tag = CableTagItem(source_text, self)
        self._target_tag = CableTagItem(target_text, self)
        
        self._source_tag.set_position_on_path(0.3)
        self._target_tag.set_position_on_path(0.7)
        self._source_tag.set_direction("right")
        self._target_tag.set_direction("left")

    def update_path(self):
        source_pos = self.source_port.get_global_pos()
        target_pos = self.target_port.get_global_pos()
        
        path = QPainterPath()
        path.moveTo(source_pos)
        ctrl_x = (source_pos.x() + target_pos.x()) / 2
        path.cubicTo(QPointF(ctrl_x, source_pos.y()), QPointF(ctrl_x, target_pos.y()), target_pos)
        self.setPath(path)
        
        self._update_tags()

    def _update_tags(self):
        if self._source_tag:
            self._source_tag._update_position()
        if self._target_tag:
            self._target_tag._update_position()
    
    def _update_tag_texts(self):
        source_node = self.source_port.parentItem()
        target_node = self.target_port.parentItem()
        
        source_node_name = source_node.node_id if source_node else "?"
        target_node_name = target_node.node_id if target_node else "?"
        source_port_name = self.source_port.port_id
        target_port_name = self.target_port.port_id
        
        source_text = f"From: {source_node_name} {source_port_name} To: {target_node_name} {target_port_name}"
        target_text = f"From: {target_node_name} {target_port_name} To: {source_node_name} {source_port_name}"
        
        if self._source_tag:
            self._source_tag.set_label_text(source_text)
        if self._target_tag:
            self._target_tag.set_label_text(target_text)

    def add_tags_to_scene(self, scene):
        if self._source_tag and self._target_tag:
            scene.addItem(self._source_tag)
            scene.addItem(self._target_tag)
            
            if self._source_tag._anchor_point:
                scene.addItem(self._source_tag._anchor_point)
            if self._target_tag._anchor_point:
                scene.addItem(self._target_tag._anchor_point)
            
            self._source_tag._update_position()
            self._target_tag._update_position()
            
            self._source_tag.show_anchor_after_delay()
            self._target_tag.show_anchor_after_delay()

    def remove_tags_from_scene(self, scene):
        if self._source_tag:
            if self._source_tag._anchor_point and self._source_tag._anchor_point.scene():
                scene.removeItem(self._source_tag._anchor_point)
            scene.removeItem(self._source_tag)
        if self._target_tag:
            if self._target_tag._anchor_point and self._target_tag._anchor_point.scene():
                scene.removeItem(self._target_tag._anchor_point)
            scene.removeItem(self._target_tag)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value:
                self.setPen(self._selected_pen)
            else:
                self.setPen(self._original_pen)
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        scene = self.scene()
        if scene and hasattr(scene, 'contextMenuEvent'):
            scene.contextMenuEvent(event)
        else:
            super().contextMenuEvent(event)

    def get_data(self):
        source_node = self.source_port.parentItem()
        target_node = self.target_port.parentItem()
        return {
            "source_node": source_node.node_id if source_node else None,
            "source_port": self.source_port.port_id,
            "target_node": target_node.node_id if target_node else None,
            "target_port": self.target_port.port_id,
            "tags_enabled": self._source_tag.is_enabled() if self._source_tag else True
        }

    def disconnect(self):
        if self.source_port:
            self.source_port.set_connected(False, None)
        if self.target_port:
            self.target_port.set_connected(False, None)
    
    def set_tags_enabled(self, enabled):
        if self._source_tag:
            self._source_tag.set_enabled(enabled)
        if self._target_tag:
            self._target_tag.set_enabled(enabled)
    
    def set_tags_fixed(self, fixed):
        if self._source_tag:
            self._source_tag.set_fixed(fixed)
        if self._target_tag:
            self._target_tag.set_fixed(fixed)
