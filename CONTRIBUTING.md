# Contributing

感谢为 DeterminFlow 社区 Plugin 生态贡献代码。

提交前请完整阅读 [README](README.md) 中的“提交到社区仓库”“重要安全说明”和
“更新、下架与所有权”。

最小要求：

1. 一个 Pull Request 只新增或更新一个 Plugin。
2. Plugin 位于 `plugins/<plugin-id>`，并同步更新 `plugin-repository.toml`。
3. 提供 `extension.toml`、README、完整 LICENSE、测试或可重复验证步骤。
4. 使用 Python 3.11 或更高版本执行 `python3.11 scripts/validate_repository.py` 和
   `git diff --check`。
5. 在 Pull Request 中披露权限影响、外部通信、数据处理、依赖、迁移和测试结果。

`determinflow-*` 品牌前缀，以及 `bishu-novel`、`public-api`、`hindsight-memory`、
`novel-teardown` 等官方或已知产品 ID 均为保留名称，社区投稿不得使用。

提交即表示你有权按 Plugin 目录中声明的许可证贡献和再分发相关内容。不要提交私人数据、
凭据、未授权第三方内容或含糊来源的生成资产。
