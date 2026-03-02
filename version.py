"""
Netopo 版本信息
"""

__version__ = "1.0.1"
__version_info__ = (1, 0, 1)
__author__ = "Netopo Team"
__release_date__ = None  # 2025-03-02

VERSION = f"V{__version__}"
FULL_VERSION = f"Netopo {VERSION}"

def get_version():
    """获取版本号"""
    return __version__

def get_version_info():
    """获取版本信息元组"""
    return __version_info__

def get_full_version():
    """获取完整版本字符串"""
    return FULL_VERSION
