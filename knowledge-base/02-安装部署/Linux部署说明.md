---
type: reference
component: DDB
scenario: Linux部署说明
priority: P2
tags:
- DDB
- Linux部署说明
- reference
status: active
---

# Linux 部署说明

## 适用场景

- Linux 版 DDB 测试
- Linux 加密卡服务端
- Linux 上的轻量化或文件服务

## 关键点

- 路径大小写敏感
- 依赖库要放对目录
- `LD_LIBRARY_PATH` 要正确
- DPL 脚本要考虑空值处理
- 服务无法启动时，先直接执行对应程序确认是否缺少运行时

## DDB Linux 典型步骤

1. 放置 DDB、Driver、平台套件
2. 复制 `.so` 依赖
3. 放置 XML 配置与 `DDBExec.ini`
4. 执行命令行测试
5. 检查缓存表和日志

## Linux 服务启动失败检查

### DDBExec

进入 DDBExec 所在目录，先直接执行：

```bash
./DDBExec
```

如果报缺少 `.so`、`GLIBCXX`、`libstdc++`，先处理运行库和 `LD_LIBRARY_PATH`，再执行正式命令。

### KMVue / kmconvertservice

KMVue Linux 环境无法启动，或报加密卡连接不上时，要直接启动 `kmconvertservice` 检查运行时。

如果 `kmconvertservice` 缺少运行库或环境变量，即使加密卡本身正常，也可能在 KMVue 侧表现为连接失败。

### 加密卡 Linux 服务端

先执行：

```bash
./KmPermitServer_Linux_Server.sh
```

或直接执行服务端程序，观察是否缺少运行库。运行环境正常后，再查授权文件、端口和防火墙。
