## Plugin

- Plugin ID：
- 变更类型：首次提交 / 功能更新 / 安全修复 / 兼容性更新 / 下架
- 已验证的 DeterminFlow 版本或 Commit：

## 行为与风险披露

- 外部服务和网络域名：
- 文件读取与写入：
- 子进程或系统命令：
- 收集、保存或发送的数据：
- Python 与系统依赖：
- Migration（迁移）、回滚和数据清理：

## 验证

- 测试命令：
- 测试结果：
- 已知限制或不兼容变化：

## Checklist

- [ ] 一个 Pull Request 只新增或更新一个 Plugin。
- [ ] 没有修改 `.github/`、`scripts/` 或其他仓库基础设施。
- [ ] `extension.toml`、目录名和 `plugin-repository.toml` 使用同一个 Plugin ID。
- [ ] Plugin 目录包含 README、完整 LICENSE、测试或可重复验证步骤。
- [ ] 已运行 `python3.11 scripts/validate_repository.py`。
- [ ] 已运行 `git diff --check`。
- [ ] 没有提交凭据、私钥、用户数据、日志、构建缓存或未授权第三方内容。
- [ ] 已披露 Plugin 的权限影响、外部通信、依赖和数据处理。
