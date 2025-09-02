import os
import re
import json
import logging
import subprocess
import shlex
from dbus_service.services import dbus_send, dbus_get_property, dbus_set_property

# Configure logging
logger = logging.getLogger(__name__)
# 切换壁纸
def _switch_wallpaper(file_url: str = None) -> str:
    try:
        def convert_url_to_local_path(url: str) -> str:
            if url.startswith("/"):
                return url
            else:
                import urllib.parse
                return urllib.parse.unquote(url)
        
        # Get wallpaper list
        logger.info("Getting wallpaper list from Appearance service...")
        wallpaper_list = dbus_send(
            "APPEARANCE",
            "List",
            "background"
        )
        
        # Get current wallpaper
        logger.info("Getting primary screen from Display service...")
        primary_screen = dbus_get_property("DISPLAY", "Primary")
        logger.info(f"Primary screen: {primary_screen}")
        
        logger.info("Getting current wallpaper from WM service...")
        current_wallpaper = dbus_send(
            "WM",
            "GetCurrentWorkspaceBackgroundForMonitor",
            primary_screen
        )
        logger.info(f"Current wallpaper: {current_wallpaper}")

        # 如果提供了文件URL，直接使用
        if file_url:
            wallpaper_path = convert_url_to_local_path(file_url)
            if not os.path.exists(wallpaper_path):
                return f"Error: 指定的壁纸文件不存在: {wallpaper_path}"
            
            logger.info("Setting new wallpaper...")
            dbus_send(
                "APPEARANCE",
                "SetMonitorBackground",
                primary_screen,
                wallpaper_path
            )
            logger.info("Wallpaper set successfully")
            return f"成功设置壁纸: {wallpaper_path}"
        
        # 解析当前壁纸路径
        current_wallpaper_path = None
        if current_wallpaper:
            match = re.search(r'string\s+"([^"]+)"', current_wallpaper)
            if match:
                current_wallpaper_path = match.group(1)
        
        # Parse wallpaper list
        wallpapers = []
        if wallpaper_list:
            # 从DBus返回中提取JSON字符串
            lines = wallpaper_list.split('\n')
            
            # 找到包含JSON的行
            json_line = None
            for line in lines:
                if line.strip().startswith('string "'):
                    json_line = line.strip()
                    break
            
            if json_line:
                # 提取JSON字符串
                match = re.search(r'string\s+"(.*)"', json_line)
                if match:
                    json_str = match.group(1)
                    
                    try:
                        # 解析JSON
                        wallpaper_data = json.loads(json_str)
                        if isinstance(wallpaper_data, list):
                            for item in wallpaper_data:
                                if isinstance(item, dict) and "Id" in item:
                                    wallpapers.append(item["Id"])
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse wallpaper list JSON: {e}")
                        return "Error: Failed to parse wallpaper list"
            else:
                logger.error("No JSON string found in DBus response")
                return "Error: No wallpaper list found"
        
        if not wallpapers or not primary_screen:
            logger.error("Failed to get wallpaper list or primary screen")
            return "Error: Failed to get wallpaper list or primary screen"
            
        # Find next wallpaper
        try:
            current_idx = wallpapers.index(current_wallpaper_path) if current_wallpaper_path else 0
            next_idx = (current_idx + 1) % len(wallpapers)
        except ValueError:
            next_idx = 0
            
        next_wallpaper = wallpapers[next_idx]
        # Set new wallpaper
        logger.info("Setting new wallpaper...")
        dbus_send(
            "APPEARANCE",
            "SetMonitorBackground",
            primary_screen,
            next_wallpaper
        )
        logger.info("Wallpaper set successfully")
        
        return "Successfully switched wallpaper"
        
    except Exception as e:
        logger.error(f"Error switching wallpaper: {e}")
        return f"Error: {str(e)}"

# 切换dock模式
def _switch_dock_mode(mode: int) -> str:
    try:
        if mode not in [0, 1]:
            return "Error: Invalid mode. Mode must be 0 (Fashion) or 1 (Efficient)"

        dbus_set_property("DOCK", "DisplayMode", mode)
        
        return f"Successfully switched dock mode to {'Fashion' if mode == 0 else 'Efficient'}"
        
    except Exception as e:
        logger.error(f"Error switching dock mode: {e}")
        return f"Error: {str(e)}"

# 设置勿扰模式
def _set_do_not_disturb(state: bool) -> str:
    try:
        dbus_send(
            "NOTIFICATION",
            "SetSystemInfo",
            "0",  # DNDMODE
            str(state).lower()
        )

        return f"Successfully {'enabled' if state else 'disabled'} do not disturb mode"            
    except Exception as e:
        logger.error(f"Error setting do not disturb mode: {e}")
        return f"Error: {str(e)}"

# 切换系统主题
def _switch_system_theme(theme: int) -> str:
    try:
        if theme not in [0, 1, 2]:
            return "Error: Invalid theme. Theme must be 0 (deepin), 1 (deepin-dark), or 2 (deepin-auto)"

        theme_map = {
            0: "deepin",
            1: "deepin-dark",
            2: "deepin-auto"
        }

        dbus_send(
            "APPEARANCE",
            "Set",
            "gtk",
            theme_map[theme]
        )
        
        return f"Successfully switched theme to {theme_map[theme]}"
        
    except Exception as e:
        logger.error(f"Error switching theme: {e}")
        return f"Error: {str(e)}"

# 获取系统硬件信息
def _get_system_memory() -> str:
    try:
        def format_size(size_bytes: int) -> str:
            """将字节数转换为人类可读的格式"""
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.2f} PB"

        # 获取CPU信息
        cpu_info = {}
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.strip():
                    if ':' in line:
                        key, value = line.split(':', 1)
                        cpu_info[key.strip()] = value.strip()
        
        # 获取内存信息
        mem_info = {}
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.strip():
                    key, value = line.split(':', 1)
                    mem_info[key.strip()] = value.strip().split()[0]

        # 通过lsblk命令获取硬盘信息
        disk_info = {}
        result = subprocess.check_output(['lsblk', '-o', 'NAME,SIZE,TYPE']).decode('utf-8')
        for line in result.split('\n'):
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 3:
                    disk_name = parts[0]
                    disk_size = parts[1]
                    disk_type = parts[2]
                    disk_info[disk_name] = {
                        'size': disk_size,
                        'type': disk_type
                    }

        # 构建返回信息
        result = []
        
        # CPU信息
        if 'model name' in cpu_info:
            result.append(f"CPU型号: {cpu_info['model name']}")
        if 'cpu cores' in cpu_info:
            result.append(f"CPU核心数: {cpu_info['cpu cores']}")
        
        # 内存信息
        if 'MemTotal' in mem_info:
            total_mem = int(mem_info['MemTotal']) * 1024  # 转换为字节
            result.append(f"总内存: {format_size(total_mem)}")
        if 'MemAvailable' in mem_info:
            available_mem = int(mem_info['MemAvailable']) * 1024
            result.append(f"可用内存: {format_size(available_mem)}")
        
        # 硬盘信息
        if disk_info:
            result.append(f"硬盘信息: {disk_info}")

        return "\n".join(result)

    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return f"获取系统信息失败: {str(e)}"

# 发送邮件
def _send_mail(email_data: dict) -> str:
    try:
        # 验证必填字段
        if not email_data.get("to"):
            return "错误：收件人(to)是必填项"
            
        # 构建mailto URL
        mailto_url = "mailto:?"
        
        # 添加查询参数
        query_params = []
        
        # 添加收件人
        if email_data.get("to"):
            query_params.append(f"to={email_data['to']}")
            
        # 添加抄送
        if email_data.get("cc"):
            query_params.append(f"cc={email_data['cc']}")
            
        # 添加密送
        if email_data.get("bcc"):
            query_params.append(f"bcc={email_data['bcc']}")
            
        # 添加主题
        if email_data.get("subject"):
            query_params.append(f"subject={email_data['subject']}")
            
        # 添加正文
        if email_data.get("content"):
            query_params.append(f"body={email_data['content']}")
            
        # 添加类型参数
        query_params.append("type=1")
        
        # 组合所有查询参数
        mailto_url += "&".join(query_params)
        
        # 使用xdg-open打开mailto URL
        try:
            process = subprocess.Popen(
                ["xdg-open", mailto_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(timeout=5)
            
            if process.returncode != 0:
                logger.warning(f"打开邮件客户端失败。退出码: {process.returncode}")
                logger.warning(f"mailto_url: {mailto_url}")
                return f"错误：打开邮件客户端失败。退出码: {process.returncode} 错误信息: {stderr.decode('utf-8')}"
                
            return f"成功打开邮件客户端，详情如下：\n" \
                   f"收件人: {email_data.get('to', '')}\n" \
                   f"主题: {email_data.get('subject', '')}\n" \
                   f"抄送: {email_data.get('cc', '')}\n" \
                   f"密送: {email_data.get('bcc', '')}\n" \
                   f"正文: {email_data.get('content', '')}"
                   
        except subprocess.TimeoutExpired:
            process.kill()
            return "错误：打开邮件客户端超时"
        except Exception as e:
            logger.error(f"打开邮件客户端错误: {e}")
            return f"错误: {str(e)}"
            
    except Exception as e:
        logger.error(f"send_mail中发生意外错误: {e}")
        return f"错误: {str(e)}"

# 创建日程
def _create_schedule(schedule_data: dict) -> str:
    try:
        # 验证必填字段
        if not all(key in schedule_data for key in ["start_time", "end_time"]):
            return "错误：开始时间(start_time)和结束时间(end_time)是必填项"

        from datetime import datetime

        # 验证时间格式
        try:
            start_time = datetime.strptime(schedule_data["start_time"], "%Y-%m-%dT%H:%M:%S")
            end_time = datetime.strptime(schedule_data["end_time"], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            return "错误：时间格式无效，请使用yyyy-MM-ddThh:mm:ss格式"

        # 准备日程数据
        schedule_obj = {
            "Title": schedule_data.get("title", "AI会议日程"),
            "Description": f"Uos Ai {schedule_data.get('title', 'AI会议日程')}",
            "AllDay": False,
            "Type": 1,
            "Start": schedule_data["start_time"],
            "End": schedule_data["end_time"],
            "Remind": "15"
        }

        # 使用dbus-send调用日历服务创建日程
        try:
            result = dbus_send(
                SERVICES["CALENDAR"]["service"],
                SERVICES["CALENDAR"]["path"],
                SERVICES["CALENDAR"]["interface"],
                "createSchedule",
                json.dumps(schedule_obj)
            )

            logger.info(f"创建日程结果: {result}")
            logger.info(f"创建日程参数: {json.dumps(schedule_obj)}")
            
            if "error" in result.lower():
                logger.error(f"创建日程失败: {result}")
                return f"创建日程失败: {result}"
                
            return f"成功创建日程：{schedule_data.get('title', 'AI会议日程')}"
            
        except Exception as e:
            logger.error(f"调用日历服务失败: {e}")
            return f"创建日程失败: 日历服务不可用"
            
    except Exception as e:
        logger.error(f"创建日程时发生错误: {e}")
        return f"创建日程失败: {str(e)}"

