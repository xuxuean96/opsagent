---
type: strategy
component: DDB
scenario: clarification
priority: P1
tags:
- DDB
- 反问策略
- DDBExec
- XML
- 日志
- DDB反问策略
- strategy
status: active
---

# DDB 反问策略

## 用户说“DDB 报错”

先问：

1. 数据源类型是什么，例如 DWG、Creo、CATIA、Excel
2. 操作模式是什么，例如 `OutXml`、`Update`、`Topdf`
3. 是 GUI 测试桩还是 CLI 调用
4. `KmDdbLog.Txt` 第一条错误是什么
5. `DDBError.log` 或 `DDBError.txt` 内容是什么

## 用户说“Linux DDBExec 启动失败”

先问：

1. 是否直接执行过 `./DDBExec`
2. 是否报缺少 `.so`、`GLIBCXX`、`libstdc++`
3. `LD_LIBRARY_PATH` 是否包含依赖目录
4. 操作系统版本和 glibc 版本是多少

## 用户说“生成 XML 失败”

先问：

1. `DDBExec.ini` 对应段名是什么
2. `ConfigFile` 路径是什么
3. 输入文件路径是什么
4. 输出路径是什么
5. 是否能用 GUI 测试桩复现

## 用户说“组件加载失败”

先问：

1. 具体哪个 DLL 或组件加载失败
2. 32 位还是 64 位
3. 是否最近覆盖过 common 目录
4. 是否管理员权限注册过组件
