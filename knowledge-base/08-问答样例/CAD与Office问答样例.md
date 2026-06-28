---
type: faq
component: CAD-Office
scenario: standard-qa
priority: P2
tags:
- Creo
- Excel
- Word
- PDF
- 签字
- CAD
- DDB
- CAD与Office问答样例
- faq
status: active
---

# CAD 与 Office 问答样例

## Q1：Creo 连接环境失败，错误码 -1

优先检查 `PRO_COMM_MSG_EXE`、PATH、`KMSoftPath` 和机器名。
机器名不能是中文，通信程序路径必须指向正确 Creo 安装目录。

## Q2：Excel 转 PDF 报参数错误

先确认 Office、Adobe 或 PDF 输出组件是否安装完整，再检查打印机环境和输出目录权限。

## Q3：Word 签字提示 Office 无法验证许可证

这是 Office 许可证问题优先，不要先改 DDB 配置。
先修复或重新安装 Office，再重试签字。

## Q4：SolidWorks 签字成功但打开没有签字

先检查工程图里是否定义了文本框或注释占位，例如 `$PRPSHEET:{设计}`。
如果没有占位，DDB 可能执行成功但实际没有写入位置。

## Q5：CATIA 二维工程图转 PDF 报未找到注册类

优先检查是否存在多页工程图。
可删除多余页，或配置 CATIA 只输出当前页。

## Q6：KMVue Linux 报加密卡连接不上

不一定是加密卡本身的问题。
先直接启动 `kmconvertservice`，确认转换服务是否缺少运行时或依赖库。只有 `kmconvertservice` 能正常启动后，再继续排查加密卡服务端、端口、防火墙和配置。

## Q7：CLOUD 服务启动不了

先查 Java 环境和版本。
确认启动脚本实际使用的 Java 路径，再看日志中是否有 Java 版本、class、jar 或运行时错误。
