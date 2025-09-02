# Deepin MCP Servers

一个为 Deepin 系统设计的 MCP (Model Context Protocol) 服务器实现，提供系统工具、文件操作、网络搜索等功能。

## 功能特性

- **系统工具**: 文件操作、Git 操作、系统控制、终端命令执行
- **网络服务**: 多搜索引擎支持（百度、必应、DuckDuckGo、Google、搜狗）
- **DBus 服务**: 系统级服务集成
- **文档处理**: 支持 PDF、Word、PowerPoint、Markdown 等格式

## 安装

使用 uv 安装依赖：

```bash
uv sync
```

或使用 pip：

```bash
pip install -r requirements.txt
```

## 使用方法

启动 MCP 服务器：

```bash
python src/deepin_mcp_server/server.py
```

## 项目结构

```
src/deepin_mcp_server/
├── server.py              # 主服务器文件
├── dbus_service/          # DBus 服务
├── system_tools/          # 系统工具模块
│   ├── file_operation.py  # 文件操作
│   ├── git_operations.py  # Git 操作
│   ├── system_control.py  # 系统控制
│   └── terminal_command.py # 终端命令
└── web_service/           # 网络服务模块
    ├── services.py        # 网络服务
    ├── utils.py          # 工具函数
    └── web_search/       # 网络搜索
        ├── engines/      # 搜索引擎实现
        └── ...
```

## 依赖

- Python >= 3.12
- httpx >= 0.28.1
- mcp[cli] >= 1.6.0
- requests >= 2.30.0
- 其他文档处理库

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
