---
type: runbook
component: Creo
scenario: 连接环境失败-1
priority: P1
tags:
- Creo
- ProE
- PRO_COMM_MSG_EXE
- 环境变量
- 机器名中文
- DDB
- Creo-连接环境失败-1
- runbook
status: active
---

# Creo-连接环境失败-1

## 适用场景

Creo/ProE 导入或调用时报“连接 Creo 环境失败，错误码 -1”。

## 可能原因

| 优先级 | 原因 | 判断依据 |
|---|---|---|
| P1 | `PRO_COMM_MSG_EXE` 配置错误 | 找不到通信程序 |
| P1 | PATH 或 `KMSoftPath` 不完整 | 组件或通信程序加载失败 |
| P1 | 机器名为中文 | Creo 通信环境异常 |
| P2 | 注册表 PTC 节点异常 | Wow6432Node 下空节点影响加载 |

## 先问用户

1. Creo 版本是多少
2. `PRO_COMM_MSG_EXE` 指向哪里
3. 机器名是否包含中文
4. 日志第一条 Creo 相关错误是什么

## 检查步骤

1. 检查 `PRO_COMM_MSG_EXE`
2. 检查 PATH 和 `KMSoftPath`
3. 确认机器名不是中文
4. 检查 PTC 相关注册表空节点
5. 重新运行导入或 DDBExec

## 验证方式

- 能连接 Creo 环境
- 不再报错误码 `-1`
- 生成 XML 或执行目标操作成功

