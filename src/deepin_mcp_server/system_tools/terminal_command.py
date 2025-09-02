import os
import subprocess
import logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from dbus_service.services import show_confirmation_dialog, show_notification

# Configure logging
logger = logging.getLogger(__name__)

def _execute_terminal_command(command: str, working_directory: str = None, timeout: int = 30, confirm_dialog: bool = True) -> str:
    """
    执行终端命令
    
    Args:
        command: 要执行的命令
        working_directory: 工作目录 (可选，默认为用户主目录)
        timeout: 超时时间，单位秒 (默认30秒)
        confirm_dialog: 是否显示确认对话框 (默认True)
    
    Returns:
        str: 命令执行结果
    """
    try:
        # 安全检查：禁止执行危险命令
        dangerous_commands = [
            'rm -rf /', 'rm -rf /*', 'mkfs', 'dd if=', 'format', 
            'fdisk', 'parted', 'shutdown', 'reboot', 'halt',
            'passwd', 'su -', 'sudo su', 'chmod 777 /', 'chown -R',
            'init 0', 'init 6', 'systemctl poweroff', 'systemctl reboot'
        ]
        
        command_lower = command.lower().strip()
        for dangerous in dangerous_commands:
            if dangerous in command_lower:
                logger.warning(f"拒绝执行危险命令: {command}")
                return f"错误: 拒绝执行危险命令，为了系统安全"
        
        # 显示确认对话框（如果启用）
        if confirm_dialog:
            # 检查是否为可能有风险的命令
            risky_patterns = ['rm ', 'mv ', 'cp ', 'chmod', 'chown', 'sudo', 'su ', 'git push', 'git reset --hard']
            is_risky = any(pattern in command_lower for pattern in risky_patterns)
            
            if is_risky or len(command) > 50:  # 长命令或风险命令需要确认
                dialog_title = "终端命令执行确认"
                dialog_message = f"即将执行以下命令:\n\n{command}\n\n工作目录: {working_directory or '用户主目录'}\n\n是否继续执行？"
                
                try:
                    user_confirmed = show_confirmation_dialog(dialog_title, dialog_message, 30)
                    if not user_confirmed:
                        show_notification("命令取消", f"用户取消了命令执行: {command[:50]}...", "dialog-warning")
                        return "用户取消了命令执行"
                except Exception as e:
                    logger.warning(f"对话框显示失败，继续执行命令: {e}")
                    # 如果对话框失败，发送通知并继续执行
                    show_notification("命令执行", f"正在执行: {command[:30]}...", "dialog-information")
        
        # 设置工作目录
        if working_directory is None:
            working_directory = os.path.expanduser("~")
        
        # 验证工作目录是否存在
        if not os.path.exists(working_directory):
            return f"错误: 工作目录不存在: {working_directory}"
        
        if not os.path.isdir(working_directory):
            return f"错误: 指定的路径不是目录: {working_directory}"
        
        logger.info(f"执行命令: {command}")
        logger.info(f"工作目录: {working_directory}")
        
        # 使用shell=True来支持管道、重定向等shell功能
        # 但要确保命令是安全的
        result = subprocess.run(
            command,
            shell=True,
            cwd=working_directory,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy()
        )
        
        # 构建返回结果
        output_parts = []
        
        if result.stdout:
            output_parts.append(f"标准输出:\n{result.stdout}")
        
        if result.stderr:
            output_parts.append(f"错误输出:\n{result.stderr}")
        
        if result.returncode != 0:
            output_parts.append(f"退出代码: {result.returncode}")
        
        if not output_parts:
            output_parts.append("命令执行完成，无输出")
        
        final_output = "\n\n".join(output_parts)
        
        logger.info(f"命令执行完成，退出代码: {result.returncode}")
        
        # 发送执行完成通知
        if result.returncode == 0:
            show_notification("命令执行成功", f"命令执行完成: {command[:30]}...", "dialog-information")
        else:
            show_notification("命令执行失败", f"命令执行失败 (退出代码: {result.returncode})", "dialog-error")
        
        return final_output
        
    except subprocess.TimeoutExpired:
        logger.error(f"命令执行超时: {command}")
        return f"错误: 命令执行超时 ({timeout}秒)"
    
    except subprocess.CalledProcessError as e:
        logger.error(f"命令执行失败: {e}")
        return f"错误: 命令执行失败，退出代码: {e.returncode}\n输出: {e.output}"
    
    except Exception as e:
        logger.error(f"执行命令时发生错误: {e}")
        return f"错误: {str(e)}" 