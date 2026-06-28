---
type: reference
component: DDB
scenario: 99-增补-LinuxDDBExec运行环境检查
priority: P2
tags:
- DDB
- 99-增补-LinuxDDBExec运行环境检查
- reference
status: active
---

# 增补：Linux DDBExec 运行环境检查

## 场景

Linux 上 DDBExec 无法启动或执行失败。

## 排查顺序

1. 进入 DDBExec 所在目录
2. 直接执行 `./DDBExec`
3. 查看是否缺少 `.so`、`GLIBCXX`、`libstdc++`
4. 检查 `LD_LIBRARY_PATH`
5. 运行环境正常后，再执行正式业务命令

## 结论

Linux DDBExec 无法启动时，先查运行库和环境变量，再查 XML 配置、输入文件和业务参数。

