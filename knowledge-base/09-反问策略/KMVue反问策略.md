---
type: strategy
component: KMVue
scenario: clarification
priority: P1
tags:
- KMVue
- kmconvertservice
- Linux
- 加密卡
- 运行环境
- 反问策略
- KMVue反问策略
- strategy
status: active
---

# KMVue 反问策略

## 用户说“KMVue Linux 启动失败”

先问：

1. 是 Nginx、前端、ODA，还是 `kmconvertservice` 启动失败
2. 是否直接启动过 `kmconvertservice`
3. 直接启动时报什么错
4. 是否缺少 `.so`、`GLIBCXX`、`libstdc++` 或其他运行库
5. `LD_LIBRARY_PATH` 是否配置正确

## 用户说“KMVue 报加密卡连接不上”

先不要只按加密卡处理，先问：

1. `kmconvertservice` 是否能独立启动
2. `kmconvertservice` 日志里是否有运行时缺失
3. 加密卡服务端进程和端口是否正常
4. KMVue/CLOUD 配置的加密卡 IP 和端口是否正确

## 判断原则

如果 `kmconvertservice` 自身都不能启动，应先修复转换服务运行环境。
转换服务正常后，再继续排查加密卡服务端、端口、防火墙和应用配置。
