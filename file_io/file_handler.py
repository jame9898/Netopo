import json
from PySide6.QtWidgets import QMessageBox
from graphics.node_item import NodeItem
from graphics.connection_item import ConnectionItem


class FileHandler:
    def __init__(self, scene):
        self.scene = scene

    def save(self, filepath: str):
        data = {"nodes": [], "connections": []}
        for node in self.scene.get_all_nodes():
            data["nodes"].append(node.get_data())
        for conn in self.scene.get_all_connections():
            data["connections"].append(conn.get_data())
        try:
            print(f"正在保存文件: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"文件保存成功: {filepath}")
            return True
        except PermissionError as e:
            error_msg = f"权限不足，无法保存文件: {str(e)}"
            print(error_msg)
            QMessageBox.warning(None, "保存失败", error_msg)
            return False
        except Exception as e:
            error_msg = f"保存文件失败: {str(e)}"
            print(error_msg)
            QMessageBox.warning(None, "保存失败", error_msg)
            return False

    def load(self, filepath: str):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._clear_scene()
            node_map = {}
            for node_data in data.get("nodes", []):
                node = NodeItem(
                    node_data["id"],
                    node_data.get("device_type", "switch"),
                    node_data.get("port_config"),
                    node_data.get("x", 0),
                    node_data.get("y", 0),
                    node_data.get("template_id"),
                    node_data.get("vendor"),
                    node_data.get("renderer_key")
                )
                self.scene.addItem(node)
                node_map[node_data["id"]] = node
            
            print(f"加载了 {len(node_map)} 个节点")
            print(f"节点端口映射:")
            for node_id, node in node_map.items():
                print(f"  {node_id}: {list(node._port_map.keys())}")
            
            connections = data.get("connections", [])
            print(f"需要加载 {len(connections)} 条连接")
            
            for conn_data in connections:
                source_node_id = conn_data["source_node"]
                target_node_id = conn_data["target_node"]
                source_port_id = conn_data["source_port"]
                target_port_id = conn_data["target_port"]
                
                print(f"尝试连接: {source_node_id}:{source_port_id} -> {target_node_id}:{target_port_id}")
                
                source_node = node_map.get(source_node_id)
                target_node = node_map.get(target_node_id)
                
                if not source_node:
                    print(f"  错误: 找不到源节点 {source_node_id}")
                    continue
                if not target_node:
                    print(f"  错误: 找不到目标节点 {target_node_id}")
                    continue
                
                source_port = source_node.get_port_by_id(source_port_id)
                target_port = target_node.get_port_by_id(target_port_id)
                
                if not source_port:
                    print(f"  错误: 在节点 {source_node_id} 上找不到端口 {source_port_id}")
                    print(f"  可用端口: {list(source_node._port_map.keys())}")
                    continue
                if not target_port:
                    print(f"  错误: 在节点 {target_node_id} 上找不到端口 {target_port_id}")
                    print(f"  可用端口: {list(target_node._port_map.keys())}")
                    continue
                
                conn = ConnectionItem(source_port, target_port)
                self.scene.addItem(conn)
                conn.add_tags_to_scene(self.scene)
                
                tags_enabled = conn_data.get("tags_enabled", False)
                conn.set_tags_enabled(tags_enabled)
                
                self.scene._connections.append(conn)
                print(f"  连接成功 (标签显示: {tags_enabled})")
            
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(None, "加载失败", f"无法加载文件: {str(e)}")
            return False

    def _clear_scene(self):
        for conn in self.scene.get_all_connections():
            conn.remove_labels_from_scene(self.scene)
        self.scene._connections.clear()
        for item in list(self.scene.items()):
            self.scene.removeItem(item)
