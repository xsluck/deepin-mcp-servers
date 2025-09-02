# 🌐 浏览器控制功能使用指南

## 📋 快速开始

### 1. 启动MCP服务器

如果您已经安装了Chrome浏览器，可以直接使用浏览器控制功能：

```bash
# 安装依赖
uv sync

# 启动MCP服务器
uv run python src/deepin_mcp_server/server.py
```

### 2. 运行演示

```bash
# 网络页面演示
uv run python examples/browser_tasks.py
```

## 🔧 自动化原理

系统使用以下方法自动获取ChromeDriver：

1. **webdriver-manager**: 自动下载匹配的ChromeDriver版本
2. **内置下载器**: 如果webdriver-manager不可用，使用内置下载功能
3. **系统PATH**: 检查系统是否已安装ChromeDriver

## 🎯 主要功能

### 基础操作
- ✅ 启动/关闭浏览器会话
- ✅ 页面导航
- ✅ 元素定位（CSS、XPath、ID等）
- ✅ 点击操作
- ✅ 文本输入
- ✅ 页面截图

### 高级功能
- ✅ JavaScript脚本执行
- ✅ 表单自动填写
- ✅ 智能等待机制
- ✅ 多种选择器支持
- ✅ 错误处理和恢复

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `src/deepin_mcp_server/server.py` | MCP服务器主程序 |
| `examples/browser_tasks.py` | 网络页面自动化示例 |
| `setup_browser.sh` | 自动安装脚本 |
| `start_mcp.sh` | MCP服务器启动脚本 |

## 🖼️ 截图保存位置

所有截图自动保存到：
```
~/.local/share/deepin-mcp-server/screenshots/
```

## 🚀 MCP工具函数

在MCP服务器中可使用的浏览器控制工具：

```python
# 会话管理
start_browser_session(browser_type="chrome", headless=False)
close_browser_session()

# 页面操作
browser_navigate(url)
browser_get_page_info()
browser_screenshot(filename=None)

# 元素交互
browser_click(selector, by_type="css")
browser_input(selector, text, by_type="css")
browser_get_text(selector, by_type="css")
browser_wait_element(selector, by_type="css", timeout=10)

# 高级功能
browser_execute_script(script)
```

## 💡 使用技巧

### 1. 选择器类型
- `css`: CSS选择器（推荐）
- `xpath`: XPath表达式
- `id`: 元素ID
- `class`: 类名
- `tag`: 标签名

### 2. 常用CSS选择器示例
```css
#elementId          /* ID选择器 */
.className          /* 类选择器 */
input[name="email"] /* 属性选择器 */
button:nth-child(2) /* 伪类选择器 */
```

### 3. 最佳实践
- 使用智能等待而不是固定延时
- 优先使用CSS选择器
- 适当使用截图记录操作过程
- 在无头模式下运行提高性能

## 🔍 故障排除

### 问题1: ChromeDriver版本不匹配
**解决方案**: 系统会自动下载匹配版本，确保网络连接正常

### 问题2: 元素定位失败
**解决方案**: 
- 检查选择器是否正确
- 使用`browser_wait_element`等待元素加载
- 尝试不同的选择器类型

### 问题3: 浏览器启动失败
**解决方案**:
- 确保Chrome已安装
- 检查系统资源是否充足
- 尝试无头模式运行

## 📞 获取帮助

如果遇到问题：

1. 检查MCP服务器日志：`~/.local/share/deepin-mcp-server/deepin-mcp-server.log`
2. 运行浏览器演示：`python examples/browser_tasks.py`
3. 检查截图了解页面状态
4. 参考示例代码进行调试

## 🎉 总结

您的Chrome浏览器**可以直接使用**浏览器控制功能！系统会自动处理ChromeDriver的下载和配置，让您专注于自动化任务的开发。 