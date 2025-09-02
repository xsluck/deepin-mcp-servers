"""
Deepin MCP Server implementation.
"""

# Standard library imports
import json
import logging
import os
import subprocess
from typing import Any
from pathlib import Path
from urllib.parse import urlparse

# 第三方库
from mcp.server.fastmcp import FastMCP

# Local imports
from dbus_service.services import dbus_send, dbus_get_property, dbus_set_property, show_confirmation_dialog, show_notification
from web_service.services import _web_search, _fetch_web_content
from web_service.utils import _download_file
from system_tools.system_control import (
    _switch_wallpaper, 
    _switch_dock_mode, 
    _set_do_not_disturb, 
    _switch_system_theme, 
    _get_system_memory, 
    _send_mail,
    _create_schedule,
)
from system_tools.terminal_command import _execute_terminal_command
from system_tools.git_operations import (
    _git_status,
    _git_log,
    _git_branch_info,
    _git_add_files,
    _git_commit,
    _git_pull,
    _git_push,
    _git_clone,
    _git_diff,
    _git_show_commit,
    _git_file_history,
)
from system_tools.file_operation import (
    _open_file,
    _copy_file,
    _move_file,
    _rename_file,
    _delete_file,
    _create_file,
    _create_folder,
    _batch_rename,
    _list_dir,
    _read_document,
    _get_files_size,
)

# Configure logging
logger = logging.getLogger(__name__)
# 设置日志级别
logger.setLevel(logging.INFO)

# 创建文件处理器
log_file = os.path.join(os.path.expanduser("~"), ".local/share/deepin-mcp-server/deepin-mcp-server.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加处理器到logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# 初始化服务器
mcp = FastMCP("deepin-mcp-servers")

@mcp.tool()
async def launch_app(app_name: str) -> str:
    """
    Name: 
        打开应用

    Description: 
        打开、启动、运行某个应用

    Args:
        app_name: 应用名称，例如：dde-calendar, dde-printer.
        应用名称列表：dde-calendar 日历,dde-computer 我的电脑,dde-cooperation 跨端协同,dde-file-manager 文件管理器,dde-introduction 欢迎,dde-printer 打印机管理器,dde-trash 回收站,deepin-album 相册,deepin-app-store 应用商店,deepin-calculator 计算器,deepin-camera 相机,deepin-compressor 归档管理器,deepin-deb-installer 软件包安装器,deepin-devicemanager 设备管理器,deepin-diskmanager 磁盘管理器,deepin-draw 画图,deepin-editor 文本编辑器,deepin-font-manager 字体管理器,deepin-gomoku 五子棋,deepin-image-viewer 看图,deepin-lianliankan 连连看,deepin-log-viewer 日志收集工具,deepin-mail 邮箱,deepin-manual 帮助手册,deepin-movie 影院,deepin-music 音乐,deepin-picker 取色器,deepin-reader 文档查看器,deepin-screen-recorder 截图录屏,deepin-system-monitor 系统监视器,deepin-terminal 终端,deepin-voice-note 语音记事本,downloader 下载器,dummyapp-wpsoffice wps,onboard 虚拟键盘,org.deepin.browser 浏览器,org.deepin.dde.control-center 控制中心,uos-ai-assistant UOSAI助手
    """
    try:
        try:
        # 使用dde-am启动应用
            subprocess.run(["dde-am", app_name], check=True)
            return f"成功启动应用 {app_name}"
        except Exception as e:
            logger.error(f"dde-am启动应用失败: {e}")
            return f"启动应用 {app_name} 失败"
                
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return f"操作失败: {str(e)}"

@mcp.tool()
async def send_mail(email_data: dict) -> str:
    """
    Name: 
        发送邮件

    Description: 
        通过用户输入发送邮件。输入是一个包含邮件详情的字典对象。

    Args:
        email_data: 包含邮件详情的字典对象，格式如下：
            {
                "subject": "邮件主题",
                "content": "邮件正文",
                "to": "收件人1,收件人2",
                "cc": "抄送1,抄送2",
                "bcc": "密送1,密送2"
            }
    """
    return _send_mail(email_data)

@mcp.tool()
async def create_schedule(schedule_data: dict) -> str:
    """
    Name:
        创建日程

    Description:
        创建一个新的日程安排，支持设置标题、开始时间、结束时间等。

    Args:
        schedule_data: 包含日程详情的字典对象，格式如下：
            {
                "title": "日程标题",
                "start_time": "开始时间 (格式: yyyy-MM-ddThh:mm:ss)",
                "end_time": "结束时间 (格式: yyyy-MM-ddThh:mm:ss)"
            }
    """
    return _create_schedule(schedule_data)

@mcp.tool()
async def switch_wallpaper(file_url: str = None) -> str:
    """
    Name: 
        Switch Wallpaper

    Description: 
        Switch to the next wallpaper in the wallpaper list or use specific wallpaper.

    Args:
        file_url: (optional) The wallpaper file path to use directly. If provided, this file will be used as wallpaper directly.
    """
    return _switch_wallpaper(file_url)

@mcp.tool()
async def dock_mode_switch(mode: int) -> str:
    """
    Name: 
        Switch Dock Mode

    Description: 
        Switch the dock display mode.

    Args:
        mode: The dock display mode to switch to (0 for Fashion mode, 1 for Efficient mode)
    """
    return _switch_dock_mode(mode)

@mcp.tool()
async def no_disturb(state: bool) -> str:
    """
    Name: 
        No Disturb

    Description: 
        Enable or disable the do not disturb mode.

    Args:
        state: True to enable do not disturb mode, False to disable it
    """
    return _set_do_not_disturb(state)

@mcp.tool()
async def system_theme_switch(theme: int) -> str:
    """
    Name: 
        System Theme Switch

    Description: 
        Switch the system theme. 

    Args:
        theme: The theme to switch to (0 for deepin, 1 for deepin-dark, 2 for deepin-auto)
    """
    return _switch_system_theme(theme)

@mcp.tool()
async def get_system_memory() -> str:
    """
    Name: 
        获取系统硬件信息

    Description: 
        获取系统的CPU型号、内存大小和硬盘信息

    Args:
        None
    """
    return _get_system_memory()

@mcp.tool()
async def open_file(file_path: str) -> str:
    """
    使用系统默认程序打开文件
    
    Args:
        file_path: 文件路径
    """
    return _open_file(file_path)

@mcp.tool()
async def copy_file(source_path: str, destination_path: str) -> str:
    """
    Name:
        复制文件

    Description:
        复制原文件到目标位置
    
    Args:
        source_path: 源文件路径
        destination_path: 目标文件路径
    """
    return _copy_file(source_path, destination_path)

@mcp.tool()
async def move_file(source_path: str, destination_path: str) -> str:
    """
    Name:
        移动文件

    Description:
        移动原文件到目标位置
    
    Args:
        source_path: 源文件路径
        destination_path: 目标文件路径
    """
    return _move_file(source_path, destination_path)

@mcp.tool()
async def rename_file(old_path: str, new_name: str) -> str:
    """
    Name:
        重命名文件

    Description:
        重命名文件
    
    Args:
        old_path: 原文件路径
        new_name: 新文件名
    """
    return _rename_file(old_path, new_name)

@mcp.tool()
async def delete_file(file_path: str) -> str:
    """
    Name:
        删除文件

    Description:
        删除指定文件
    
    Args:
        file_path: 要删除的文件路径
    """
    return _delete_file(file_path)

@mcp.tool()
async def create_file(file_path: str, content: str = "") -> str:
    """
    Name:
        创建新文件

    Description:
        根据文件路径创建新文件，并写入初始内容
    
    Args:
        file_path: 新文件路径
        content: 文件初始内容（可选）
    """
    return _create_file(file_path, content)

@mcp.tool()
async def create_folder(folder_path: str) -> str:
    """
    Name:
        创建新文件夹

    Description:
        根据文件夹路径创建新文件夹
    
    Args:
        folder_path: 新文件夹路径
    """
    return _create_folder(folder_path)

@mcp.tool()
async def batch_rename(folder_path: str, new_name: str) -> str:
    """
    Name:
        批量重命名

    Description:
        批量重命名文件夹下的所有文件
        
    Args:
        folder_path: 文件夹路径
        new_name: 新文件名
    """
    return _batch_rename(folder_path, new_name)

@mcp.tool()
async def list_dir(folder_path: str, recursive: bool = False) -> str:
    """
    Name:
        查询文件列表

    Description:
        查询指定文件夹下的文件列表
    
    Args:
        folder_path: 文件夹路径
        recursive: 递归查询子文件夹(default: False)
    """
    return _list_dir(folder_path, recursive)

@mcp.tool()
async def read_document(document_path: str) -> str:
    """
    Name:
        读取文档

    Description:
        读取文档内容，支持txt、md、doc、docx、pdf、xls、xlsx、ppt、pptx等格式。
    
    Args:
        document_path: 文档路径
    """
    return _read_document(document_path)

@mcp.tool()
async def download_file(url: str, download_dir: str = None) -> str:
    """
    Name:
        下载文件

    Description:
        从HTTP/HTTPS链接下载文件到指定目录
    
    Args:
        url: 文件下载链接 (必须以http://或https://开头)
        download_dir: 下载目录 (可选，默认为用户下载目录)
    """
    return _download_file(url, download_dir)

@mcp.tool()
async def user_directory() -> str:
    """
    Name:
        获取用户目录

    Description:
        获取用户目录
    """
    return str(Path.home())

@mcp.tool()
async def get_files_size(file_paths: list[str]) -> str:
    """
    Name:
        获取多个文件大小

    Description:
        获取多个文件大小
    
    Args:
        file_paths: 文件路径列表
    """
    return _get_files_size(file_paths)

@mcp.tool()
async def web_search(query: str) -> str:
    """
    Name:
    Web search

    Description:
        Search content on web.
    
    Args:
        query: Search keywords
    """
    return _web_search(query)

@mcp.tool()
async def fetch_web_content(url):
    """
    Name:
        Fetch web page

    Description:
        Fetch a URL and extract its contents as markdown.

    Args:
        url: URL of the web page to fetch

    Returns:
        str: Extracted main content of the page
    """
    return _fetch_web_content(url)

@mcp.tool()
async def execute_terminal_command(command: str, working_directory: str = None, timeout: int = 30, confirm_dialog: bool = True) -> str:
    """
    Name:
        执行终端命令

    Description:
        在终端中执行指定的命令，支持大部分常用的Linux命令。为了系统安全，会拒绝执行危险命令。
        对于风险命令会弹出确认对话框，执行完成后会显示系统通知。

    Args:
        command: 要执行的终端命令
        working_directory: 工作目录 (可选，默认为用户主目录)
        timeout: 超时时间，单位秒 (默认30秒，最大120秒)
        confirm_dialog: 是否显示确认对话框 (默认True，风险命令会弹窗确认)
    
    Returns:
        str: 命令执行结果，包括标准输出、错误输出和退出代码
    """
    # 限制最大超时时间
    if timeout > 120:
        timeout = 120
    
    return _execute_terminal_command(command, working_directory, timeout, confirm_dialog)

@mcp.tool()
async def git_status(repository_path: str = None) -> str:
    """
    Name:
        Git状态查询

    Description:
        获取Git仓库的当前状态，包括分支信息、文件更改状态等。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: Git仓库状态信息
    """
    return _git_status(repository_path)

@mcp.tool()
async def git_log(repository_path: str = None, max_commits: int = 10) -> str:
    """
    Name:
        Git提交历史

    Description:
        获取Git仓库的提交历史记录。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        max_commits: 最大显示提交数量 (默认10，最大50)
    
    Returns:
        str: Git提交历史
    """
    # 限制最大提交数量
    if max_commits > 50:
        max_commits = 50
    
    return _git_log(repository_path, max_commits)

@mcp.tool()
async def git_branch_info(repository_path: str = None) -> str:
    """
    Name:
        Git分支信息

    Description:
        获取Git仓库的分支信息，包括当前分支和所有分支列表。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: Git分支信息
    """
    return _git_branch_info(repository_path)

@mcp.tool()
async def git_add_files(repository_path: str = None, files: list[str] = None) -> str:
    """
    Name:
        Git添加文件

    Description:
        将文件添加到Git暂存区。如果不指定文件，则添加所有更改的文件。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        files: 要添加的文件列表 (可选，默认为所有更改的文件)
    
    Returns:
        str: 操作结果
    """
    return _git_add_files(repository_path, files)

@mcp.tool()
async def git_commit(repository_path: str = None, message: str = None) -> str:
    """
    Name:
        Git提交更改

    Description:
        提交暂存区的更改到Git仓库。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        message: 提交信息 (必需)
    
    Returns:
        str: 操作结果
    """
    return _git_commit(repository_path, message)

@mcp.tool()
async def git_pull(repository_path: str = None) -> str:
    """
    Name:
        Git拉取更新

    Description:
        从远程仓库拉取最新的更改。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: 操作结果
    """
    return _git_pull(repository_path)

@mcp.tool()
async def git_push(repository_path: str = None) -> str:
    """
    Name:
        Git推送更改

    Description:
        将本地提交推送到远程仓库。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: 操作结果
    """
    return _git_push(repository_path)

@mcp.tool()
async def git_clone(repository_url: str, target_directory: str = None) -> str:
    """
    Name:
        Git克隆仓库

    Description:
        从远程URL克隆Git仓库到本地。

    Args:
        repository_url: Git仓库URL (必需)
        target_directory: 目标目录 (可选)
    
    Returns:
        str: 操作结果
    """
    return _git_clone(repository_url, target_directory)

@mcp.tool()
async def git_diff(repository_path: str = None, file_path: str = None, staged: bool = False) -> str:
    """
    Name:
        Git差异查看

    Description:
        查看Git仓库中文件的修改差异。可以查看工作区或暂存区的差异，AI可以分析具体的代码修改内容。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        file_path: 特定文件路径 (可选，默认查看所有文件)
        staged: 是否查看暂存区差异 (默认False，查看工作区差异)
    
    Returns:
        str: Git差异内容，包含具体的代码修改
    """
    return _git_diff(repository_path, file_path, staged)

@mcp.tool()
async def git_show_commit(repository_path: str = None, commit_hash: str = None) -> str:
    """
    Name:
        Git提交详情

    Description:
        查看特定Git提交的详细信息和修改内容。AI可以分析提交中的具体代码更改。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        commit_hash: 提交哈希值 (可选，默认为最新提交)
    
    Returns:
        str: 提交的详细信息和代码修改内容
    """
    return _git_show_commit(repository_path, commit_hash)

@mcp.tool()
async def git_file_history(repository_path: str = None, file_path: str = None, max_commits: int = 10) -> str:
    """
    Name:
        Git文件历史

    Description:
        查看特定文件的Git修改历史记录。AI可以了解文件的演变过程。

    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        file_path: 文件路径 (必需)
        max_commits: 最大显示提交数量 (默认10，最大30)
    
    Returns:
        str: 文件的修改历史记录
    """
    # 限制最大提交数量
    if max_commits > 30:
        max_commits = 30
    
    return _git_file_history(repository_path, file_path, max_commits)

@mcp.tool()
async def show_dialog(title: str, message: str, timeout: int = 30) -> str:
    """
    Name:
        显示确认对话框

    Description:
        显示一个确认对话框，用户可以选择"是"或"否"。适用于需要用户确认的操作。

    Args:
        title: 对话框标题
        message: 对话框消息内容
        timeout: 超时时间，单位秒 (默认10秒，最大15秒)
    
    Returns:
        str: 用户选择结果
    """
    # 限制最大超时时间
    if timeout > 15:
        timeout = 15
    
    try:
        result = show_confirmation_dialog(title, message, timeout)
        if result:
            return "用户选择了：是"
        else:
            return "用户选择了：否 (或超时)"
    except Exception as e:
        return f"对话框显示失败: {str(e)}"

@mcp.tool()
async def send_notification(title: str, message: str, icon: str = "dialog-information", timeout: int = 5000) -> str:
    """
    Name:
        发送系统通知

    Description:
        发送系统桌面通知消息，用于提醒用户重要信息。

    Args:
        title: 通知标题
        message: 通知消息内容
        icon: 通知图标 (可选: dialog-information, dialog-warning, dialog-error)
        timeout: 显示时间，单位毫秒 (默认5000毫秒，最大30000毫秒)
    
    Returns:
        str: 通知发送结果
    """
    # 限制最大显示时间
    if timeout > 30000:
        timeout = 30000
    
    return show_notification(title, message, icon, timeout)


if __name__ == "__main__":
    # 设置D-Bus环境变量
    if not os.getenv("DBUS_SESSION_BUS_ADDRESS"):
        os.environ.update({"DBUS_SESSION_BUS_ADDRESS": f"unix:path=/run/user/{os.getuid()}/bus"})
        
    #Initialize and run the server
    mcp.run(transport='stdio')