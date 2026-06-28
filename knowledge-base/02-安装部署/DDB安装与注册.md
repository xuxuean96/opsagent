---
type: reference
component: DDB
scenario: DDB安装与注册
priority: P2
tags:
- DDB
- DDB安装与注册
- reference
status: active
---

# DDB 安装与注册

## 安装要点

- 公共组件目录要完整
- DDB 组件要按位数注册
- `DDBExec.exe` 和相关 DLL 要在同一套目录体系里

## 常见安装失败点

- 运行库缺失
- DLL 注册失败
- 32/64 位混用
- 公共组件被覆盖一部分

## 首轮排查

1. 确认系统位数
2. 确认 DDB 目录完整
3. 确认 DLL 是否注册
4. 确认是否有管理员权限
5. 确认日志是否生成

