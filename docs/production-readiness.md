# 运维 Agent 试用发布说明

当前工程定位为“超级运维问答机器人”的内部试用版：实施人员用账号登录后创建会话、上传日志或图片并提问；管理员在后台查看告警、会话反馈、介入单、知识草稿、备份、作业和审计日志。

## 已具备能力

- LLM 强依赖：启动和问答都要求 LLM 可访问；兜底只解释错误，不绕过 LLM 直接给答案。
- RAG 检索：知识库切片、SQLite 向量库、文档引用和多轮上下文。
- 试用入口：项目缩写必须使用拼音首字母大写缩写，实施姓名必填，便于会话追溯和沉淀。
- 附件分析：支持上传日志、文本、配置文件和图片，图片在环境具备 OCR 依赖时自动识别。
- 用户与权限：支持 `admin`、`reviewer`、`implementer`、`auditor`，可按项目和组件设置白名单。
- 后台告警：备份校验失败、恢复失败、LLM 不可用、后台作业失败会写入 `data/alerts.jsonl`，管理员可在“后台告警”查看。
- 会话反馈：每次会话可标记已解决、部分解决或未解决；未反馈会话会进入后台统计。
- 管理员介入：无法解决的问题可申请介入，处理后可生成待审核知识草稿。
- 知识审核：草稿需要人工批准，并通过治理评分阈值后才能发布。
- 自动回归：发布知识后自动重建索引并运行评测。
- 备份恢复：支持备份创建、校验、恢复和 SHA-256 manifest。
- 审计日志：登录、配置、问答、备份、治理、评测、发布等关键动作写入 JSONL。

## 关键入口

- `/`：Web 试用入口。
- `/api/trial/entry`：试用入口配置，返回项目缩写规则、附件类型和反馈选项。
- `/api/chat`：问答接口。
- `/api/alerts`：管理员告警中心。
- `/api/jobs`：后台作业状态。
- `/api/knowledge/drafts`：待审核知识草稿。
- `/api/backup/create`、`/api/backup/verify`、`/api/backup/restore`：备份维护。
- `/health`：进程存活检查。
- `/ready`：依赖就绪检查。

## 账号建议

- `admin`：系统配置、用户管理、备份恢复、告警和全部后台能力。
- `reviewer`：知识审核、介入处理、评测和复盘。
- `implementer`：创建会话、上传附件、问答、反馈和申请管理员介入。
- `auditor`：只读查看审计、告警、复盘、备份和存储检查。

## 试用前准备

1. 复制 `config/app.yaml.example` 为 `config/app.yaml`。
2. 配置 LLM 地址、API Key、模型名和管理员密码。
3. 运行 `python -m ops_agent.cli index` 建立索引。
4. 运行 `python -m ops_agent.cli govern --report data/governance-report.json` 确认治理无错误。
5. 启动 Web 服务后，用管理员账号创建实施账号。

## 内部告警说明

当前不接企业微信、钉钉、邮件等外部通知。以下事件会自动沉淀到后台告警：

- `LLM_UNAVAILABLE`：问答或 LLM 连通性测试失败。
- `BACKUP_VERIFY_FAILED`：备份包不存在、manifest 缺失或校验失败。
- `BACKUP_RESTORE_FAILED`：备份恢复失败。
- `JOB_FAILED`：重建索引、治理、评测等后台作业失败。
- `NO_BACKUP`、`BACKUP_TOO_OLD`、`PENDING_FEEDBACK`、`FAILED_TASKS`：运行状态类告警。

## 生产环境仍需外部配套

- HTTPS / 反向代理。
- Windows 服务、systemd、supervisord 或容器守护。
- 异地备份和恢复演练。
- 外部监控和外部通知接入。
- 安装包、升级回滚和发布流水线。
