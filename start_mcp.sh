#!/bin/bash

# Deepin MCP Server 启动脚本
# 用于Cursor集成

# 设置工作目录
cd "$(dirname "$0")"

# 设置环境变量
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"

# 启动MCP服务器
exec /home/xsluck/.local/bin/uv run python src/deepin_mcp_server/server.py 