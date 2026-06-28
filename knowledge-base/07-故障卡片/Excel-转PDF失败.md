---
type: runbook
component: Excel
scenario: 转PDF失败
priority: P1
tags:
- Excel
- PDF
- Office
- Adobe
- SaveAsPDFandXPS
- DDB
- Excel-转PDF失败
- runbook
status: active
---

# Excel-转PDF失败

## 适用场景

Excel 转 PDF 时报参数错误、未安装打印机、转换失败或没有输出 PDF。

## 可能原因

| 优先级 | 原因 | 判断依据 |
|---|---|---|
| P1 | Office 未安装或异常 | Excel COM 不可用 |
| P1 | PDF 组件缺失 | 缺少 Adobe 或 SaveAsPDFandXPS |
| P2 | 打印机环境异常 | 报未安装打印机 |
| P2 | 输出目录权限不足 | 无 PDF 输出 |

## 先问用户

1. 是否安装 Office 或 WPS
2. 是否安装 Adobe 或 PDF 输出组件
3. 报错全文是什么
4. 输出目录是否可写

## 检查步骤

1. 确认 Office 可正常打开 Excel
2. 检查 Excel COM 注册
3. 检查 PDF 组件
4. 检查打印机环境
5. 检查输出路径权限

## 验证方式

- Excel 能独立转 PDF
- DDB 转 PDF 成功输出文件
- 日志无参数错误或打印机错误

