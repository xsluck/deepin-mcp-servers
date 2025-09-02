import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def _is_git_repository(path: str) -> bool:
    """检查指定路径是否为Git仓库"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False

def _git_status(repository_path: str = None) -> str:
    """
    获取Git仓库状态
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: Git状态信息
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not os.path.exists(repository_path):
            return f"错误: 路径不存在: {repository_path}"
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        logger.info(f"获取Git状态: {repository_path}")
        
        result = subprocess.run(
            ["git", "status", "--porcelain", "-b"],
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return f"错误: {result.stderr}"
        
        # 解析状态输出
        lines = result.stdout.strip().split('\n')
        if not lines or lines == ['']:
            return "工作目录干净，没有未提交的更改"
        
        branch_info = lines[0] if lines[0].startswith('##') else "## 未知分支"
        file_changes = [line for line in lines[1:] if line.strip()]
        
        output = [f"分支信息: {branch_info[3:]}"]
        
        if file_changes:
            output.append(f"\n文件更改 ({len(file_changes)} 个文件):")
            for change in file_changes[:20]:  # 限制显示前20个文件
                status = change[:2]
                filename = change[3:]
                status_desc = {
                    'M ': '已修改',
                    ' M': '已修改(未暂存)',
                    'A ': '新增',
                    'D ': '删除',
                    'R ': '重命名',
                    'C ': '复制',
                    '??': '未跟踪',
                    'MM': '已修改(部分暂存)'
                }.get(status, f'状态:{status}')
                output.append(f"  {status_desc}: {filename}")
            
            if len(file_changes) > 20:
                output.append(f"  ... 还有 {len(file_changes) - 20} 个文件")
        
        return '\n'.join(output)
        
    except subprocess.TimeoutExpired:
        return "错误: Git命令执行超时"
    except Exception as e:
        logger.error(f"获取Git状态失败: {e}")
        return f"错误: {str(e)}"

def _git_log(repository_path: str = None, max_commits: int = 10) -> str:
    """
    获取Git提交历史
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        max_commits: 最大显示提交数量 (默认10)
    
    Returns:
        str: Git提交历史
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        logger.info(f"获取Git日志: {repository_path}")
        
        result = subprocess.run([
            "git", "log", 
            f"--max-count={max_commits}",
            "--pretty=format:%h|%an|%ad|%s",
            "--date=short"
        ], cwd=repository_path, capture_output=True, text=True, timeout=15)
        
        if result.returncode != 0:
            return f"错误: {result.stderr}"
        
        if not result.stdout.strip():
            return "没有找到提交历史"
        
        lines = result.stdout.strip().split('\n')
        output = [f"最近 {len(lines)} 次提交:"]
        output.append("-" * 80)
        
        for line in lines:
            parts = line.split('|', 3)
            if len(parts) == 4:
                hash_short, author, date, message = parts
                output.append(f"{hash_short} | {date} | {author}")
                output.append(f"    {message}")
                output.append("")
        
        return '\n'.join(output)
        
    except subprocess.TimeoutExpired:
        return "错误: Git命令执行超时"
    except Exception as e:
        logger.error(f"获取Git日志失败: {e}")
        return f"错误: {str(e)}"

def _git_branch_info(repository_path: str = None) -> str:
    """
    获取Git分支信息
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: Git分支信息
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        logger.info(f"获取Git分支信息: {repository_path}")
        
        # 获取所有分支
        result = subprocess.run([
            "git", "branch", "-a", "-v"
        ], cwd=repository_path, capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            return f"错误: {result.stderr}"
        
        output = ["Git分支信息:"]
        output.append("-" * 50)
        
        lines = result.stdout.strip().split('\n')
        current_branch = None
        
        for line in lines:
            line = line.strip()
            if line.startswith('*'):
                current_branch = line[2:].split()[0]
                output.append(f"当前分支: {current_branch}")
                output.append("")
                break
        
        output.append("所有分支:")
        for line in lines:
            if line.strip():
                output.append(f"  {line}")
        
        return '\n'.join(output)
        
    except subprocess.TimeoutExpired:
        return "错误: Git命令执行超时"
    except Exception as e:
        logger.error(f"获取Git分支信息失败: {e}")
        return f"错误: {str(e)}"

def _git_add_files(repository_path: str = None, files: List[str] = None) -> str:
    """
    添加文件到Git暂存区
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        files: 要添加的文件列表 (可选，默认为所有更改的文件)
    
    Returns:
        str: 操作结果
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        if files is None or len(files) == 0:
            # 添加所有更改的文件
            cmd = ["git", "add", "."]
            logger.info(f"添加所有文件到暂存区: {repository_path}")
        else:
            # 添加指定文件
            cmd = ["git", "add"] + files
            logger.info(f"添加指定文件到暂存区: {files}")
        
        result = subprocess.run(
            cmd,
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return f"错误: {result.stderr}"
        
        # 获取暂存区状态
        status_result = subprocess.run(
            ["git", "status", "--porcelain", "--cached"],
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if status_result.stdout.strip():
            staged_files = status_result.stdout.strip().split('\n')
            return f"成功添加 {len(staged_files)} 个文件到暂存区:\n" + '\n'.join([f"  {f}" for f in staged_files])
        else:
            return "没有文件被添加到暂存区（可能没有更改）"
        
    except subprocess.TimeoutExpired:
        return "错误: Git命令执行超时"
    except Exception as e:
        logger.error(f"添加文件到暂存区失败: {e}")
        return f"错误: {str(e)}"

def _git_commit(repository_path: str = None, message: str = None) -> str:
    """
    提交Git更改
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        message: 提交信息
    
    Returns:
        str: 操作结果
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        if not message or not message.strip():
            return "错误: 提交信息不能为空"
        
        logger.info(f"提交Git更改: {repository_path}")
        
        result = subprocess.run([
            "git", "commit", "-m", message.strip()
        ], cwd=repository_path, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            if "nothing to commit" in result.stdout:
                return "没有需要提交的更改"
            return f"错误: {result.stderr}"
        
        return f"提交成功!\n{result.stdout}"
        
    except subprocess.TimeoutExpired:
        return "错误: Git命令执行超时"
    except Exception as e:
        logger.error(f"Git提交失败: {e}")
        return f"错误: {str(e)}"

def _git_pull(repository_path: str = None) -> str:
    """
    拉取远程更改
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: 操作结果
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        logger.info(f"拉取远程更改: {repository_path}")
        
        result = subprocess.run([
            "git", "pull"
        ], cwd=repository_path, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return f"拉取失败: {result.stderr}"
        
        return f"拉取成功!\n{result.stdout}"
        
    except subprocess.TimeoutExpired:
        return "错误: Git命令执行超时"
    except Exception as e:
        logger.error(f"Git拉取失败: {e}")
        return f"错误: {str(e)}"

def _git_push(repository_path: str = None) -> str:
    """
    推送到远程仓库
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
    
    Returns:
        str: 操作结果
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        logger.info(f"推送到远程仓库: {repository_path}")
        
        result = subprocess.run([
            "git", "push"
        ], cwd=repository_path, capture_output=True, text=True, timeout=60)
        
        if result.returncode != 0:
            return f"推送失败: {result.stderr}"
        
        return f"推送成功!\n{result.stdout}"
        
    except subprocess.TimeoutExpired:
        return "错误: Git命令执行超时"
    except Exception as e:
        logger.error(f"Git推送失败: {e}")
        return f"错误: {str(e)}"

def _git_clone(repository_url: str, target_directory: str = None) -> str:
    """
    克隆Git仓库
    
    Args:
        repository_url: Git仓库URL
        target_directory: 目标目录 (可选)
    
    Returns:
        str: 操作结果
    """
    try:
        if not repository_url or not repository_url.strip():
            return "错误: 仓库URL不能为空"
        
        cmd = ["git", "clone", repository_url.strip()]
        if target_directory and target_directory.strip():
            cmd.append(target_directory.strip())
        
        logger.info(f"克隆Git仓库: {repository_url}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        if result.returncode != 0:
            return f"克隆失败: {result.stderr}"
        
        return f"克隆成功!\n{result.stdout}"
        
    except subprocess.TimeoutExpired:
        return "错误: Git克隆超时（5分钟）"
    except Exception as e:
        logger.error(f"Git克隆失败: {e}")
        return f"错误: {str(e)}"

def _git_diff(repository_path: str = None, file_path: str = None, staged: bool = False) -> str:
    """
    查看Git差异内容
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        file_path: 特定文件路径 (可选，默认查看所有文件)
        staged: 是否查看暂存区差异 (默认False，查看工作区差异)
    
    Returns:
        str: Git差异内容
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        # 构建git diff命令
        cmd = ["git", "diff"]
        
        if staged:
            cmd.append("--cached")
        
        if file_path:
            cmd.append(file_path)
        
        logger.info(f"查看Git差异: {repository_path}, 文件: {file_path or '所有'}, 暂存区: {staged}")
        
        result = subprocess.run(
            cmd,
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return f"错误: {result.stderr}"
        
        if not result.stdout.strip():
            if staged:
                return "暂存区没有差异"
            else:
                return "工作区没有差异"
        
        # 格式化输出
        diff_content = result.stdout
        
        # 添加头部信息
        output = []
        if staged:
            output.append("=== 暂存区差异 ===")
        else:
            output.append("=== 工作区差异 ===")
        
        if file_path:
            output.append(f"文件: {file_path}")
        else:
            output.append("所有文件的差异")
        
        output.append("-" * 60)
        output.append(diff_content)
        
        return '\n'.join(output)
        
    except subprocess.TimeoutExpired:
        return "错误: Git差异查看超时"
    except Exception as e:
        logger.error(f"查看Git差异失败: {e}")
        return f"错误: {str(e)}"

def _git_show_commit(repository_path: str = None, commit_hash: str = None) -> str:
    """
    查看特定提交的详细信息和修改内容
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        commit_hash: 提交哈希值 (可选，默认为最新提交)
    
    Returns:
        str: 提交详细信息
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        # 构建git show命令
        cmd = ["git", "show"]
        
        if commit_hash:
            cmd.append(commit_hash)
        
        logger.info(f"查看Git提交详情: {repository_path}, 提交: {commit_hash or '最新'}")
        
        result = subprocess.run(
            cmd,
            cwd=repository_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return f"错误: {result.stderr}"
        
        if not result.stdout.strip():
            return "没有找到提交信息"
        
        # 格式化输出
        output = []
        output.append("=== Git提交详细信息 ===")
        if commit_hash:
            output.append(f"提交哈希: {commit_hash}")
        else:
            output.append("最新提交")
        output.append("-" * 60)
        output.append(result.stdout)
        
        return '\n'.join(output)
        
    except subprocess.TimeoutExpired:
        return "错误: Git提交查看超时"
    except Exception as e:
        logger.error(f"查看Git提交失败: {e}")
        return f"错误: {str(e)}"

def _git_file_history(repository_path: str = None, file_path: str = None, max_commits: int = 10) -> str:
    """
    查看特定文件的修改历史
    
    Args:
        repository_path: Git仓库路径 (可选，默认为当前目录)
        file_path: 文件路径 (必需)
        max_commits: 最大显示提交数量 (默认10)
    
    Returns:
        str: 文件修改历史
    """
    try:
        if repository_path is None:
            repository_path = os.getcwd()
        
        if not _is_git_repository(repository_path):
            return f"错误: {repository_path} 不是一个Git仓库"
        
        if not file_path:
            return "错误: 必须指定文件路径"
        
        logger.info(f"查看文件修改历史: {file_path}")
        
        # 获取文件的提交历史
        result = subprocess.run([
            "git", "log",
            f"--max-count={max_commits}",
            "--pretty=format:%h|%an|%ad|%s",
            "--date=short",
            "--follow",  # 跟踪文件重命名
            "--", file_path
        ], cwd=repository_path, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return f"错误: {result.stderr}"
        
        if not result.stdout.strip():
            return f"文件 {file_path} 没有找到修改历史"
        
        lines = result.stdout.strip().split('\n')
        output = [f"文件 {file_path} 的修改历史 (最近 {len(lines)} 次):"]
        output.append("=" * 80)
        
        for line in lines:
            parts = line.split('|', 3)
            if len(parts) == 4:
                hash_short, author, date, message = parts
                output.append(f"{hash_short} | {date} | {author}")
                output.append(f"    {message}")
                output.append("")
        
        return '\n'.join(output)
        
    except subprocess.TimeoutExpired:
        return "错误: Git文件历史查看超时"
    except Exception as e:
        logger.error(f"查看Git文件历史失败: {e}")
        return f"错误: {str(e)}" 