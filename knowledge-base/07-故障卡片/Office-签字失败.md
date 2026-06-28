---
type: runbook
component: Office
scenario: 签字失败
priority: P2
tags:
- Office
- Word
- Excel
- 签字
- COM
- 许可证
- DDB
- Office-签字失败
- runbook
status: active
---

# Office-签字失败

## 适用场景

Word 或 Excel 签字失败、签不上、Office 许可证异常、图片签字不显示。

## 可能原因

| 优先级 | 原因 | 判断依据 |
|---|---|---|
| P1 | Office 未安装或许可证异常 | Office 打开时报许可问题 |
| P1 | COM 注册异常 | 报无效指针或找不到 Application |
| P2 | 表格范围配置过小 | Word 文字签字签不上 |
| P2 | 组件版本混乱 | 文字可签，图片签不上 |

## 先问用户

1. 是 Word 还是 Excel
2. 是文字签字还是图片签字
3. Office 是否能正常打开
4. 报错全文和日志是什么

## 检查步骤

1. 确认 Office 许可证正常
2. 确认 Office COM 可用
3. 检查 update.xml
4. 检查签字位置或表格范围
5. 确认 DDB 目录 DLL 版本一致

## 验证方式

- 签字内容写入目标文件
- 打开文件能看到文字或图片
- 日志无 Office COM 错误

