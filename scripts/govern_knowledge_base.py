from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path("knowledge-base")
FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
REQUIRED = ("type", "component", "scenario", "priority", "tags", "status")

TYPE_BY_PREFIX = {
    "00-README.md": "overview",
    "01-概览": "overview",
    "02-安装部署": "reference",
    "03-调用方式": "reference",
    "04-报错排查": "runbook",
    "05-日志与证据": "reference",
    "06-FAQ": "faq",
    "07-故障卡片": "runbook",
    "08-问答样例": "faq",
    "09-反问策略": "strategy",
    "10-原文拆分": "reference",
    "11-测试集": "testcase",
    "12-规范": "standard",
    "13-待审核": "runbook",
    "99-附录": "reference",
}

COMPONENT_ALIASES = {
    "DDB": "DDB",
    "DDBExec": "DDBExec",
    "KMVue": "KMVue",
    "CLOUD": "CLOUD",
    "eCol": "eCol",
    "Office": "Office",
    "Excel": "Excel",
    "Creo": "Creo",
    "CAD": "CAD",
    "CATIA": "CATIA",
    "SolidWorks": "SolidWorks",
    "加密卡": "加密卡",
    "数据库": "数据库",
    "文件服务": "文件服务",
}


def main() -> None:
    changed = 0
    for path in sorted(ROOT.rglob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        metadata, body = split_front_matter(text)
        rel = path.relative_to(ROOT).as_posix()
        inferred = infer_metadata(path, body)
        for key in REQUIRED:
            metadata.setdefault(key, inferred[key])
        metadata["type"] = normalize_type(rel, str(metadata["type"]))
        metadata["priority"] = normalize_priority(str(metadata["priority"]))
        metadata["status"] = normalize_status(str(metadata["status"]))
        metadata["tags"] = normalize_tags(metadata.get("tags"), inferred["tags"])
        if not has_h1(body):
            body = f"# {title_from_path(path)}\n\n{body.lstrip()}"
        new_text = render_front_matter(metadata) + body.lstrip()
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
    print(f"governed {changed} markdown files")


def split_front_matter(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        metadata = {}
    return metadata, text[match.end() :]


def infer_metadata(path: Path, body: str) -> dict:
    rel = path.relative_to(ROOT).as_posix()
    doc_type = normalize_type(rel, "")
    title = title_from_path(path)
    component = infer_component(rel, body)
    scenario = title
    priority = "P2"
    if doc_type in {"overview", "standard", "testcase"}:
        priority = "P1"
    if "P0" in rel or "高频" in rel or "启动失败" in rel:
        priority = "P1"
    tags = [component, scenario, doc_type]
    return {
        "type": doc_type,
        "component": component,
        "scenario": scenario,
        "priority": priority,
        "tags": tags,
        "status": "active",
    }


def normalize_type(rel: str, current: str) -> str:
    for prefix, doc_type in TYPE_BY_PREFIX.items():
        if rel == prefix or rel.startswith(prefix + "/"):
            return doc_type
    return current if current in {"runbook", "faq", "reference", "strategy", "testcase", "standard", "overview"} else "reference"


def normalize_priority(value: str) -> str:
    return value if value in {"P0", "P1", "P2", "P3"} else "P2"


def normalize_status(value: str) -> str:
    return value if value in {"active", "draft", "deprecated"} else "active"


def normalize_tags(value, fallback: list[str]) -> list[str]:
    if isinstance(value, list):
        tags = [str(item).strip() for item in value if str(item).strip()]
    elif isinstance(value, str) and value.strip():
        tags = [item.strip() for item in value.split(",") if item.strip()]
    else:
        tags = []
    for item in fallback:
        if item and item not in tags:
            tags.append(item)
    return tags or ["knowledge-base"]


def infer_component(rel: str, body: str) -> str:
    haystack = f"{rel}\n{body[:2000]}"
    found = [component for marker, component in COMPONENT_ALIASES.items() if marker in haystack]
    if found:
        return found[0]
    if rel.startswith("11-测试集") or rel.startswith("12-规范") or rel.startswith("00-README"):
        return "knowledge-base"
    if rel.startswith("99-附录"):
        return "通用"
    return "多组件"


def title_from_path(path: Path) -> str:
    return path.stem.replace("_", " ").strip() or "未命名文档"


def has_h1(body: str) -> bool:
    return any(line.startswith("# ") for line in body.splitlines())


def render_front_matter(metadata: dict) -> str:
    ordered = {key: metadata[key] for key in REQUIRED}
    for key, value in metadata.items():
        if key not in ordered:
            ordered[key] = value
    return "---\n" + yaml.safe_dump(ordered, allow_unicode=True, sort_keys=False).strip() + "\n---\n\n"


if __name__ == "__main__":
    main()
