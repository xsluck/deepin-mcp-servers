import requests
import os
from pathlib import Path
from urllib.parse import urlparse

def _download_file(url: str, download_dir: str = None) -> str:
    try:
        # 检查URL是否合法
        if not url.startswith(('http://', 'https://')):
            return "只支持HTTP/HTTPS协议的下载链接"
            
        # 获取下载目录
        if download_dir is None:
            download_dir = str(Path.home() / 'Downloads')
            
        # 确保下载目录存在
        os.makedirs(download_dir, exist_ok=True)
        
        # 从URL获取文件名
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename:
            filename = 'downloaded_file'
            
        file_path = os.path.join(download_dir, filename)
        
        # 下载文件
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        return f"文件已成功下载到: {file_path}"
        
    except requests.exceptions.RequestException as e:
        return f"下载文件失败: {str(e)}"
    except Exception as e:
        return f"下载文件失败: {str(e)}"