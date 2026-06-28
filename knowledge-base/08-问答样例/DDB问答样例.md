---
type: faq
component: DDB
scenario: standard-qa
priority: P1
tags:
- DDB
- DDBExec
- XML
- COM
- 组件加载
- DDB问答样例
- faq
status: active
---

# DDB 问答样例

## Q1：DDBExec 生成 XML 失败怎么办

先确认是 GUI 还是 CLI 调用，再看 `KmDdbLog.Txt` 和 `DDBError.log` 第一条错误。

检查顺序：

1. `Mode` 是否为 `OutXml`
2. `ConfigFile` 是否存在
3. `sDataSrcFile` 是否存在
4. 输出目录是否可写
5. 组件是否注册
6. XML 编码是否正确

## Q2：提示不能加载 DpDplCom.Dpl 组件

优先检查 DPL 组件注册。
用管理员权限执行对应注册命令，并确认 32/64 位匹配。

## Q3：提示拒绝访问或 Process 处理 XML 出错

先用管理员权限运行 DDBExec，再检查输入输出目录权限。
如果是服务调用，还要检查服务账号是否有访问文件路径的权限。

## Q4：输出 XML 是空的

常见原因是输入数据为空、配置映射不完整、数据源类型选错或输出路径不可写。
先用 GUI 测试桩验证同一配置和同一输入文件。

## Q5：注册 DLL 报不兼容

通常是 32/64 位 `regsvr32` 混用。
确认 DLL 位数，再使用对应位数的注册工具。

