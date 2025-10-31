# S1CLI - Stage1st 论坛命令行工具

> 一个功能完整的 Stage1st 论坛命令行客户端

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## ✨ 特性

- 🔐 **登录状态持久化** - 自动保存登录信息，支持会话过期检测（7天）
- 📱 **浏览器模拟** - 模拟真实 Chrome User Agent + 完整 Headers，避免被封号
- ⏱️ **请求频率限制** - 随机 0.5-2 秒延迟，防止被识别为机器人
- 📖 **完整功能支持**：
  - ✅ 查看论坛版块和帖子列表
  - ✅ 阅读帖子内容和回复
  - ✅ 发布新帖和回复帖子
  - ✅ 搜索帖子（支持版块限定）
  - ✅ 个人信息查看
  - ⏳ 签到、收藏、点赞（开发中）

## 🚀 快速开始

### 安装

#### 使用 uv（推荐，更快）

```bash
# 克隆项目
git clone https://github.com/Geoion/s1cli.git
cd s1cli

# 安装
uv pip install -e .
```

#### 使用 pip

```bash
# 克隆项目
git clone https://github.com/Geoion/s1cli.git
cd s1cli

# 安装
pip install -e .
```

### 基本使用

#### 查看帮助

```bash
# 不带参数会显示帮助信息
s1cli

# 或显式查看帮助
s1cli --help
```

#### 登录账号

```bash
s1cli login
# 按提示输入用户名和密码
```

#### 浏览论坛

```bash
# 列出所有版块
s1cli list

# 查看指定版块的帖子（第1页）
s1cli list --forum 游戏论坛

# 查看指定页码
s1cli list --forum 游戏论坛 --page 2

# JSON 格式输出
s1cli list --forum 游戏论坛 --json
```

#### 查看帖子

```bash
# 查看帖子详情（需要帖子 ID）
s1cli view 2265956

# 查看第2页
s1cli view 2265956 --page 2
```

#### 搜索

```bash
# 搜索关键词
s1cli search "宝可梦"

# 限定版块搜索
s1cli search "宝可梦" --forum 游戏论坛
```

#### 发帖和回帖

```bash
# 发新帖
s1cli post --forum 游戏论坛 --title "测试标题" --content "帖子内容"

# 回复帖子
s1cli reply 2265956 --content "回复内容"
```

#### 个人中心

```bash
# 查看个人信息
s1cli profile

# 登出
s1cli logout
```

#### 配置管理

```bash
# 查看配置
s1cli config show

# 设置配置
s1cli config set theme=dark
```

### 示例工作流

```bash
# 1. 登录
s1cli login
# 输入用户名：your_username
# 输入密码：********

# 2. 浏览游戏论坛
s1cli list --forum 游戏论坛

# 3. 查看感兴趣的帖子（假设 ID 是 2265956）
s1cli view 2265956

# 4. 回复帖子
s1cli reply 2265956 --content "很有意思的讨论！"

# 5. 搜索相关话题
s1cli search "塞尔达" --forum 游戏论坛

# 6. 发表新帖
s1cli post --forum 游戏论坛 --title "关于游戏的讨论" --content "这里是内容..."
```

## 📂 配置文件

配置文件存储在 `~/.config/s1cli/`：

- `config.toml` - 用户偏好设置
- `session.toml` - 登录会话信息（cookies、用户名、登录时间）
- `cache/` - 缓存目录

会话信息会自动保存，7天后过期，过期后需要重新登录。

## 🔧 开发

### 安装开发依赖

```bash
# 使用 uv
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"
```

### 运行

```bash
# 直接运行
python -m s1cli --help

# 或使用已安装的命令
s1cli --help
```

### 代码格式化

```bash
black s1cli
```

### 类型检查

```bash
mypy s1cli
```

### 运行测试

```bash
pytest
```

## 📊 项目结构

```
s1cli/
├── s1cli/
│   ├── __init__.py
│   ├── __main__.py          # 命令行入口（Click）
│   ├── config.py            # 配置管理
│   ├── utils.py             # 工具函数
│   ├── api/                 # API 层
│   │   ├── client.py        # HTTP 客户端（UA 模拟）
│   │   ├── auth.py          # 登录认证
│   │   ├── forum.py         # 论坛版块
│   │   ├── thread.py        # 帖子操作
│   │   └── search.py        # 搜索功能
│   ├── models/              # 数据模型
│   │   ├── forum.py         # Forum 模型
│   │   ├── thread.py        # Thread/Post 模型
│   │   └── user.py          # User 模型
│   └── ui/                  # UI 界面（待完善）
│       ├── app.py           # 应用主程序
│       ├── screens/         # 各个界面
│       └── widgets/         # 自定义组件
├── tests/                   # 测试
├── pyproject.toml           # 项目配置
├── README.md                # 本文件
└── LICENSE                  # MIT 许可证
```

## 🎯 技术要点

### Discuz API 逆向

由于 Discuz 没有官方 REST API，本项目通过分析网页请求实现：

#### 1. 登录流程
- GET 登录页面获取 `formhash` 和 `loginhash`
- POST 登录数据，保存 cookies
- 验证登录状态

#### 2. 发帖流程
- GET 发帖页面获取 `formhash`
- POST 发帖数据（标题、内容）
- 从响应提取帖子 ID

#### 3. HTML 解析
使用 BeautifulSoup4 + lxml 解析页面内容

### 防封号措施

#### 1. User Agent 模拟
```python
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
```

完整的浏览器 Headers：
```python
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
```

#### 2. 请求频率限制
随机 0.5-2 秒延迟：
```python
delay = random.uniform(0.5, 2.0)
time.sleep(delay)
```

#### 3. Cookie 管理
- 持久化登录状态到 `~/.config/s1cli/session.toml`
- Base64 编码安全存储
- 自动过期检测（7天）

## 🎓 技术栈

- **语言**: Python 3.9+
- **包管理**: uv / pip
- **HTTP 客户端**: httpx
- **HTML 解析**: BeautifulSoup4 + lxml
- **CLI 框架**: Click
- **美化输出**: Rich
- **配置格式**: TOML

## 📈 项目状态

### ✅ 已完成

#### 核心功能 (100%)
- ✅ 完整的项目结构（22个文件，~1,750行代码）
- ✅ 全局命令行工具配置
- ✅ 配置文件管理和会话持久化
- ✅ 数据模型（Forum、Thread、Post、User）
- ✅ HTTP 客户端（Chrome UA 模拟 + 频率限制）
- ✅ 完整的 API 实现（登录、论坛、帖子、搜索）
- ✅ 命令行接口

### 🚧 待完善

#### 功能增强
- [ ] 更完善的错误处理和重试机制
- [ ] 本地缓存机制
- [ ] 图片预览支持
- [ ] BBCode 格式化显示
- [ ] 签到功能实现
- [ ] 收藏功能
- [ ] 点赞功能

#### 测试
- [ ] 单元测试
- [ ] 集成测试
- [ ] Mock 测试数据

## 💡 常见问题

### 登录失败

1. 检查用户名和密码是否正确
2. 确保网络连接正常
3. 如果多次失败，可能被临时限制，请稍后再试

### 找不到版块

运行 `s1cli list` 查看所有可用版块名称。

### 帖子 ID 在哪里

- 在网页 URL 中：`thread-2265956-1-1.html` 中的 `2265956`
- 或使用 `s1cli list --forum 版块名` 查看帖子列表

### 会话过期

会话会在 7 天后自动过期，过期后运行 `s1cli login` 重新登录即可。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发优先级

1. 添加错误处理
2. 编写测试
3. 优化性能
4. 完善功能

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## ⚠️ 免责声明

本工具仅供学习交流使用，请遵守 Stage1st 论坛的用户协议和使用规则。使用本工具产生的任何后果由使用者自行承担。

## 🔗 链接

- **项目主页**: https://github.com/Geoion/s1cli
- **问题反馈**: https://github.com/Geoion/s1cli/issues
- **Stage1st 论坛**: https://stage1st.com/

---

## 📝 更新日志

### [0.1.0] - 2025-10-31

#### 重大更新

##### 📝 文档整合
- ✅ 将所有 markdown 文件（DEVELOPMENT.md、QUICKSTART.md、PROJECT_SUMMARY.md）合并到单一的 README.md
- ✅ README.md 现在包含完整的使用说明、开发文档、技术要点和常见问题
- ✅ 文档更加集中和易于维护

##### 📦 包管理器迁移
- ✅ 从 Poetry 迁移到 uv（更快的 Python 包管理器）
- ✅ pyproject.toml 采用标准 PEP 621 格式
- ✅ 使用 hatchling 作为构建后端（更轻量）
- ✅ 完全兼容 pip 和 uv

##### 🛠️ 项目改进
- ✅ 更新 .gitignore 支持 uv.lock
- ✅ 简化项目根目录（只保留核心文件）
- ✅ 统一文档风格和格式

#### 安装方式更新

##### 旧方式（Poetry）
```bash
poetry install
```

##### 新方式（uv，推荐）
```bash
uv pip install -e .

# 或使用 pip
pip install -e .
```

#### 兼容性
- ✅ 完全向后兼容
- ✅ 不影响现有功能
- ✅ 支持 Python 3.9+

#### 功能清单

##### ✅ 已实现
- 完整的 Discuz API 封装
- 命令行接口（双模式）
- 配置和会话管理
- 登录状态持久化
- Chrome UA 模拟
- 请求频率限制
- TUI 基础框架

##### 🎉 新增功能（2025-10-31）

###### TUI 界面全部完成
- ✅ 登录界面（带表单输入）
- ✅ 帖子列表界面（可滚动DataTable）
- ✅ 帖子详情查看界面（支持分页）
- ✅ 发帖编辑器（标题+内容）
- ✅ 回帖编辑器（内容编辑）
- ✅ 搜索界面（实时搜索）
- ✅ 完整的快捷键支持
- ✅ 集成到主应用

###### 错误处理机制
- ✅ 自定义异常类（7种异常类型）
- ✅ 重试装饰器（指数退避）
- ✅ 错误处理装饰器
- ✅ 友好的错误提示

###### 代码质量
- ✅ 新增 7 个界面和工具文件
- ✅ 总代码量达 2,500+ 行
- ✅ 完整的类型注解
- ✅ 详细的文档字符串

##### 🚧 未来可选功能
- 本地缓存机制
- 单元测试
- 图片预览
- BBCode 格式化

---

**Made with ❤️ by eskiyin**
