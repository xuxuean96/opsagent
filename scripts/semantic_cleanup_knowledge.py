from __future__ import annotations

import re
from pathlib import Path


ROOT = Path("knowledge-base")
REPORT = Path("data/semantic-cleanup-report.md")


CANONICAL_FILES = {
    "00-README.md": """---
type: overview
component: knowledge-base
scenario: knowledge-base-entry
priority: P1
tags: [knowledge-base, 目录, 使用规范]
status: active
---

# 运维组件问答知识库

本知识库服务于“组件安装 / 调用 / 报错排查助手”。机器人回答问题时应优先使用结构化故障卡片、问答样例和报错排查文档；原文拆分文档只作为补充检索和追溯来源。

## 使用目标

1. 快速识别组件、系统环境、调用方式和错误关键词。
2. 优先给出可执行检查项，而不是泛泛解释。
3. 报错类问题按“现象 -> 可能原因 -> 判断依据 -> 处理步骤 -> 验证方式”组织。
4. 信息不足时先反问最少必要信息，不一次性展开过多方向。
5. 涉及重启、覆盖、删除、恢复等操作时，必须先提示备份和风险确认。

## 推荐检索顺序

1. `07-故障卡片/`：结构化 Runbook，优先用于生成排查步骤。
2. `08-问答样例/`：真实问法和标准回答风格。
3. `04-报错排查/`：按现象、报错和环境分类的排查说明。
4. `09-反问策略/`：信息不足时的追问规则。
5. `02-安装部署/`、`03-调用方式/`、`05-日志与证据/`：补充部署、调用和证据采集细节。
6. `10-原文拆分/`：保留原始上下文，作为兜底追溯材料。

## 维护原则

- 一个文件只解决一个主主题。
- 同一问题只保留一个标准答案，其他文件通过引用补充。
- 新增内容必须包含适用组件、触发场景、判断依据、处理步骤和验证方式。
- 自动沉淀的草稿必须先人工审核，确认无客户敏感信息后再发布。
""",
    "12-规范/机器人回答结构.md": """---
type: standard
component: knowledge-base
scenario: answer-format
priority: P1
tags: [机器人, 回答结构, 排障, 知识库]
status: active
---

# 机器人回答结构

## 信息充分时

按以下顺序回答：

1. 判断结论：说明最可能的故障方向。
2. 可能原因：最多列出 3 个优先原因。
3. 检查步骤：每个原因必须给出明确检查方法。
4. 处理步骤：命令使用 Markdown 代码块。
5. 验证方式：说明如何确认问题已解决。
6. 需要补充的证据：列出日志、截图、配置或环境信息。

## 信息不足时

不要直接给大段方案，优先反问最少必要信息：

1. 组件名称和版本。
2. 操作系统和位数。
3. 调用方式或启动方式。
4. 报错全文。
5. 日志中的第一条错误。

## 风险约束

- 不绕过 LLM 直接给答案。
- 知识库未命中时，只说明缺少依据并要求补充信息。
- 涉及重装、覆盖、删除、恢复、停止服务前，必须提示备份和影响范围。
- 服务端正常但客户端异常时，先查网络、配置、权限和防火墙，再考虑重装。
""",
    "04-报错排查/高频问题清洗版.md": """---
type: runbook
component: 多组件
scenario: high-frequency-issues
priority: P1
tags: [高频问题, DDB, KMVue, CLOUD, eCol, 加密卡, Office, CAD]
status: active
---

# 高频问题标准排查

## 服务无法启动

服务无法启动时，先确认该软件自身运行环境是否满足要求，再继续排查授权、端口、配置和日志。

1. CLOUD：检查 Java 环境和版本。
2. Linux DDB：直接执行 `DDBExec`，确认是否缺少运行库。
3. KMVue Linux：直接启动 `kmconvertservice`，确认是否缺少运行时。
4. Linux 加密卡：执行 `KmPermitServer_Linux_Server.sh` 或 `KmPermitServer_Linux`，确认是否缺少运行库。

## KMVue Linux 报加密卡连接不上

不要只按加密卡方向排查。若 `kmconvertservice` 缺少运行时或无法独立启动，也可能表现为 KMVue 报加密卡连接不上。

排查顺序：

1. 先确认 `kmconvertservice` 能独立启动。
2. 再检查加密卡服务 IP、端口、授权和客户端配置。
3. 最后检查服务端和客户机防火墙、跨网段策略和安全软件。

## 加密卡服务端启动成功但应用不可用

如果加密卡服务启动成功，但 eCol、CLOUD 等应用仍无法使用，优先怀疑应用程序中配置的加密卡地址、端口或客户端模式不正确。

判断依据：

1. 独立客户端可以连接加密卡服务端。
2. 加密卡服务端进程和端口正常。
3. 只有某个业务程序无法调用授权。

处理步骤：

1. 检查业务程序配置中的加密卡服务器 IP 和端口。
2. 确认客户机访问的是正确服务端。
3. 保存配置后重启业务程序并验证。

## 加密卡进程存在但客户机连不上

进程存在不代表客户机一定能访问端口。优先检查服务端防火墙、客户机防火墙、安全软件和跨网段网络策略。

## 加密卡启动失败

启动失败时先检查是否已存在加密卡进程，或端口是否被占用。已有正常进程时不要重复启动。

## DDB 生成 XML 失败

优先检查 `Mode`、`ConfigFile`、输入文件、输出目录和日志第一条错误，再检查组件注册、位数匹配和 XML 编码。

## DDB 组件加载失败

优先检查 COM 注册、32/64 位匹配、依赖 DLL 和 `common` 目录是否完整覆盖。

## Creo 连接环境失败 -1

优先检查 `PRO_COMM_MSG_EXE`、`PATH`、`KMSoftPath` 和机器名。机器名不应使用中文。

## Excel 转 PDF 失败

优先检查 Office、Adobe 或 PDF 输出组件、打印机环境和输出目录权限。

## Word / Excel 签字失败

优先检查 Office 许可证、Office COM、`update.xml`、签字位置和 DDB DLL 版本一致性。
""",
}


NORMALIZATION_RULES = [
    (re.compile(r"(?i)\bcloud\b"), "CLOUD"),
    (re.compile(r"(?i)\becol\b"), "eCol"),
    (re.compile(r"(?i)\bkmvue\b"), "KMVue"),
    (re.compile(r"(?i)\bddbexec\b"), "DDBExec"),
    (re.compile(r"不要只看"), "不要只依据"),
    (re.compile(r"先看一下"), "先检查"),
    (re.compile(r"大概|可能是可能|试试看"), "优先判断"),
]


def main() -> None:
    changes: list[str] = []
    for rel, content in CANONICAL_FILES.items():
        path = ROOT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        before = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        if before != content:
            path.write_text(content, encoding="utf-8")
            changes.append(f"- 重写标准文档：`{rel}`")

    for path in sorted(ROOT.rglob("*.md")):
        before = path.read_text(encoding="utf-8", errors="ignore")
        after = normalize_text(before)
        if after != before:
            path.write_text(after, encoding="utf-8")
            changes.append(f"- 统一术语和旧话术：`{path.relative_to(ROOT).as_posix()}`")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(render_report(changes), encoding="utf-8")
    print(f"semantic cleanup changed {len(changes)} files")


def normalize_text(text: str) -> str:
    result = text.replace(" -> ", " -> ")
    for pattern, replacement in NORMALIZATION_RULES:
        result = pattern.sub(replacement, result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"[ \t]+$", "", result, flags=re.M)
    return result


def render_report(changes: list[str]) -> str:
    body = "\n".join(changes) if changes else "- 本次未发现需要修改的语义项。"
    return f"""# 知识库语义清洗报告

## 清洗范围

- 统一入口说明、机器人回答结构、高频问题标准排查。
- 统一 eCol、CLOUD、KMVue、DDBExec 等术语大小写。
- 收敛“先看一下”“试试看”等口语化旧话术。
- 保留人工审核发布流程，不自动发布草稿。

## 修改记录

{body}
"""


if __name__ == "__main__":
    main()
