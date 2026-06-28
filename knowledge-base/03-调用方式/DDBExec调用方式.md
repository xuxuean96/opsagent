---
type: reference
component: DDB
scenario: DDBExec调用方式
priority: P2
tags:
- DDB
- DDBExec调用方式
- reference
status: active
---

# DDBExec 调用方式

## 两种典型方式

### 1. GUI 测试

- 适合验证配置和结果
- 适合排查单个问题
- 适合快速定位日志

### 2. CLI 调用

- 适合自动化和生产环境
- 适合批处理和服务调用
- 适合由机器人生成命令模板

## 调用时必须确认

- 数据源类型
- 操作模式
- 配置文件路径
- 输入文件路径
- 输出文件路径

## 机器人回答模板

1. 你现在用的是 GUI 还是 CLI
2. 传入的配置文件是否存在
3. 输入文件路径是否正确
4. 输出目录是否可写

