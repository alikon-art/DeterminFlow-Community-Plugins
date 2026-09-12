# DeterminFlow Codex Bridge

在 DeterminFlow 中使用**你自己登录的官方 Codex CLI 账户**。通过插件仓库安装，不需要 Codex 桌面应用，不提供共享账户或共享额度。

**0.3.4 预览版：仅 macOS Apple Silicon。** 基于 DeterminFlow Desktop 1.1.0 / Core `9db9d98c` 的扩展接口，固定官方 Codex CLI `0.153.4`。其他 Core、CLI 版本、Intel Mac、Windows、Linux 尚未验收。此项目不是 OpenAI 或 DeterminFlow 官方插件。

工作流推理强度优先级：任务显式覆盖 → agent 自身设置 → Main 默认 → `high`。0.3.1 修复了 Main 强度覆盖 agent 设置的问题；已创建任务的冻结配置不追溯修改。

## 安装

1. 安装 [Node.js](https://nodejs.org/)，然后在终端运行：

   ```sh
   npm install -g @openai/codex@0.153.4
   codex login
   codex login status
   ```

   在官方浏览器页面登录**自己的** ChatGPT 账户。仅 API Key 登录不适用于本插件当前版本。已有 CLI 时不要直接降级正在使用的环境；可单独安装固定版本并在插件设置指定其路径。

2. 在 DeterminFlow 的「插件 → 添加仓库」填入：

   - 名称：`DeterminFlow Community Plugins`
   - Git 仓库地址：`https://github.com/alikon-art/DeterminFlow-Community-Plugins.git`
   - 分支或标签：`main`

3. 保存并拉取，选择 **Codex Bridge**，确认第三方插件权限后安装、启用，重启 DeterminFlow。
4. 在插件设置中按需填写：

   - `codex_path`：CLI 完整路径；留空检查常见目录。若使用 nvm 或自定义安装，填写终端 `command -v codex` 的结果。
   - `proxy`：Codex Runtime 的 HTTP(S) 代理，例如 `http://127.0.0.1:7890`；留空直连。插件不修改系统代理或其他供应商的代理。

   保存设置后重启 DeterminFlow。
5. 打开插件「Codex 账户与用量」页面，检查账户并刷新模型目录；按页面提示重启，再在原模型菜单选择 **Codex Bridge**、模型与推理强度。

首次启动只在插件数据目录生成本地 TLS 证书。无需运行旧版 `install_app.py`，不会下载 Runtime、复制账户凭据或上传本机数据到本仓库。

## 账户与额度

调用链：`DeterminFlow → 本机 Bridge → 官方 Codex app-server → OpenAI`。

Bridge 使用当前系统用户的 `CODEX_HOME`（默认 `~/.codex`）；凭据由官方 Runtime 从该目录或系统凭据库加载。账户检查页面只显示账户类型和邮箱，不显示令牌。登录、退出均通过官方 CLI；退出后，依赖同一登录存储的其他 Codex 客户端也可能需要重新登录。

**登录谁，就使用谁的账户额度。** 克隆仓库不会取得作者账户。不要提交 `auth.json`、`.codex`、API Key、插件数据目录、私钥或运行记录。也不要把已登录的本机服务通过端口转发提供给他人。

本插件仅提供回环接口，并给模型接口配置每次启动随机生成的通行证。插件与 DeterminFlow 共享系统权限，不是同机恶意软件的安全隔离层。请求内容会发送到 OpenAI；本地插件数据还会保存模型结果、工具参数、用量和失败状态，分享故障资料前需脱敏。

官方资料：[Codex 认证](https://developers.openai.com/codex/auth/) · [固定版本发布](https://github.com/openai/codex/releases/tag/rust-v0.153.4)

## 能力与限制

- 普通聊天、工作流、多轮文字历史；模型工具调用交回 DeterminFlow 执行。
- 每次请求使用独立 Runtime，会话不共享；后续请求由 DeterminFlow 提供完整历史。
- 保留指定模型，不自动替换；模型目录可见不等于账户已获该模型访问权。
- JSON 对象/Schema 和严格工具参数有本地校验；不能宣称等价于原生严格约束解码。
- Runtime 未提供 temperature/top_p/penalty 的语义映射，插件不会伪装为支持。
- 当前是完整结果返回后包装为 SSE，**不是真正逐 token 流式输出**。长推理需在模型参数设置足够的流式分块超时。
- 请求失败或断开后，远端是否完成及用量可能未知；不会把未知当零用量。

## 开发检查

以下命令从社区仓库根目录执行。

Python 3.11+；检查依赖为 `httpx fastapi uvicorn cryptography certifi jsonschema`，运行时由兼容的 DeterminFlow 环境提供。

```sh
python plugins/taixu-codex-bridge/tests/check_package.py
python plugins/taixu-codex-bridge/tests/check_selection.py
python plugins/taixu-codex-bridge/tests/check_usage.py
python plugins/taixu-codex-bridge/tests/check_diagnostics.py
CODEX_TEST_RUNTIME=/absolute/path/to/native/codex python plugins/taixu-codex-bridge/tests/check_runtime.py
CODEX_TEST_RUNTIME=/absolute/path/to/native/codex python plugins/taixu-codex-bridge/tests/check_runtime.py --json-output
CODEX_TEST_RUNTIME=/absolute/path/to/native/codex python plugins/taixu-codex-bridge/tests/check_runtime.py --validation-feedback
CODEX_TEST_RUNTIME=/absolute/path/to/native/codex python plugins/taixu-codex-bridge/tests/check_runtime.py --validation-feedback --invalid-again
```

Runtime 检查使用临时 HOME 和本地合成服务，不读取个人登录、不调用官方模型。发布验证范围见 [VALIDATION.md](VALIDATION.md)；第二台真实电脑安装和真实账户调用尚待验证。

## 许可

插件代码采用 [MIT](LICENSE)。官方 Codex CLI 和 DeterminFlow 使用各自的许可；本仓库不分发其二进制或源码。

### 账户与用量

在 DeterminFlow 的插件列表打开「Codex 账户与用量」。页面自动读取一次，也可手动刷新：

- 账户：通过官方 `account/rateLimits/read` 读取实际 CLI 登录账户的额度窗口、重置时间与 credits 余额；这与该账户其他设备共享，不是人民币或本插件独享余额。不可用时显示未知。
- 本机：按模型汇总保留调用记录中的输入、输出、缓存、推理 token，显示有记录/总调用次数及缺失数量。它可能包含历史登录账户的调用；只汇总 Runtime 返回的记录，不作为官方完整账单。缓存和推理为子集，不重复加进总量。
- 刷新不发送模型生成请求。生成期间仍可看本机统计，账户查询需等当前节点结束。

可选页面检查（需已有 Playwright）：`node plugins/taixu-codex-bridge/tests/check_usage_ui.cjs`；可用 `CHROME_PATH` 指定浏览器可执行文件。

## 维护、权限和清理

维护仓库与问题反馈：[dongxiaojv-create/determinflow-codex-bridge](https://github.com/dongxiaojv-create/determinflow-codex-bridge/issues)。本次社区包来自作者仓库 commit `984fed1`，运行代码未改动，仅补充社区要求的资源命名空间声明、目录材料和调整测试路径。

- 外部通信：官方 Runtime 访问 OpenAI / ChatGPT 服务（包括 `chatgpt.com`、`api.openai.com`、`auth.openai.com`；具体子域和端点由固定 Runtime 决定），以及用户可选的 HTTP(S) 代理。管理页请求本机回环接口。本插件没有作者托管的转发服务或遥测端点。
- 读取：CLI 可执行文件及配套 code-mode-host，用 SHA256 校验；读取 Codex 配置，由官方 Runtime 使用当前用户的登录存储。模型输入包含用户消息、历史、工具结果等任务上下文。
- 写入：插件私有数据目录中的 TLS 证书与私钥、目录缓存、请求结果、用量、临时文件和运行诊断。不会把账户/额度接口的完整响应或登录令牌写入日志。代码会注册自身 Provider，并为 Core 当前进程设置本地 TLS 信任文件；不改变系统信任库。
- 子进程：启动用户预先安装的固定版本 Codex `app-server`，模型调用使用独立进程；停止时会终止其子进程。业务工具由 DeterminFlow 执行。
- 依赖：Python 3.11+，兼容 Core 提供 `httpx fastapi uvicorn cryptography certifi jsonschema`；macOS Apple Silicon、Node/npm 安装的官方 Codex CLI 0.153.4。插件不自动安装依赖、不下载 Runtime。页面无远程脚本或字体依赖。
- 升级不迁移书库；重启生效。失败时可使用 DeterminFlow 的插件回滚，回到同一来源的历史 revision 后重启。不同 Git 来源不能当作同一插件直接更新；从作者仓库改为社区来源前请备份并按宿主卸载/安装流程处理。
- 卸载：先等待调用结束，禁用或卸载插件并重启。确认不再需要历史结果后，再删除宿主用户数据目录下 `data/plugins/data/taixu-codex-bridge`；若宿主保留了 Codex Bridge Provider，也从模型配置中移除。卸载不会执行 `codex logout` 或删除共享的 `~/.codex` 登录存储。
- 第三方来源：插件为作者以 MIT 许可发布的代码；无捆绑字体、媒体、模型权重、Core 源码或 Codex 二进制。第三方依赖由其各自许可证约束。

### 故障定位与发布检查

失败消息包含阶段和请求编号。本机插件数据目录的 `attempts/<编号>.json` 保存相同诊断。`not_submitted` 表示尚未提交生成；`unknown` 表示尝试提交后无法确认结果，请先核查而不要直接重复提交。`runtime_failed` / `runtime_interrupted` 是 Runtime 报告的终态，不保证没有消耗额度；`completed` 表示生成结束但结果交付或校验失败。诊断不展示原始异常、提示词或凭据。

[自动检查](https://github.com/dongxiaojv-create/determinflow-codex-bridge/actions/workflows/check.yml) 在每次推送和 PR 上运行固定 Runtime 的合成生成、JSON、工具交回以及离线错误/取消测试。发布前检查对应提交全部通过；绿色检查不替代第二台电脑和真实账户验收。

社区目录校验与作者 Runtime 回归检查分别运行。
