[README.md](https://github.com/user-attachments/files/25679169/README.md)
# Netopo - 网络拓扑编辑器

一个基于 PySide6 开发的网络拓扑图编辑器，支持多种网络设备的可视化编辑、连接管理和机架布局。

## 功能特性

### 设备支持
- **网络设备**：交换机、路由器、服务器、防火墙
- **终端设备**：PC、手机、NAS
- **接入设备**：光猫、家用路由器、无线控制器(AC)、无线接入点(AP)
- **运营商网络**：ISP（单接口/双接口）

### 拓扑编辑
- 拖拽式设备添加和移动
- 设备端口自定义配置（电口、光口、Console、USB）
- 多种端口布局模式（单行、双行、Z字形、N字形）
- 设备间端口连接管理
- 线缆标签显示和管理

### 机架管理
- 47U 标准机架支持
- 设备上架和 U 位管理
- 多 U 高度设备支持（1U-8U）
- 机架视图与拓扑视图联动

### 文件操作
- 保存/加载拓扑文件（.topo 格式）
- 导出为 PDF 文档（含拓扑图、机架布局、设备清单）

## 安装

### 方式一：直接运行 EXE（推荐）

从 [Releases](../../releases) 页面下载最新的 `Netopo.exe`，双击运行即可。

### 方式二：从源码运行

#### 环境要求
- Python 3.10+
- PySide6

#### 安装依赖
```bash
pip install PySide6
```

#### 运行程序
```bash
python main.py
```

## 使用指南

### 添加设备
1. 点击工具栏「快速添加」按钮
2. 选择设备类型（运营商网络/三层设备/二层设备/终端设备）
3. 设备将自动添加到拓扑界面

### 连接设备
1. 确保工具栏「连接」状态为 ON
2. 右键点击源设备的端口
3. 再右键点击目标设备的端口
4. 连接自动创建

### 管理机架
1. 点击「快速添加」→「添加机架（47U）」
2. 右键点击设备 →「添加到机架」
3. 选择目标 U 位

### 保存/导出
- **保存**：文件 → 保存（.topo 格式）
- **导出**：文件 → 导出为 PDF

## 项目结构

```
Netopo/
├── main.py                 # 主程序入口
├── config/
│   └── device_specs.py     # 设备规格配置
├── dialogs/
│   ├── device_config_dialog.py    # 设备配置对话框
│   ├── device_name_dialog.py      # 设备命名对话框
│   ├── rack_device_dialog.py      # 机架设备对话框
│   ├── template_selection_dialog.py # 模板选择对话框
│   └── cable_tag_table_dialog.py  # 线缆标签表格对话框
├── file_io/
│   └── file_handler.py     # 文件读写处理
├── graphics/
│   ├── scene.py            # 拓扑场景
│   ├── node_item.py        # 设备节点
│   ├── port_item.py        # 端口组件
│   └── connection_item.py  # 连接线
├── rack/
│   ├── rack_scene.py       # 机架场景
│   ├── rack_device.py      # 机架设备
│   └── u_slot.py           # U位槽位
├── renderers/
│   └── device_renderers.py # 设备渲染器
├── templates/
│   └── device_templates.py # 设备模板
└── Netopo.spec             # PyInstaller 配置
```

## 打包说明

使用 PyInstaller 打包为独立可执行文件：

```bash
pip install pyinstaller
python -m PyInstaller Netopo.spec --noconfirm
```

打包后的 EXE 文件位于 `dist/Netopo.exe`。

> 注意：如果直接运行 `pyinstaller` 命令提示找不到命令，请使用 `python -m PyInstaller` 代替。

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！
