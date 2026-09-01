# DeterminFlow Community Plugins

[`DeterminFlow`](https://github.com/alikon-art/DeterminFlow) 的社区 Plugin 仓库。
本仓库接收社区维护的 Plugin，但不把它们标记为 DeterminFlow 官方 Plugin，也不承诺
官方支持、持续维护或安全背书。

官方 Plugin 继续位于
[`DeterminFlow-Plugins`](https://github.com/alikon-art/DeterminFlow-Plugins)。两类仓库
分开维护，避免用户把“通过社区目录审核”误解成“官方可信”。

## 重要安全说明

DeterminFlow Plugin 与 Core 在同一台机器、同一权限边界内运行，目前没有进程沙箱或
细粒度权限隔离。Plugin 可以执行 Python、安装依赖、启动子进程、访问网络，并读取当前
账号有权访问的文件。

安装社区 Plugin 前，请至少检查源码、依赖、网络访问、文件写入、子进程和迁移脚本，
并备份重要工作区。目录收录只表示仓库结构和提交材料通过审核，不等于代码绝对安全。

## 两种发布方式

| 方式 | 适用场景 | 用户如何安装 | 信任与维护 |
|---|---|---|---|
| 提交到本仓库 | 希望进入统一社区目录 | 添加本仓库后从目录选择 | 作者仍是主要维护者；目录维护者只负责审核、索引和必要下架 |
| 作者自有仓库 | 希望独立发版、独立签名或使用自己的加速地址 | 用户添加作者的 Git 仓库 | 作者完全控制版本、签名密钥和托管服务 |

无论选择哪一种方式，canonical Git URL（规范 Git 地址）和精确 Commit 都是 Plugin
身份；对象存储、CDN、静态网站或 Nginx 只负责加速传输，不能替代 Git 身份。

## 用户安装

当前仓库刚建立，尚未收录社区 Plugin。首次收录后，在 DeterminFlow 的 Plugin 页面
添加以下第三方来源：

```text
名称：DeterminFlow Community Plugins
Git URL：https://github.com/alikon-art/DeterminFlow-Community-Plugins.git
Ref：main
```

刷新目录并选择 Plugin 后，DeterminFlow 会再次校验 `extension.toml`，解析并锁定精确
Commit。社区来源始终保持第三方信任边界，安装时仍需确认风险。

如果作者使用独立仓库，将 Git URL 换成作者提供的公开 HTTPS Git 地址；维护者推送 Remote
应使用 SSH，但面向用户的公开安装地址使用 HTTPS。

## 提交到社区仓库

### 1. 准备 Plugin 目录

每个 Plugin 使用全局唯一的小写 kebab-case ID（短横线命名），目录必须为
`plugins/<plugin-id>`：

```text
plugins/example-plugin/
├── extension.toml
├── README.md
├── LICENSE
├── requirements.txt          # 可选
├── settings.schema.json      # 可选；使用时必须在 extension.toml 声明
├── example_plugin/           # 可选 Python package，名称必须足够独特
├── resources/                # 可选 Agent、Prompt、Skill、Rule、Workflow、Script
├── ui/                       # 可选预构建静态页面
└── tests/                    # 强烈建议
```

不要提交 Token、密码、Cookie、私钥、真实连接串、用户数据、数据库导出、日志、构建缓存、
Python bytecode、符号链接或无法确认再分发权利的第三方资源。

### 2. 编写 `extension.toml`

最小清单：

```toml
[extension]
id = "example-plugin"
name = "Example Plugin"
version = "0.1.0"
api_version = "1"
description = "一句话说明 Plugin 的真实能力。"
capabilities = ["resources.workflows"]

[resource_namespace]
prefix = "example"
```

有 Backend（后端扩展）时使用唯一 Python package，并声明入口：

```toml
[extension]
id = "example-plugin"
name = "Example Plugin"
version = "0.1.0"
api_version = "1"
description = "Example backend integration."
backend = "determinflow_example_plugin.extension:create_extension"
dependencies = []
capabilities = ["api.routes"]

[installation]
requirements = "requirements.txt"

[resource_namespace]
prefix = "example"
```

资源型 Plugin 可以声明以下路径：

```toml
[resources]
agents = "resources/agents.json"
prompts = "resources/prompts.json"
skills = "resources/skills.json"
skill_bundles = "resources/skill-bundles"
rules = "resources/rules.json"
rule_bundles = "resources/rule-bundles"
preset_phrases = "resources/preset-phrases.json"
workflows = "resources/workflows"
script_libraries = "resources/script-library"
```

同一种资源可以声明一个路径或路径数组：

```toml
[resources]
agents = ["resources/agents/base.json", "resources/agents/extra.json"]
```

配置 Schema、静态页面和子进程必须显式声明，单独放置文件不会自动生效：

```toml
[settings]
schema = "settings.schema.json"

[page]
label = "Example 配置"
static_dir = "ui"
entrypoint = "index.html"

[[processes]]
id = "example-api"
command = ["${PYTHON}", "-m", "determinflow_example_plugin.api"]
working_directory = "."
```

注意：

- `id` 必须与目录名、仓库索引条目完全一致。
- `id` 最长 128 个字符；`determinflow-*` 品牌前缀和官方/已知产品 ID 由项目保留。
- `version` 用于展示；安装和更新仍以精确 Commit 为准。
- `api_version` 当前只能使用 `1`。
- `capabilities` 是展示和审计信息，不是权限系统。
- Plugin 之间的资源调用必须在 `dependencies` 中显式声明依赖。
- 路径必须留在当前 Plugin 目录内，不能使用 `..`、绝对路径或符号链接。
- 配置字段只在 `settings.schema.json` 中声明，并通过 `[settings].schema` 引用；不得把真实密钥值提交到仓库。
- 安装、更新、启停和配置修改在 Core 重启后生效，不要假设热加载。
- `[page]`、`[header_status]`、`[[processes]]` 和 `[lifecycle]` 等扩展面必须通过 Core 预检；不要只验证 TOML 能解析。

完整 Package 契约以
[`DeterminFlow/docs/plugin-packages.md`](https://github.com/alikon-art/DeterminFlow/blob/main/docs/plugin-packages.md)
为准。

### 3. 更新仓库索引

在根目录 `plugin-repository.toml` 添加：

```toml
[[plugins]]
id = "example-plugin"
subdirectory = "plugins/example-plugin"
```

索引只用于发现；`extension.toml` 才是安装时的最终契约。一个 Plugin ID 只能出现一次。

### 4. 本地校验

```bash
python3.11 scripts/validate_repository.py
git diff --check
```

校验脚本要求 Python 3.11 或更高版本，与当前 DeterminFlow 开发环境一致。
仓库 CI 还会固定到已记录的公开 Core Commit，运行 Core 自己的无副作用 Plugin 预检；
更新该固定 Commit 属于兼容性变更，需要单独审查。

作者还必须运行自己的测试，并在 Pull Request（合并请求）中写明：

- 测试命令和结果；
- 已验证的 DeterminFlow 版本或 Commit；
- 外部服务、网络域名、文件读写和子进程行为；
- Python 与系统依赖；
- Migration（迁移）及回滚/恢复方式；
- 收集、保存或发送的数据；
- 已知限制和不兼容变更。

### 5. 发起 Pull Request

一个 Pull Request 原则上只新增或更新一个 Plugin。首次提交至少包含：

- 可审查源码和完整许可证；
- Plugin README，包含用途、安装、配置、权限影响、卸载和数据清理；
- `extension.toml` 与仓库索引；
- 测试或可重复的验证步骤；
- 维护者联系方式，优先使用 GitHub Issue，不要提交私人邮箱；
- 第三方代码、模型、字体、媒体和数据的来源及再分发依据。

维护者可以因恶意行为、来源不明、不可重复构建、长期无人维护、名称抢占、许可证冲突、
误导性描述或明显超出声明的权限影响而拒绝或移除 Plugin。

## 作者自有仓库

独立仓库可以只包含一个 Plugin，并把 `extension.toml` 放在根目录；也可以像本仓库一样
使用 `plugin-repository.toml` 管理多个 Plugin。用户把作者仓库添加为第三方来源后，Core
仍会锁定 Git Commit 和内容摘要。

推荐做法：

1. 使用公开 Git 仓库作为 canonical source（规范来源）。
2. 使用 Release Tag 表达稳定版本，但不要移动已公开 Tag。
3. 保留完整 LICENSE、SECURITY、变更记录和兼容范围。
4. 通过 CI 在干净环境运行测试，不依赖本机绝对路径或私有配置。
5. 发现安全问题时发布新 Commit/Tag，不静默替换历史对象。

## 自托管签名加速（尚未向社区开放）

R2 只是 S3-compatible（兼容 S3）对象存储的一种实现。通用目标是让作者把签名 Registry
（注册表）托管在任意静态 HTTPS 服务，例如对象存储、CDN、静态网站或 Nginx。

截至 2026-09-01，真实公开边界是：

| Core 状态 | 社区来源传输能力 |
|---|---|
| 稳定版 `v1.0.10` | 只有 Git；该 Tag 中没有 Registry 客户端或发布工具 |
| 公开 `main` | 已有官方单端点签名 Registry，但第三方来源仍禁止配置 Registry |
| 后续通用分发版本 | 计划允许第三方来源配置多个 HTTPS 端点和独立 Ed25519 公钥 |

因此，社区作者现在应发布可独立使用的 Git 仓库，不要复制私有开发分支中的 CLI、字段或
Manifest 格式，也不要宣称当前公开 Core 已支持社区加速。通用能力正式进入公开 Core 后，
以该版本的 `docs/plugin-packages.md`、CLI `--help` 和 Release Notes 为唯一执行依据。

### 已确认的未来协议原则

- canonical Git URL 与精确 Commit 始终是 Plugin 身份；加速服务只负责传输。
- Registry 使用独立 Ed25519 密钥签名，不复用 Git、对象存储或账号凭据。
- Manifest 使用相对包路径，同一份签名对象可以原样复制到多个 HTTPS 端点。
- 客户端按端点顺序尝试，并校验 Manifest 签名、ZIP SHA-256、解压后内容摘要和精确 Commit。
- 全部端点不可用或校验失败时回退 canonical Git；配置端点不会把社区来源提升为官方来源。
- R2、MinIO 和其他兼容 S3 的服务共享同一发布适配；其他静态服务使用自己的同步工具。

未来来源配置预计采用以下形态；这是协议预览，当前公开版不能使用：

```json
{
  "name": "Example Plugins",
  "url": "https://github.com/OWNER/REPOSITORY.git",
  "ref": "main",
  "registry": {
    "endpoints": [
      "https://cdn.example.com/plugins/v1",
      "https://backup.example.net/plugins/v1"
    ],
    "public_key": "<Base64 Ed25519 public key>"
  }
}
```

### 作者现在可以准备的事项

1. 保持公开 Git 来源、Tag、Commit 和许可证清晰且不可变。
2. 设计 32 字节 Ed25519 seed 的生成、CI Secret 注入、备份和轮换流程；私钥不得进入仓库、
   命令参数、日志或构建产物。
3. 准备匿名 HTTPS 域名；端点不能包含账号信息、query（查询参数）或 fragment（片段）。
4. 规划不可变 `packages/`、Commit 快照和稳定 Manifest；不可变 Key 内容冲突必须失败关闭。
5. 稳定 Manifest 使用 `no-cache` 或 `no-store`，Commit 包和快照使用长期 immutable cache。
6. 设计端到端验收：正常端点、备用端点、Git 回退，以及篡改 Manifest、签名和 ZIP 的拒绝测试。

正式开放后，发布顺序必须是“不可变包和快照 → 公网摘要校验 → 稳定签名 → 稳定 Manifest”，
并在发布说明中写明最低 Core 版本、公钥指纹、端点和密钥轮换方式。

## 更新、下架与所有权

- 更新 Plugin 时同时更新 `extension.toml`、测试和变更说明；破坏性变化必须明确迁移路径。
- 已安装用户锁定的是精确 Commit。删除目录条目不会自动卸载用户机器上的 Plugin。
- 安全下架时，维护者会删除目录条目并发布公告；必要时保留证据和修复说明，但不公开漏洞利用细节。
- Plugin 转移维护权必须由原维护者和接收方共同确认，并重新核验许可证与签名密钥边界。
- 作者停止维护时应在 README 标记；长期无人响应或不兼容当前 Core 的 Plugin 可以从目录移除。

## 社区仓库与官方仓库的边界

| 项目 | 官方 Plugin 仓库 | 本社区仓库 |
|---|---|---|
| 维护主体 | DeterminFlow 维护者 | 作者负责 Plugin；目录维护者负责收录、索引和下架 |
| 默认信任 | 内置官方来源 | 始终是第三方来源 |
| 安装风险确认 | 按官方来源策略 | 必须显式确认 |
| 安全背书 | 官方发布流程负责 | 收录不构成安全或持续维护保证 |
| 加速托管 | DeterminFlow 维护 | 当前仅 Git；作者自托管需等待通用分发能力公开 |
| 生命周期 | 官方版本策略 | 各 Plugin 独立版本和维护状态 |

## License

仓库治理文件使用 [GNU AGPL v3](LICENSE)（`AGPL-3.0-only`）。每个 Plugin 是独立发行包，
必须在自己的目录内提供完整 `LICENSE`，其代码适用该目录声明的许可证；根许可证不会自动
替换 Plugin 自己的许可证。只接受允许公开再分发的开源许可证，许可证和第三方内容由贡献者
声明、目录维护者复核。
