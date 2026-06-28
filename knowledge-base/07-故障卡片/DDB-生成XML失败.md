---
type: runbook
component: DDB
scenario: 生成XML失败
priority: P1
tags:
- DDB
- OutXml
- XML
- DDBExec
- DDBError
- DDB-生成XML失败
- runbook
status: active
---

# DDB-生成XML失败

## 适用场景

使用 DDBExec 或平台导入时，生成 XML 失败、输出为空或没有生成输出文件。

## 可能原因

| 优先级 | 原因 | 判断依据 |
|---|---|---|
| P1 | XML 配置路径错误 | 日志提示读取配置失败 |
| P1 | 输入文件不存在或无权限 | 日志提示打开数据源失败 |
| P1 | 组件注册或依赖异常 | 日志提示组件加载失败 |
| P2 | 输出目录不可写 | 没有输出文件或权限错误 |
| P2 | 配置映射不完整 | 输出为空或结构不完整 |

## 先问用户

1. 用 GUI 还是 CLI
2. `Mode` 是否为 `OutXml`
3. `ConfigFile`、`sDataSrcFile`、`OutputFile` 分别是什么
4. `KmDdbLog.Txt` 和 `DDBError.log` 第一条错误是什么

## 检查步骤

1. 用 GUI 测试桩复现
2. 检查配置文件路径
3. 检查输入文件路径和权限
4. 检查输出目录权限
5. 检查组件注册和位数
6. 根据日志定位具体驱动

## 验证方式

- 成功生成 XML
- 日志返回值正常
- 输出文件内容非空且结构正确

