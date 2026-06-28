---
type: faq
component: DDB
scenario: 报错FAQ
priority: P2
tags:
- DDB
- 报错FAQ
- faq
status: active
---

# 报错 FAQ

## 先看什么

1. 报错关键词
2. 日志首条错误
3. 配置文件
4. 环境变量
5. 组件位数

## 先别做什么

- 不要先改一堆配置
- 不要先换多个版本
- 不要先重装全部组件

## 加密卡启动成功但系统还是不能用怎么办

先不要重装加密卡。
如果加密卡服务端已经正常启动，优先检查 eCol/CLOUD 中配置的加密卡服务器地址和端口是否正确。

重点看：

- IP 是否还是旧服务器地址
- 端口是否和 `KmPermitServer` 一致
- CLOUD 的 `kmwp.encryption.EncryptionCard.mode` 是否匹配
- 修改配置后是否重启了应用服务

## 加密卡进程存在但客户机连不上怎么办

先查防火墙和端口连通性。

重点看：

- 服务端防火墙是否放行端口
- 客户机防火墙或安全软件是否拦截
- 默认端口 `5600` 是否能从客户机访问
- 跨网段时路由、ACL 或安全组是否放行

## 加密卡启动失败先看什么

先看是否已经存在加密卡进程。
如果已有 `KmPermitServer` 进程或端口已被占用，重复启动可能会失败。先确认旧进程状态，再决定停止旧进程、释放端口或修改端口。

## 服务无法启动先看什么

先看运行环境，不要只查业务配置。

- CLOUD：检查 Java 环境和版本
- Linux DDB：直接执行 `DDBExec`，看是否缺少运行库
- KMVue Linux：直接启动 `kmconvertservice`，看是否缺少运行时
- Linux 加密卡：执行 `KmPermitServer_Linux_Server.sh` 或 `KmPermitServer_Linux`

如果直接执行程序就报缺少 `.so`、`GLIBCXX`、`libstdc++`、Java 版本错误，应先修复运行环境。

## KMVue Linux 报加密卡连接不上一定是加密卡问题吗

不一定。
KMVue Linux 环境报加密卡连接不上时，也可能是 `kmconvertservice` 服务缺少运行时或无法启动。先确认 `kmconvertservice` 能独立启动，再继续排查加密卡服务端、端口、防火墙和配置。
