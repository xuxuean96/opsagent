---
type: reference
component: 加密卡
scenario: 98-增补-Linux加密卡运行环境检查
priority: P2
tags:
- 加密卡
- 98-增补-Linux加密卡运行环境检查
- reference
status: active
---

# 增补：Linux 加密卡运行环境检查

## 场景

Linux 加密卡服务端无法启动。

## 排查顺序

1. 执行 `KmPermitServer_Linux_Server.sh`
2. 或直接执行 `KmPermitServer_Linux`
3. 查看是否报缺少运行库
4. 检查 `LD_LIBRARY_PATH`
5. 确认依赖库满足后，再查授权文件、端口和防火墙

## 结论

加密卡 Linux 服务端启动失败时，运行时缺失是前置排查项。不要直接跳到授权或网络问题。

