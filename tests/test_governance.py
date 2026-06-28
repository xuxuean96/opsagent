from pathlib import Path

from ops_agent.governance import KnowledgeGovernance, Severity


def write_doc(root: Path, name: str, body: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_governance_accepts_well_formed_runbook(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(
        kb,
        "07-故障卡片/加密卡-启动失败.md",
        """---
type: runbook
component: 加密卡
scenario: 启动失败
priority: P1
tags: [加密卡, 启动失败]
status: active
---
# 加密卡启动失败

## 典型现象

服务启动失败，日志提示初始化错误。

## 处理步骤

1. 先检查进程是否已存在。
2. 再检查端口、防火墙和运行环境。
""",
    )

    report = KnowledgeGovernance(kb).inspect()

    assert report.file_count == 1
    assert report.error_count == 0
    assert report.score == 100


def test_governance_reports_missing_metadata_and_short_content(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "04-报错排查/短文档.md", "# 短文档\n\n太短")

    report = KnowledgeGovernance(kb).inspect()

    codes = {issue.code for issue in report.issues}
    assert "MISSING_FRONT_MATTER" in codes
    assert "CONTENT_TOO_SHORT" in codes
    assert report.warning_count >= 1


def test_governance_detects_duplicate_documents(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    body = """---
type: faq
component: DDB
scenario: 生成XML失败
priority: P1
tags: [DDB, XML]
status: active
---
# DDB 生成 XML 失败

需要检查配置文件路径、权限和日志第一条错误。
"""
    write_doc(kb, "06-FAQ/a.md", body)
    write_doc(kb, "06-FAQ/b.md", body)

    report = KnowledgeGovernance(kb).inspect()

    duplicate_issues = [issue for issue in report.issues if issue.code == "DUPLICATE_CONTENT"]
    assert duplicate_issues
    assert duplicate_issues[0].severity == Severity.WARNING


def test_governance_report_can_render_markdown(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "README.md", "# 知识库")

    report = KnowledgeGovernance(kb).inspect()
    markdown = report.to_markdown()

    assert "# 知识库治理报告" in markdown
    assert "质量分" in markdown


def test_governance_report_can_render_json(tmp_path: Path) -> None:
    kb = tmp_path / "kb"
    write_doc(kb, "README.md", "# 知识库")

    report = KnowledgeGovernance(kb).inspect()
    payload = report.to_dict()

    assert payload["file_count"] == 1
    assert payload["issues"]
