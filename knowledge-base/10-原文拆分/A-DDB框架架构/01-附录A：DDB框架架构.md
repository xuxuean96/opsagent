---
type: reference
component: DDB
scenario: 01-附录A：DDB框架架构
priority: P2
tags:
- DDB
- 01-附录A：DDB框架架构
- reference
status: active
---

# 01-附录A：DDB框架架构

## 附录 A：DDB 框架架构

```
应用�?    DDBExec.exe / DDBExec_64.exe (测试�?
             �?km_DdbShell()
入口�?    DdbShell.dll / DdbShell_64.dll
             �?DdbShell()
调度�?    DDBDispatch.DLL (OLE Automation, CDDBPack)
             �?AddCon/OpenSrc/ReadToXml/Process/UpdateModel
核心�?    DDBCore.dll (CDDBFrame, ConMgr)
             �?LoadObject()
驱动�?    DDBDriver.dll (统一驱动)
             �?读写�?    CAD 专用驱动 DLL (UgSeRW, SWTranslator, CATIATranslator, ...)
处理�?    DDBDplPsr.DLL (DPL 脚本引擎)
日志�?    kmDdbLog.dll / kmDdbLog_64.dll
```
