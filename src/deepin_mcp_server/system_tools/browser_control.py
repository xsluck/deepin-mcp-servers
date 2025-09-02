"""
浏览器控制模块
支持自动化浏览器操作来完成各种任务
"""

import os
import time
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.chrome.service import Service as ChromeService
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

import requests
import zipfile
import platform
import stat

# Configure logging
logger = logging.getLogger(__name__)

def _get_chrome_version():
    """获取Chrome浏览器版本"""
    try:
        # 尝试不同的Chrome命令
        chrome_commands = ['google-chrome', 'chromium-browser', 'chrome']
        
        for cmd in chrome_commands:
            try:
                result = subprocess.run([cmd, '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    # 提取版本号，例如: "Google Chrome 139.0.7258.138" -> "139.0.7258.138"
                    version_line = result.stdout.strip()
                    version = version_line.split()[-1]
                    # 只取主版本号，例如: "139.0.7258.138" -> "139"
                    major_version = version.split('.')[0]
                    logger.info(f"检测到Chrome版本: {version} (主版本: {major_version})")
                    return major_version
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        logger.warning("无法检测Chrome版本")
        return None
    except Exception as e:
        logger.error(f"获取Chrome版本失败: {e}")
        return None

def _download_chromedriver(version=None):
    """自动下载ChromeDriver"""
    try:
        # 创建ChromeDriver存储目录
        driver_dir = Path.home() / ".local/share/deepin-mcp-server/drivers"
        driver_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果没有指定版本，尝试获取Chrome版本
        if not version:
            version = _get_chrome_version()
            if not version:
                logger.error("无法获取Chrome版本，无法下载匹配的ChromeDriver")
                return None
        
        # ChromeDriver文件路径
        if platform.system() == "Windows":
            driver_filename = "chromedriver.exe"
        else:
            driver_filename = "chromedriver"
        
        driver_path = driver_dir / driver_filename
        
        # 如果已存在且可执行，直接返回
        if driver_path.exists() and os.access(driver_path, os.X_OK):
            logger.info(f"使用现有的ChromeDriver: {driver_path}")
            return str(driver_path)
        
        logger.info(f"正在下载ChromeDriver版本 {version}...")
        
        # 构建下载URL
        system = platform.system().lower()
        if system == "linux":
            if platform.machine() == "x86_64":
                platform_name = "linux64"
            else:
                platform_name = "linux32"
        elif system == "darwin":
            platform_name = "mac64"
        elif system == "windows":
            platform_name = "win32"
        else:
            logger.error(f"不支持的操作系统: {system}")
            return None
        
        # ChromeDriver下载URL (使用新的API)
        # 对于Chrome 115+，使用新的下载地址
        try:
            # 首先尝试获取最新版本信息
            api_url = f"https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            response = requests.get(api_url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # 查找匹配的版本
                matching_version = None
                for version_info in data.get('versions', []):
                    if version_info['version'].startswith(version + '.'):
                        matching_version = version_info
                        break
                
                if matching_version:
                    # 查找对应平台的下载链接
                    downloads = matching_version.get('downloads', {})
                    chromedriver_downloads = downloads.get('chromedriver', [])
                    
                    download_url = None
                    for download in chromedriver_downloads:
                        if download['platform'] == platform_name:
                            download_url = download['url']
                            break
                    
                    if download_url:
                        logger.info(f"找到ChromeDriver下载链接: {download_url}")
                    else:
                        logger.warning(f"未找到平台 {platform_name} 的下载链接")
                        # 回退到旧的下载方式
                        download_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version}"
                        response = requests.get(download_url, timeout=10)
                        if response.status_code == 200:
                            exact_version = response.text.strip()
                            download_url = f"https://chromedriver.storage.googleapis.com/{exact_version}/chromedriver_{platform_name}.zip"
                        else:
                            raise Exception("无法获取ChromeDriver版本信息")
                else:
                    logger.warning(f"未找到Chrome版本 {version} 对应的ChromeDriver")
                    # 使用最新版本
                    if data.get('versions'):
                        latest_version = data['versions'][-1]
                        downloads = latest_version.get('downloads', {})
                        chromedriver_downloads = downloads.get('chromedriver', [])
                        
                        for download in chromedriver_downloads:
                            if download['platform'] == platform_name:
                                download_url = download['url']
                                break
                    
                    if not download_url:
                        raise Exception("无法找到合适的ChromeDriver版本")
            else:
                raise Exception(f"无法访问ChromeDriver API: {response.status_code}")
        
        except Exception as e:
            logger.warning(f"使用新API失败，尝试旧方式: {e}")
            # 回退到旧的下载方式
            try:
                version_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{version}"
                response = requests.get(version_url, timeout=10)
                if response.status_code == 200:
                    exact_version = response.text.strip()
                    download_url = f"https://chromedriver.storage.googleapis.com/{exact_version}/chromedriver_{platform_name}.zip"
                else:
                    # 如果特定版本不存在，尝试获取最新版本
                    latest_url = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE"
                    response = requests.get(latest_url, timeout=10)
                    if response.status_code == 200:
                        exact_version = response.text.strip()
                        download_url = f"https://chromedriver.storage.googleapis.com/{exact_version}/chromedriver_{platform_name}.zip"
                    else:
                        raise Exception("无法获取ChromeDriver版本信息")
            except Exception as e2:
                logger.error(f"下载ChromeDriver失败: {e2}")
                return None
        
        # 下载ChromeDriver
        logger.info(f"正在从 {download_url} 下载ChromeDriver...")
        response = requests.get(download_url, timeout=60)
        response.raise_for_status()
        
        # 保存zip文件
        zip_path = driver_dir / "chromedriver.zip"
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        # 解压文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(driver_dir)
        
        # 删除zip文件
        zip_path.unlink()
        
        # 查找解压后的chromedriver文件
        for root, dirs, files in os.walk(driver_dir):
            for file in files:
                if file == driver_filename or file.startswith('chromedriver'):
                    extracted_path = Path(root) / file
                    # 移动到标准位置
                    if extracted_path != driver_path:
                        extracted_path.rename(driver_path)
                    break
        
        # 设置执行权限
        if driver_path.exists():
            driver_path.chmod(driver_path.stat().st_mode | stat.S_IEXEC)
            logger.info(f"ChromeDriver下载完成: {driver_path}")
            return str(driver_path)
        else:
            logger.error("ChromeDriver下载后未找到文件")
            return None
            
    except Exception as e:
        logger.error(f"下载ChromeDriver失败: {e}")
        return None

class BrowserController:
    """浏览器控制器类"""
    
    def __init__(self, browser_type: str = "chrome", headless: bool = False):
        self.browser_type = browser_type.lower()
        self.headless = headless
        self.driver = None
        self.wait = None
        
    def _setup_chrome_driver(self) -> webdriver.Chrome:
        """设置Chrome驱动"""
        options = ChromeOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        # 添加常用选项
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 禁用通知和其他干扰
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.managed_default_content_settings.images": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        # 尝试不同的ChromeDriver获取方式
        service = None
        
        # 方法1: 检查系统PATH中是否有chromedriver
        try:
            result = subprocess.run(['which', 'chromedriver'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                chromedriver_path = result.stdout.strip()
                logger.info(f"使用系统ChromeDriver: {chromedriver_path}")
                service = ChromeService(chromedriver_path)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # 方法2: 尝试使用webdriver-manager自动管理
        if not service and WEBDRIVER_MANAGER_AVAILABLE:
            try:
                logger.info("使用webdriver-manager自动管理ChromeDriver...")
                chromedriver_path = ChromeDriverManager().install()
                service = ChromeService(chromedriver_path)
                logger.info(f"webdriver-manager获取ChromeDriver: {chromedriver_path}")
            except Exception as e:
                logger.warning(f"webdriver-manager失败: {e}")
        
        # 方法3: 自动下载ChromeDriver
        if not service:
            logger.info("尝试自动下载ChromeDriver...")
            chromedriver_path = _download_chromedriver()
            if chromedriver_path:
                service = ChromeService(chromedriver_path)
                logger.info(f"自动下载ChromeDriver: {chromedriver_path}")
        
        # 方法4: 使用默认方式（让selenium自己处理）
        if service:
            return webdriver.Chrome(service=service, options=options)
        else:
            logger.info("使用默认ChromeDriver配置...")
            return webdriver.Chrome(options=options)
    
    def _setup_firefox_driver(self) -> webdriver.Firefox:
        """设置Firefox驱动"""
        options = FirefoxOptions()
        
        if self.headless:
            options.add_argument("--headless")
        
        # 设置用户代理
        options.set_preference("general.useragent.override", 
                             "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0")
        
        # 禁用通知
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("dom.push.enabled", False)
        
        return webdriver.Firefox(options=options)
    
    def start_browser(self) -> bool:
        """启动浏览器"""
        try:
            if not SELENIUM_AVAILABLE:
                raise ImportError("Selenium未安装，请运行: pip install selenium")
            
            if self.browser_type == "chrome":
                self.driver = self._setup_chrome_driver()
            elif self.browser_type == "firefox":
                self.driver = self._setup_firefox_driver()
            else:
                raise ValueError(f"不支持的浏览器类型: {self.browser_type}")
            
            self.wait = WebDriverWait(self.driver, 10)
            logger.info(f"成功启动{self.browser_type}浏览器")
            return True
            
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}")
            return False
    
    def close_browser(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器时出错: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def navigate_to(self, url: str) -> bool:
        """导航到指定URL"""
        try:
            if not self.driver:
                raise RuntimeError("浏览器未启动")
            
            self.driver.get(url)
            logger.info(f"成功导航到: {url}")
            return True
            
        except Exception as e:
            logger.error(f"导航失败: {e}")
            return False
    
    def find_element(self, selector: str, by_type: str = "css") -> Any:
        """查找页面元素"""
        try:
            if by_type.lower() == "css":
                return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            elif by_type.lower() == "xpath":
                return self.wait.until(EC.presence_of_element_located((By.XPATH, selector)))
            elif by_type.lower() == "id":
                return self.wait.until(EC.presence_of_element_located((By.ID, selector)))
            elif by_type.lower() == "class":
                return self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, selector)))
            elif by_type.lower() == "tag":
                return self.wait.until(EC.presence_of_element_located((By.TAG_NAME, selector)))
            else:
                raise ValueError(f"不支持的选择器类型: {by_type}")
                
        except TimeoutException:
            logger.error(f"未找到元素: {selector}")
            return None
        except Exception as e:
            logger.error(f"查找元素时出错: {e}")
            return None
    
    def click_element(self, selector: str, by_type: str = "css") -> bool:
        """点击页面元素"""
        try:
            element = self.find_element(selector, by_type)
            if element:
                # 等待元素可点击
                clickable_element = self.wait.until(EC.element_to_be_clickable(element))
                clickable_element.click()
                logger.info(f"成功点击元素: {selector}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"点击元素失败: {e}")
            return False
    
    def input_text(self, selector: str, text: str, by_type: str = "css", clear_first: bool = True, retry_count: int = 3) -> bool:
        """在输入框中输入文本"""
        for attempt in range(retry_count):
            try:
                element = self.find_element(selector, by_type)
                if element:
                    if clear_first:
                        element.clear()
                    element.send_keys(text)
                    logger.info(f"成功输入文本到元素: {selector}")
                    return True
                
                if attempt < retry_count - 1:
                    logger.warning(f"输入文本失败，重试 {attempt + 1}/{retry_count}")
                    time.sleep(1)
                    
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(f"输入文本失败，重试 {attempt + 1}/{retry_count}: {e}")
                    time.sleep(1)
                else:
                    logger.error(f"输入文本失败: {e}")
        
        return False
    
    def get_text(self, selector: str, by_type: str = "css") -> Optional[str]:
        """获取元素文本"""
        try:
            element = self.find_element(selector, by_type)
            if element:
                text = element.text
                logger.info(f"成功获取元素文本: {selector}")
                return text
            return None
            
        except Exception as e:
            logger.error(f"获取文本失败: {e}")
            return None
    
    def get_attribute(self, selector: str, attribute: str, by_type: str = "css") -> Optional[str]:
        """获取元素属性"""
        try:
            element = self.find_element(selector, by_type)
            if element:
                attr_value = element.get_attribute(attribute)
                logger.info(f"成功获取元素属性: {selector}.{attribute}")
                return attr_value
            return None
            
        except Exception as e:
            logger.error(f"获取属性失败: {e}")
            return None
    
    def scroll_to_element(self, selector: str, by_type: str = "css") -> bool:
        """滚动到指定元素"""
        try:
            element = self.find_element(selector, by_type)
            if element:
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
                logger.info(f"成功滚动到元素: {selector}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"滚动失败: {e}")
            return False
    
    def wait_for_element(self, selector: str, by_type: str = "css", timeout: int = 10, condition: str = "presence") -> bool:
        """等待元素出现"""
        try:
            wait = WebDriverWait(self.driver, timeout)
            
            # 选择等待条件
            if condition == "clickable":
                condition_func = EC.element_to_be_clickable
            elif condition == "visible":
                condition_func = EC.visibility_of_element_located
            else:
                condition_func = EC.presence_of_element_located
            
            # 选择定位方式
            if by_type.lower() == "css":
                locator = (By.CSS_SELECTOR, selector)
            elif by_type.lower() == "xpath":
                locator = (By.XPATH, selector)
            elif by_type.lower() == "id":
                locator = (By.ID, selector)
            elif by_type.lower() == "class":
                locator = (By.CLASS_NAME, selector)
            elif by_type.lower() == "tag":
                locator = (By.TAG_NAME, selector)
            else:
                raise ValueError(f"不支持的选择器类型: {by_type}")
            
            wait.until(condition_func(locator))
            logger.info(f"元素已出现: {selector}")
            return True
            
        except TimeoutException:
            logger.error(f"等待元素超时: {selector}")
            return False
        except Exception as e:
            logger.error(f"等待元素时出错: {e}")
            return False
    
    def execute_script(self, script: str) -> Any:
        """执行JavaScript脚本"""
        try:
            result = self.driver.execute_script(script)
            logger.info("成功执行JavaScript脚本")
            return result
            
        except Exception as e:
            logger.error(f"执行脚本失败: {e}")
            return None
    
    def take_screenshot(self, filename: str = None) -> str:
        """截取屏幕截图"""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            # 确保截图目录存在
            screenshot_dir = Path.home() / ".local/share/deepin-mcp-server/screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = screenshot_dir / filename
            self.driver.save_screenshot(str(filepath))
            
            logger.info(f"截图已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return ""
    
    def get_page_title(self) -> str:
        """获取页面标题"""
        try:
            return self.driver.title
        except Exception as e:
            logger.error(f"获取页面标题失败: {e}")
            return ""
    
    def get_current_url(self) -> str:
        """获取当前URL"""
        try:
            return self.driver.current_url
        except Exception as e:
            logger.error(f"获取当前URL失败: {e}")
            return ""
    
    def smart_input_with_suggestions(self, selector: str, text: str, by_type: str = "css") -> bool:
        """智能输入，支持自动选择建议项"""
        try:
            # 输入文本
            if not self.input_text(selector, text, by_type):
                return False
            
            # 等待建议列表出现
            time.sleep(1)
            
            # 尝试多种可能的建议选择器
            suggestion_selectors = [
                ".station_name",
                ".ui-menu-item",
                ".dropdown-item",
                ".suggestion-item",
                "[role='option']",
                "li[data-value]"
            ]
            
            for suggestion_selector in suggestion_selectors:
                try:
                    suggestions = self.driver.find_elements(By.CSS_SELECTOR, suggestion_selector)
                    if suggestions and len(suggestions) > 0:
                        # 点击第一个建议项
                        suggestions[0].click()
                        logger.info(f"成功选择建议项: {text}")
                        return True
                except:
                    continue
            
            # 如果没有找到建议，尝试按回车确认
            element = self.find_element(selector, by_type)
            if element:
                element.send_keys(Keys.ENTER)
                logger.info(f"通过回车确认输入: {text}")
                return True
            
            return True  # 即使没有建议也算成功
            
        except Exception as e:
            logger.error(f"智能输入失败: {e}")
            return False

# 全局浏览器控制器实例
_browser_controller = None

def _get_browser_controller() -> BrowserController:
    """获取浏览器控制器实例"""
    global _browser_controller
    if _browser_controller is None:
        _browser_controller = BrowserController()
    return _browser_controller

def _start_browser_session(browser_type: str = "chrome", headless: bool = False) -> str:
    """启动浏览器会话"""
    try:
        controller = _get_browser_controller()
        controller.browser_type = browser_type.lower()
        controller.headless = headless
        
        if controller.start_browser():
            return f"成功启动{browser_type}浏览器会话"
        else:
            return "启动浏览器失败，请检查是否安装了对应的WebDriver"
            
    except Exception as e:
        return f"启动浏览器会话失败: {str(e)}"

def _close_browser_session() -> str:
    """关闭浏览器会话"""
    try:
        controller = _get_browser_controller()
        controller.close_browser()
        return "浏览器会话已关闭"
        
    except Exception as e:
        return f"关闭浏览器会话失败: {str(e)}"

def _browser_navigate(url: str) -> str:
    """浏览器导航到指定URL"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        if controller.navigate_to(url):
            title = controller.get_page_title()
            return f"成功导航到: {url}\n页面标题: {title}"
        else:
            return f"导航到 {url} 失败"
            
    except Exception as e:
        return f"导航失败: {str(e)}"

def _browser_click(selector: str, by_type: str = "css") -> str:
    """点击页面元素"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        if controller.click_element(selector, by_type):
            return f"成功点击元素: {selector}"
        else:
            return f"点击元素失败: {selector}"
            
    except Exception as e:
        return f"点击操作失败: {str(e)}"

def _browser_input(selector: str, text: str, by_type: str = "css") -> str:
    """在输入框中输入文本"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        if controller.input_text(selector, text, by_type):
            return f"成功在元素 {selector} 中输入文本"
        else:
            return f"输入文本失败: {selector}"
            
    except Exception as e:
        return f"输入操作失败: {str(e)}"

def _browser_get_text(selector: str, by_type: str = "css") -> str:
    """获取元素文本"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        text = controller.get_text(selector, by_type)
        if text is not None:
            return f"元素文本: {text}"
        else:
            return f"获取元素文本失败: {selector}"
            
    except Exception as e:
        return f"获取文本失败: {str(e)}"

def _browser_wait_element(selector: str, by_type: str = "css", timeout: int = 10) -> str:
    """等待元素出现"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        if controller.wait_for_element(selector, by_type, timeout):
            return f"元素已出现: {selector}"
        else:
            return f"等待元素超时: {selector}"
            
    except Exception as e:
        return f"等待元素失败: {str(e)}"

def _browser_smart_input(selector: str, text: str, by_type: str = "css") -> str:
    """智能输入，支持自动选择建议项"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        if controller.smart_input_with_suggestions(selector, text, by_type):
            return f"成功智能输入: {text} 到元素 {selector}"
        else:
            return f"智能输入失败: {selector}"
            
    except Exception as e:
        return f"智能输入失败: {str(e)}"

def _browser_screenshot(filename: str = None) -> str:
    """截取屏幕截图"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        filepath = controller.take_screenshot(filename)
        if filepath:
            return f"截图已保存: {filepath}"
        else:
            return "截图失败"
            
    except Exception as e:
        return f"截图操作失败: {str(e)}"

def _browser_execute_script(script: str) -> str:
    """执行JavaScript脚本"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        result = controller.execute_script(script)
        return f"脚本执行完成，返回值: {result}"
        
    except Exception as e:
        return f"脚本执行失败: {str(e)}"

def _browser_get_page_info() -> str:
    """获取当前页面信息"""
    try:
        controller = _get_browser_controller()
        if not controller.driver:
            return "浏览器未启动，请先启动浏览器会话"
        
        title = controller.get_page_title()
        url = controller.get_current_url()
        
        return f"页面标题: {title}\n当前URL: {url}"
        
    except Exception as e:
        return f"获取页面信息失败: {str(e)}" 