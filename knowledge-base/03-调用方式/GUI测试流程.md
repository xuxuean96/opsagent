---
type: reference
component: DDB
scenario: GUI测试流程
priority: P2
tags:
- DDB
- GUI测试流程
- reference
status: active
---

# GUI 测试流程

## 适用场景

- 快速验证配置
- 排查单个文件问题
- 观察 DDB 是否正常加载配置

## 典型流程

1. 启动 `DDBExec.exe`
2. 选择方案
3. 选择数据源类型
4. 选择处理模式
5. 指定配置文件
6. 指定输入文件
7. 执行并查看输出

## 排障价值

- 可以直接观察加载过程
- 更容易拿到首条错误
- 适合先定位是配置错还是执行链错

