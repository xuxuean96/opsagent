from __future__ import annotations


SYNONYMS = {
    "卡起不来": "加密卡 服务启动失败 初始化错误 KmPermitServer",
    "加密狗": "加密卡",
    "连不上卡": "加密卡 连接不上 IP 端口 防火墙",
    "转不出来": "KMVue DDB 转换失败 运行环境 日志",
    "出不了xml": "DDB 生成 XML 失败 配置 路径 权限",
    "起不来": "启动失败 运行环境 进程 端口 日志",
    "报错": "错误 日志 第一条错误",
}


def rewrite_query(question: str, attachment_context: str = "") -> str:
    expanded = [question]
    lower = question.lower()
    for phrase, replacement in SYNONYMS.items():
        if phrase in question or phrase.lower() in lower:
            expanded.append(replacement)
    if "kmvue" in lower and "加密卡" in question:
        expanded.append("KMVue Linux kmconvertservice 运行时 加密卡连接不上")
    if "ddb" in lower and ("xml" in lower or "生成" in question):
        expanded.append("DDBExec 生成 XML 失败 update.xml 配置 日志")
    if attachment_context:
        expanded.append(_important_attachment_terms(attachment_context))
    return "\n".join(item for item in expanded if item.strip())


def _important_attachment_terms(text: str) -> str:
    terms = []
    for marker in ("error", "exception", "failed", "失败", "错误", "缺少", "cannot", "denied", "timeout"):
        if marker in text.lower():
            terms.append(marker)
    return "附件日志 " + " ".join(terms) if terms else "附件日志"
