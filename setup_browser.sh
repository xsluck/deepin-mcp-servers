#!/bin/bash

# Deepin MCP Server 浏览器控制功能设置脚本
# 用于安装必要的 WebDriver 和依赖

set -e

echo "🌐 Deepin MCP Server 浏览器控制功能设置"
echo "=========================================="

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
   echo "❌ 请不要以root用户运行此脚本"
   exit 1
fi

# 更新包列表
echo "📦 更新软件包列表..."
sudo apt update

# 安装Chrome/Chromium WebDriver
echo "🔧 安装 Chrome WebDriver..."
if command -v chromium-browser &> /dev/null || command -v google-chrome &> /dev/null; then
    sudo apt install -y chromium-chromedriver
    echo "✅ Chrome WebDriver 安装完成"
else
    echo "⚠️  未检测到 Chrome/Chromium 浏览器，跳过 Chrome WebDriver 安装"
fi

# 安装Firefox WebDriver
echo "🔧 安装 Firefox WebDriver..."
if command -v firefox &> /dev/null; then
    sudo apt install -y firefox-geckodriver
    echo "✅ Firefox WebDriver 安装完成"
else
    echo "⚠️  未检测到 Firefox 浏览器，跳过 Firefox WebDriver 安装"
fi

# 检查Python环境
echo "🐍 检查 Python 环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    echo "✅ Python 版本: $PYTHON_VERSION"
    
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 12) else 1)" 2>/dev/null; then
        echo "✅ Python 版本满足要求 (>= 3.12)"
    else
        echo "⚠️  Python 版本可能过低，建议使用 Python 3.12 或更高版本"
    fi
else
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

# 安装Python依赖
echo "📚 安装 Python 依赖..."
if command -v uv &> /dev/null; then
    echo "使用 uv 安装依赖..."
    uv sync
elif command -v pip3 &> /dev/null; then
    echo "使用 pip 安装依赖..."
    pip3 install -e .
else
    echo "❌ 未找到 pip 或 uv，请先安装包管理器"
    exit 1
fi

# 验证安装
echo "🔍 验证安装..."

# 检查Selenium
if python3 -c "import selenium; print(f'Selenium 版本: {selenium.__version__}')" 2>/dev/null; then
    echo "✅ Selenium 安装成功"
else
    echo "❌ Selenium 安装失败"
    exit 1
fi

# 检查WebDriver
WEBDRIVER_FOUND=false

if command -v chromedriver &> /dev/null; then
    CHROME_VERSION=$(chromedriver --version 2>/dev/null | head -n1 || echo "未知版本")
    echo "✅ Chrome WebDriver: $CHROME_VERSION"
    WEBDRIVER_FOUND=true
fi

if command -v geckodriver &> /dev/null; then
    FIREFOX_VERSION=$(geckodriver --version 2>/dev/null | head -n1 || echo "未知版本")
    echo "✅ Firefox WebDriver: $FIREFOX_VERSION"
    WEBDRIVER_FOUND=true
fi

if [ "$WEBDRIVER_FOUND" = false ]; then
    echo "⚠️  未找到可用的 WebDriver，浏览器控制功能可能无法正常工作"
    echo "请手动安装 Chrome 或 Firefox WebDriver"
fi

# 创建截图目录
SCREENSHOT_DIR="$HOME/.local/share/deepin-mcp-server/screenshots"
mkdir -p "$SCREENSHOT_DIR"
echo "📁 创建截图目录: $SCREENSHOT_DIR"

echo ""
echo "🎉 设置完成！"
echo ""
echo "📋 使用说明："
echo "1. 启动 MCP 服务器: python src/deepin_mcp_server/server.py"
echo "2. 运行浏览器演示: python examples/browser_tasks.py"
echo "3. 截图保存位置: $SCREENSHOT_DIR"
echo ""
echo "💡 提示："
echo "- 首次使用时，浏览器可能需要一些时间来启动"
echo "- 如果遇到权限问题，请确保 WebDriver 在 PATH 中"
echo "- 无头模式可以在后台运行，不显示浏览器窗口"
echo ""
echo "�� 更多信息请查看 README.md" 