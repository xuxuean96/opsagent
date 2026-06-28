---
type: reference
component: KMVue
scenario: 99-增补-KMVue运行环境与加密卡误报
priority: P2
tags:
- KMVue
- 99-增补-KMVue运行环境与加密卡误报
- reference
status: active
---

# 增补：KMVue 运行环境与加密卡误报

## 场景

KMVue Linux 环境无法启动，或报加密卡连接不上。

## 重要判断

这不一定是加密卡服务端问题。`kmconvertservice` 服务自身缺少运行时或依赖库时，也可能在 KMVue 侧表现为加密卡连接不上。

## 排查顺序

1. 先直接启动 `kmconvertservice`
2. 查看是否报缺少 `.so`、`GLIBCXX`、`libstdc++` 或其他运行库
3. 检查 `LD_LIBRARY_PATH`
4. 确认 `kmconvertservice` 能独立启动
5. 再排查加密卡服务端进程、端口、防火墙和应用配置

## 结论

KMVue Linux 报加密卡连接不上时，必须把 `kmconvertservice` 运行环境作为前置检查项。

