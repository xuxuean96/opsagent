# 运维问答 Agent 平台

这是一个面向组件安装、调用、报错排查的运维问答 Agent。当前版本包含 Web 控制台、RAG 检索、多轮问答、SQLite 向量库、模型配置管理、知识库治理、效果评测、任务状态追踪、会话反馈、管理员介入和知识沉淀闭环。

## 当前能力

- Web 控制台：问答、模型配置、知识库、效果评测、会话后台、管理员介入、任务日志、复盘统计。
- 会话准入：对话开始前必须填写项目缩写和实施人员；项目缩写只允许拼音首字母，便于追溯和复盘。
- 附件上传：支持 txt、log、xml、json、ini、conf 等文本文件；支持图片上传并尝试 OCR。
- OCR：图片识别通过可选的 `pytesseract` + `Pillow` 适配；未安装 OCR 运行时也不会阻断问答，会返回清晰提示。
- RAG：Markdown 知识库切片、索引持久化、SQLite 向量库、关键词和向量混合检索、重排和去重。
- LLM 接入：OpenAI-compatible 接口，支持 GPT、GLM、DeepSeek、Qwen 等兼容模型。
- 强依赖 LLM：服务启动时会检查 LLM 可访问性，LLM 不可用则服务不可用；兜底只用于交互体验和错误说明，不绕过 LLM 给答案。
- 输出规范：回答包含排查步骤、命令块、风险提示、验证方式和文档引用。
- 会话反馈：记录已解决、部分解决、未解决和待反馈状态；后台可筛选未反馈会话。
- 管理员介入：知识库多轮问答无法解决时可申请管理员介入，后台记录介入单。
- 知识沉淀：已解决会话可生成候选知识草稿；管理员处理后可生成草稿；人工审核后发布到正式知识库。
- 治理与评测：支持知识库治理报告、效果评测数据、复盘统计和任务记录。

## 配置

复制配置文件：

```powershell
Copy-Item config/app.yaml.example config/app.yaml
```

设置 API Key：

```powershell
$env:OPENAI_API_KEY="你的 API Key"
```

核心配置：

```yaml
llm:
  provider: openai-compatible
  base_url: https://api.openai.com/v1
  api_key: ${OPENAI_API_KEY}
  model: gpt-4.1-mini

embedding:
  provider: local

vector_store:
  provider: sqlite
  path: data/vector_store.sqlite3

session:
  store_path: data/sessions.jsonl
  upload_dir: data/uploads
  draft_dir: knowledge-base/13-待审核
```

## 启动

```powershell
pip install -r requirements.txt
python -m ops_agent.cli index
python -m uvicorn ops_agent.app:app --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## OCR 依赖

图片 OCR 是可选增强能力。要让截图、照片自动提取文字，需要安装：

```powershell
pip install Pillow pytesseract
```

同时需要本机安装 Tesseract OCR 运行时，并配置中文语言包 `chi_sim`。如果未安装，系统仍会保存图片附件，并提示当前环境没有可用 OCR 引擎或未识别到文字。

## 常用命令

重建索引和向量库：

```powershell
python -m ops_agent.cli index
```

知识库治理：

```powershell
python -m ops_agent.cli govern --report data/governance-report.md
python -m ops_agent.cli govern --report data/governance-report.json
python -m ops_agent.cli govern --strict --report data/governance-report.md
```

效果评测：

```powershell
python -m ops_agent.cli eval
```

评测命令需要真实 LLM 可访问。

## 会话闭环

对话开始前必须创建会话：

- 项目缩写：只能填写拼音首字母，例如 `ZJDL`。
- 实施人员：实施人员姓名。
- 组件：可选，例如 `DDB`、`KMVue`、`加密卡`。

会话过程中可以上传日志或截图。文本类附件会自动提取内容；图片会尝试 OCR，OCR 不可用时保留附件并给出提示。

每个会话都应记录解决反馈。没有反馈的会话会保留为 `pending_feedback`，管理员可以在“会话后台”筛查。

如果知识库多轮对话仍无法解决，可以申请管理员介入。管理员处理时填写问题原因和解决方案，系统会生成 `knowledge-base/13-待审核` 下的知识草稿。草稿经过人工审核、治理检查后，再发布到正式知识库。

## 知识沉淀流程

1. 用户反馈本次会话已解决。
2. 点击“生成候选知识”，系统根据问题、答案、附件摘要生成 `status: draft` 的候选草稿。
3. 管理员审核草稿，补齐适用组件、场景、判断依据、处理步骤和验证方式。
4. 执行知识库治理检查。
5. 审核通过后发布到 `knowledge-base/07-故障卡片` 等正式目录，状态改为 `active`。
6. 重建索引，让新知识进入 RAG 检索。

## 工程结构

```text
ops_agent/
  app.py          Web API 和控制台接口
  cli.py          索引、治理、评测命令
  config.py       配置加载与保存
  embedding.py    Embedding 接入
  evaluation.py   效果评测
  governance.py   知识库治理
  indexing.py     Markdown 切片和索引
  llm.py          LLM 接入与健康检查
  orchestrator.py 问答编排
  retrieval.py    混合检索
  sessions.py     会话、附件、反馈、管理员介入、知识草稿
  tasks.py        任务状态追踪
  vector_store.py SQLite 向量库
web/              控制台前端
knowledge-base/   运维知识库
tests/            自动化测试
```

## 当前治理基线

治理报告输出到：

```text
data/governance-report.md
data/governance-report.json
```

`warnings` 主要来自历史文档缺少 YAML front matter 或必填元数据。它们不阻断当前使用，但建议后续分批补齐。
