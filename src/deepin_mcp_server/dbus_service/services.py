"""
DBus interface constants for Deepin system services.
"""

import json
import os
import logging
import subprocess
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def _get_system_version() -> str:
    """Get the deepin system version"""
    try:
        with open("/etc/deepin-version", 'r') as f:
            for line in f:
                if line.startswith("Version="):
                    return line.split("=")[1].strip()
    except Exception as e:
        logger.error(f"Failed to get system version: {e}")
    return "25"  # Default to latest version

# Get system version
version = _get_system_version()
is_v20 = "20" in version

# Common DBus services that don't change with version
COMMON_SERVICES = {
    "WM": {
        "service": "com.deepin.wm",
        "path": "/com/deepin/wm",
        "interface": "com.deepin.wm"
    },
    "CALENDAR": {
        "service": "com.deepin.dataserver.Calendar",
        "path": "/com/deepin/dataserver/Calendar/account_local",
        "interface": "com.deepin.dataserver.Calendar.Account"
    }
}

# Version-specific DBus services
V20_SERVICES = {
    "DOCK": {
        "service": "com.deepin.dde.daemon.Dock",
        "path": "/com/deepin/dde/daemon/Dock",
        "interface": "com.deepin.dde.daemon.Dock"
    },
    "APPEARANCE": {
        "service": "com.deepin.daemon.Appearance",
        "path": "/com/deepin/daemon/Appearance",
        "interface": "com.deepin.daemon.Appearance"
    },
    "DISPLAY": {
        "service": "com.deepin.daemon.Display",
        "path": "/com/deepin/daemon/Display",
        "interface": "com.deepin.daemon.Display"
    },
    "NOTIFICATION": {
        "service": "com.deepin.dde.Notification",
        "path": "/com/deepin/dde/Notification",
        "interface": "com.deepin.dde.Notification"
    },
    "START_MANAGER": {
        "service": "com.deepin.SessionManager",
        "path": "/com/deepin/StartManager",
        "interface": "com.deepin.StartManager"
    },
    "MIME": {
        "service": "com.deepin.daemon.Mime",
        "path": "/com/deepin/daemon/Mime",
        "interface": "com.deepin.daemon.Mime"
    }
}

V23_SERVICES = {
    "DOCK": {
        "service": "org.deepin.dde.Dock1",
        "path": "/org/deepin/dde/Dock1",
        "interface": "org.deepin.dde.daemon.Dock1"
    },
    "APPEARANCE": {
        "service": "org.deepin.dde.Appearance1",
        "path": "/org/deepin/dde/Appearance1",
        "interface": "org.deepin.dde.Appearance1"
    },
    "DISPLAY": {
        "service": "org.deepin.dde.Display1",
        "path": "/org/deepin/dde/Display1",
        "interface": "org.deepin.dde.Display1"
    },
    "NOTIFICATION": {
        "service": "org.deepin.dde.Notification1",
        "path": "/org/deepin/dde/Notification1",
        "interface": "org.deepin.dde.Notification1"
    },
    "START_MANAGER": {
        "service": "org.desktopspec.ApplicationManager1",
        "path": "/org/desktopspec/ApplicationManager1",
        "interface": "org.desktopspec.ApplicationManager1.Application"
    },
    "MIME": {
        "service": "org.deepin.dde.Mime1",
        "path": "/org/deepin/dde/Mime1",
        "interface": "org.deepin.dde.Mime1"
    }
}

# Combine services based on version
SERVICES = {**COMMON_SERVICES, **(V20_SERVICES if is_v20 else V23_SERVICES)}

# Export individual constants for backward compatibility
for name, service in SERVICES.items():
    globals()[f"{name}_SERVICE"] = service["service"]
    globals()[f"{name}_PATH"] = service["path"]
    globals()[f"{name}_INTERFACE"] = service["interface"]

def dbus_send(service_name: str, method: str, *args) -> str:
    """
    使用dbus-send命令调用DBus接口
    
    Args:
        service_name: 服务名
        method: 方法名
        *args: 方法参数
    
    Returns:
        str: 命令输出结果
    """
    try:
        # 构建dbus-send命令
        cmd = ["dbus-send", "--session", "--print-reply"]

        service_info = SERVICES[service_name]
        
        # 添加服务、路径和接口
        cmd.extend([
            f"--dest={service_info['service']}", 
            service_info['path'], 
            f"{service_info['interface']}.{method}"
        ])
        
        # 添加参数
        for arg in args:
            if isinstance(arg, bool):
                cmd.append(f"boolean:{str(arg).lower()}")
            elif isinstance(arg, int):
                cmd.append(f"int32:{arg}")
            elif isinstance(arg, str):
                cmd.append(f"string:{arg}")
            elif isinstance(arg, list):
                cmd.append(f"array:string:{','.join(arg)}")
            else:
                cmd.append(f"string:{str(arg)}")
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"DBus command failed: {e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in dbus_send: {e}")
        raise

def dbus_get_property(service_name: str,  property_name: str) -> str:
    """
    获取DBus属性值
    
    Args:
        service: 服务名
        interface: 接口名
        property_name: 属性名
    
    Returns:
        str: 属性值
    """
    try:
        cmd = ["dbus-send", "--session", "--print-reply"]
        service_info = SERVICES[service_name]

        # dbus-send --session --print-reply --dest=org.deepin.dde.Display1 /org/deepin/dde/Display1 org.freedesktop.DBus.Properties.Get string:"org.deepin.dde.Display1" string:"Primary"
        cmd.extend([
            f"--dest={service_info['service']}", 
            service_info['path'], 
            f"org.freedesktop.DBus.Properties.Get",
            f"string:{service_info['interface']}",
            f"string:{property_name}"
        ])

        # 解析返回的DBus消息
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        match = re.search(r'variant\s+string\s+"([^"]+)"', result.stdout)
        if match:
            return match.group(1)
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to get property {property_name} for {service_name}: {e}")
        raise

def dbus_set_property(service_name: str, property_name: str, value) -> None:
    """
    设置DBus属性值
    
    Args:
        service: 服务名
        interface: 接口名
        property_name: 属性名
        value: 属性值
    """
    try:
        cmd = ["dbus-send", "--session", "--print-reply"]
        service_info = SERVICES[service_name]
        cmd.extend([
            f"--dest={service_info['service']}", 
            service_info['path'], 
            f"org.freedesktop.DBus.Properties.Set",
            f"string:{service_info['interface']}",
            f"string:{property_name}",
            f"variant",
            f"string",
            f"{value}"
        ])

        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        logger.error(f"Failed to set property {property_name} for {service_name}: {e}")
        raise

def show_confirmation_dialog(title: str, message: str, timeout: int = 30) -> bool:
    """
    显示确认对话框
    
    Args:
        title: 对话框标题
        message: 对话框消息
        timeout: 超时时间（秒）
    
    Returns:
        bool: True表示用户点击确认，False表示取消或超时
    """
    try:
        # 使用zenity显示对话框（深度系统通常包含zenity）
        result = subprocess.run([
            "zenity", "--question",
            f"--title={title}",
            f"--text={message}",
            f"--timeout={timeout}",
            "--width=400",
            "--height=150"
        ], capture_output=True, timeout=timeout + 5)
        
        # zenity返回0表示用户点击了"是"，1表示"否"，5表示超时
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.warning("对话框超时")
        return False
    except FileNotFoundError:
        # 如果zenity不可用，尝试使用kdialog
        try:
            result = subprocess.run([
                "kdialog", "--yesno",
                message,
                f"--title={title}"
            ], capture_output=True, timeout=timeout + 5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("没有可用的对话框工具")
            return False
    except Exception as e:
        logger.error(f"显示对话框失败: {e}")
        return False

def show_notification(title: str, message: str, icon: str = "dialog-information", timeout: int = 5000) -> str:
    """
    显示系统通知
    
    Args:
        title: 通知标题
        message: 通知消息
        icon: 图标名称
        timeout: 显示时间（毫秒）
    
    Returns:
        str: 操作结果
    """
    try:
        # 尝试使用深度通知服务
        if "NOTIFICATION" in SERVICES:
            try:
                result = dbus_send(
                    "NOTIFICATION",
                    "Notify",
                    "deepin-mcp-server",  # app_name
                    0,                    # replaces_id
                    icon,                 # app_icon
                    title,                # summary
                    message,              # body
                    [],                   # actions
                    {},                   # hints
                    timeout               # expire_timeout
                )
                return f"通知已发送: {title}"
            except Exception as e:
                logger.warning(f"D-Bus通知失败: {e}")
        
        # 备用方案：使用notify-send
        result = subprocess.run([
            "notify-send",
            f"--expire-time={timeout}",
            f"--icon={icon}",
            title,
            message
        ], capture_output=True, timeout=10)
        
        if result.returncode == 0:
            return f"通知已发送: {title}"
        else:
            return f"通知发送失败: {result.stderr.decode()}"
            
    except FileNotFoundError:
        return "错误: 系统不支持通知功能"
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        return f"通知发送失败: {str(e)}"