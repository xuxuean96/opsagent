from pathlib import Path
import re
import shutil


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "集成组件.md"
OUT = ROOT / "knowledge-base" / "10-原文拆分"


SECTION_MAP = [
    ("附录 AA", "AA-系统配置项速查"),
    ("附录 BB", "BB-版本升级注意事项"),
    ("附录 CC", "CC-2026现场问题案例库"),
    ("附录 DD", "DD-系统架构与组件关系"),
    ("一、通用部署问题速查", "01-通用部署问题速查"),
    ("二、DDB 测试桩全流程使用", "02-DDB测试桩全流程使用"),
    ("三、DDB 平台配置项详", "03-DDB平台配置项详解"),
    ("三·补：DDB 配置项完整参考", "03A-DDB配置项完整参考"),
    ("四、加密卡部署排查", "04-加密卡部署排查"),
    ("五、KMVue 集成环境部署", "05-KMVue集成环境部署"),
    ("六、各", "06-各CAD集成环境配置速查"),
    ("附录 A", "A-DDB框架架构"),
    ("附录 B", "B-关键文件路径"),
    ("附录 C", "C-调试技巧"),
    ("附录 D", "D-实战操作指南"),
    ("附录 E", "E-各CAD软件完整部署清单"),
    ("附录 F", "F-现场排查流程"),
    ("附录 G", "G-快速参考卡"),
    ("附录 H", "H-同义词与口语映射表"),
    ("附录 I", "I-用户提问模式与Agent应答策略"),
    ("附录 J", "J-DDB日志解读完全指南"),
    ("附录 K：签字功能", "K-签字功能完整指南"),
    ("录 K", "K2-CAD坐标测量指南"),
    ("附录 M", "M-转PDF完整指南"),
    ("附录 N", "N-轻量化完整指南"),
    ("附录 O：update.xml", "O-update入口参数编写指南"),
    ("附录 O：现场案例库", "P-现场案例库"),
    ("附录 P：特殊场景", "P2-特殊场景处理指南"),
    ("附录 Q", "Q-版本管理指南"),
    ("附录 R", "R-现场信息收集清单"),
    ("附录 T", "T-LinuxDDB部署完整指南"),
    ("附录 U", "U-KMVue集成部署完整指南"),
    ("附录 V", "V-加密卡授权管理完整指南"),
    ("附录 W", "W-CLOUD系统配置与排查指南"),
    ("附录 X", "X-数据库常见报错与排查"),
    ("附录 Y", "Y-文件服务与本地代理配置"),
    ("附录 Z", "Z-打印配置完全指南"),
]


def slug_title(title: str) -> str:
    cleaned = re.sub(r"[#`*_<>|?\"/:\\]", "", title).strip()
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = cleaned.replace("�", "")
    return cleaned[:60] or "section"


def detect_dir(title: str) -> str:
    if "CAD" in title and ("¼" in title or "录 K" in title):
        return "K2-CAD坐标测量指南"
    for marker, folder in SECTION_MAP:
        if marker in title:
            return folder
    return "ZZ-未分类"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    lines = text.splitlines()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)

    sections = []
    current = None
    buffer = []

    for line in lines:
        if line.startswith("## "):
            if current is not None:
                sections.append((current, buffer))
            current = line[3:].strip()
            buffer = [line]
        elif current is not None:
            buffer.append(line)
    if current is not None:
        sections.append((current, buffer))

    index_lines = [
        "# 原文拆分索引",
        "",
        "本目录按原始 `集成组件.md` 的二级章节拆分，作为完整追溯库。",
        "",
        "优先给机器人检索使用的是上层的提炼文档；本目录用于兜底查原文上下文。",
        "",
    ]

    counters = {}
    for title, content in sections:
        folder_name = detect_dir(title)
        folder = OUT / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        count = counters.get(folder_name, 0) + 1
        counters[folder_name] = count
        file_name = f"{count:02d}-{slug_title(title)}.md"
        path = folder / file_name
        body = "\n".join(content).rstrip() + "\n"
        path.write_text(body, encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        index_lines.append(f"- [{title}](../../{rel})")

    (OUT / "00-索引.md").write_text("\n".join(index_lines) + "\n", encoding="utf-8")
    print(f"split {len(sections)} sections into {OUT}")


if __name__ == "__main__":
    main()
