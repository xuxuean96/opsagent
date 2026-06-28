---
type: reference
component: DDB
scenario: CLI参数说明
priority: P2
tags:
- DDB
- CLI参数说明
- reference
status: active
---

# CLI 参数说明

## 基本格式

```text
DDBExec.exe <SectionName> <IniFilePath> [PreDplFile] [Mode]
```

## 参数含义

| 参数 | 说明 |
|---|---|
| `SectionName` | `DDBExec.ini` 中的段名 |
| `IniFilePath` | 配置文件路径 |
| `PreDplFile` | 可选，前处理 DPL 脚本 |
| `Mode` | 运行位数或模式 |

## 机器人需要确认

- 段名是否存在
- 配置文件是否可读
- 输入文件是否存在
- 输出目录是否可写

