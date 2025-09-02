# Deepin MCP Servers

## 简介

一个为 Deepin 系统设计的 MCP (Model Context Protocol) 服务器实现，提供系统工具、文件操作、网络搜索等功能。
源自 Deepin 的 MCP 服务器实现，并进行了优化和扩展。

## 功能特性

### 🚀 应用管理
- **启动应用**: 支持启动系统内置应用
  - 支持的应用包括：日历、文件管理器、计算器、相机、画图、文本编辑器、音乐、影院、浏览器、控制中心等40+个应用

### 📁 文件操作
- **基础文件操作**
  - 打开文件（使用系统默认程序）
  - 复制文件/文件夹
  - 移动文件/文件夹
  - 重命名文件/文件夹
  - 删除文件/文件夹
  - 创建新文件
  - 创建新文件夹
  - 批量重命名文件
  - 列出目录内容（支持递归）
  - 获取文件大小信息
  - 获取用户目录路径

- **文档处理**
  - 支持读取多种文档格式：
    - 文本文件 (.txt, .md)
    - Microsoft Office 文档 (.doc, .docx, .xls, .xlsx, .ppt, .pptx)
    - PDF 文档
    - 其他常见格式

### 🌐 网络服务
- **多搜索引擎支持**
  - 百度搜索
  - 必应搜索 (Bing)
  - DuckDuckGo 搜索
  - Google 搜索
  - 搜狗搜索

- **网页内容获取**
  - 获取网页内容并转换为 Markdown 格式
  - 支持内容提取和清理
  - 文件下载功能（支持 HTTP/HTTPS）

### 🖥️ 系统控制
- **桌面环境控制**
  - 切换系统壁纸（支持指定文件或自动切换）
  - 切换任务栏模式（时尚模式/高效模式）
  - 开启/关闭勿扰模式
  - 切换系统主题（浅色/深色/自动）

- **系统信息**
  - 获取系统硬件信息（CPU、内存、硬盘）

- **通信功能**
  - 发送邮件（支持主题、正文、收件人、抄送、密送）
  - 创建日程安排（支持标题、开始时间、结束时间）

### 💻 终端命令
- **安全的命令执行**
  - 执行常用 Linux 命令
  - 危险命令拦截和确认机制
  - 支持自定义工作目录
  - 命令超时控制（最大120秒）
  - 执行结果包含标准输出、错误输出和退出代码

### 🔧 Git 操作
- **仓库管理**
  - 查看 Git 仓库状态
  - 获取提交历史记录
  - 查看分支信息
  - 克隆远程仓库

- **文件操作**
  - 添加文件到暂存区
  - 提交更改
  - 拉取远程更新
  - 推送本地提交

- **差异和历史**
  - 查看文件修改差异（工作区/暂存区）
  - 查看特定提交的详细信息
  - 查看文件的修改历史记录

### 🌐 浏览器控制
- **浏览器自动化**
  - 支持 Chrome 和 Firefox 浏览器
  - 启动/关闭浏览器会话
  - 有头模式和无头模式支持
  - 页面导航和截图功能

- **页面元素操作**
  - 多种元素选择器支持（CSS、XPath、ID等）
  - 点击页面元素（按钮、链接等）
  - 输入框文本输入
  - 获取元素文本和属性
  - 等待元素出现（智能等待）

- **高级功能**
  - 执行自定义 JavaScript 脚本
  - 页面滚动和元素定位
  - 表单自动填写
  - 页面信息获取（标题、URL等）

### 🔔 系统交互
- **DBus 服务集成**
  - 与 Deepin 系统服务深度集成
  - 支持 V20 和 V25 版本的 DBus 接口
  - 系统属性读取和设置

- **用户交互**
  - 显示确认对话框
  - 发送系统桌面通知
  - 支持自定义图标和超时时间

## 安装

### 使用 uv 安装依赖：

```bash
uv sync
```

### 或使用 pip：

```bash
pip install -e .
```

## 使用方法

### 启动 MCP 服务器

```bash
python src/deepin_mcp_server/server.py
```

### 浏览器控制功能设置

> **💡 重要提示**: 如果您已经安装了Chrome浏览器，**可以直接使用**！系统会自动下载匹配的ChromeDriver，无需手动安装。

**Chrome用户（推荐）:**
```bash
# 如果已安装Chrome，直接测试即可
python test_chrome_direct.py
```

**完整自动设置:**
```bash
# 运行自动设置脚本
./setup_browser.sh
```

**手动设置:**

浏览器控制功能需要安装对应的 WebDriver：

**Chrome WebDriver 安装:**
```bash
# 方法1: 使用包管理器 (推荐)
sudo apt install chromium-chromedriver

# 方法2: 手动下载
# 访问 https://chromedriver.chromium.org/ 下载对应版本
```

**Firefox WebDriver 安装:**
```bash
# 方法1: 使用包管理器
sudo apt install firefox-geckodriver

# 方法2: 手动下载
# 访问 https://github.com/mozilla/geckodriver/releases 下载
```

### 浏览器功能测试

验证浏览器控制功能：
```bash
# 启动MCP服务器
python src/deepin_mcp_server/server.py
```

该示例包含：
- 百度搜索自动化
- GitHub 页面导航演示
- JavaScript 脚本执行
- 表单自动填写演示

## 项目结构

```
src/deepin_mcp_server/
├── server.py                    # 主服务器文件，定义所有 MCP 工具
├── dbus_service/               # DBus 服务模块
│   └── services.py            # DBus 接口和服务定义
├── system_tools/              # 系统工具模块
│   ├── file_operation.py      # 文件操作功能
│   ├── git_operations.py      # Git 操作功能
│   ├── system_control.py      # 系统控制功能
│   ├── terminal_command.py    # 终端命令执行
│   └── browser_control.py     # 浏览器控制功能
└── web_service/               # 网络服务模块
    ├── services.py            # 网络服务主接口
    ├── utils.py              # 工具函数
    └── web_search/           # 网络搜索子模块
        ├── base.py           # 搜索基类
        ├── search.py         # 搜索主逻辑
        ├── search_types.py   # 搜索类型定义
        ├── util.py           # 搜索工具函数
        └── engines/          # 搜索引擎实现
            ├── baidu.py      # 百度搜索
            ├── bing.py       # 必应搜索
            ├── duckduckgo.py # DuckDuckGo 搜索
            ├── google.py     # Google 搜索
            └── sogou.py      # 搜狗搜索
```

## 技术依赖

- **Python >= 3.12**
- **核心依赖**:
  - `httpx >= 0.28.1` - HTTP 客户端
  - `mcp[cli] >= 1.6.0` - MCP 协议支持
  - `requests >= 2.30.0` - HTTP 请求库

- **文档处理**:
  - `PyPDF2` - PDF 文档处理
  - `python-docx` - Word 文档处理
  - `python-pptx` - PowerPoint 文档处理
  - `pandas` - 数据处理

- **网页处理**:
  - `beautifulsoup4 >= 4.12.0` - HTML 解析
  - `lxml >= 4.9.0` - XML/HTML 处理器
  - `markdownify >= 0.11.0` - HTML 转 Markdown
  - `readabilipy >= 0.2.0` - 网页内容提取
  - `readability-lxml >= 0.8.1` - 可读性分析
  - `lxml_html_clean` - HTML 清理

- **浏览器自动化**:
  - `selenium >= 4.15.0` - 浏览器自动化框架

## 特色功能

1. **深度系统集成**: 与 Deepin 桌面环境深度集成，支持壁纸切换、主题切换等系统级操作
2. **安全命令执行**: 内置危险命令检测和用户确认机制，保障系统安全
3. **多搜索引擎**: 支持5种主流搜索引擎，自动切换确保搜索成功率
4. **完整的 Git 工作流**: 从基础操作到高级功能，支持完整的 Git 开发工作流
5. **丰富的文档支持**: 支持多种文档格式的读取和处理
6. **浏览器自动化**: 基于 Selenium 的强大浏览器控制，支持复杂的网页任务自动化
7. **用户友好交互**: 提供对话框确认和系统通知，提升用户体验

## 日志记录

服务器运行日志保存在：`~/.local/share/deepin-mcp-server/deepin-mcp-server.log`

## 兼容性

- 支持 Deepin V20 和 V25 系统
- 自动检测系统版本并使用对应的 DBus 接口
- 向后兼容旧版本系统功能
