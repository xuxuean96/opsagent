---
type: reference
component: DDB
scenario: 01-六、各CAD集成环境配置速查
priority: P2
tags:
- DDB
- 01-六、各CAD集成环境配置速查
- reference
status: active
---

# 01-六、各CAD集成环境配置速查

## 六、各�?CAD 集成环境配置速查

### DWG

- 不依�?AutoCAD
- 组件：`KmDDBDWG.dll`�?2位）
- XML 配置：`AutoCAD_2D.XML`
- 字体：`isocp.shx` �?`kmcadplat\fonts` + 环境变量 `ACAD`
- 坐标方式和块方式**不能同时配置**
- 中望机械版转 PDF：添�?`TOPDF_CADTYPE="ZWCADJXB"` + 安装中望2D机械�?
### UG/NX

- 组件：`UgSeRW.dll`/`UgSeRW_64.dll` + `TransferAttribute_64.dll`（需注册�?- 环境：PATH �?LIBUFUN.DLL 所在路�?- UG8.0：加 `UGII_UTF8_MODE=1`
- 轻量化：安装 3DAST，`readmodel.ini` �?`[OutPutSCSFile]=1` `[KMCloud]=1`

### SolidWorks

- 组件：`SWTranslator.dll`�?2位，支持64�?SW�?- 系统属�?文档属性需设为 `yes`
- 插件：`KMPDM_SwAddin.dll`
- 工程图签字需定义文本�?`$PRPSHEET:{设计}`

### ProE/Creo

- 组件：`DDBProeTranslator.dll`（固定放 `DDB\Creo3` 目录，不�?2/64位）
- 环境：`PRO_COMM_MSG_EXE` + PATH + `KMSoftPath`
- 正版 Creo 需�?`protk_unlock.bat` 解锁 DLL
- **机器名不能为中文**
- Creo 7.0：删 `Wow6432Node\PTC` 空节�?- v4.0+ 公共组件：统一�?`DDBProeTranslator_64.dll`

### CATIA

- 组件：`CATIATranslator.dll`/`CATIATranslator_64.dll`
- �?PDF：二维工程图只允许一页（或设�?Catia 多页输出�?- 轻量化：�?`KM3DSUPERBROWSER` 环境变量 + 安装 3DAST
- 轻量�?PDF 冲突：方�?-组件拷到 CATIA 安装路径；方�?-复制 3DAST iop �?KMAPS

### Inventor

- �?32�?DDB 框架
- 安装公共组件 + Inventor 即可
- 坐标测量：编辑定�?�?模型浏览�?�?量取
- 标识格不能选带 `<>` 的文本框
- i3 CPU 上可能报「服务器正在运行中」（建议 i5+�?
### CAXA

- �?32�?- 必须加载插件 `CAXAAddin2013.crx`
- 签字时命令行窗口必须开�?- 乱码原因：文件不存在/坐标错误/画在布局�?CDRAFT_M.exe 残留/加密软件

### 中望3D

- 2023：`ZW3DDriver_64.dll` + 3DAST 16.1 + 必须破解�?- 2025：`ZWTranslator.dll`/`ZWTranslator_64.dll` + 3DAST 17.6+
- 2026（带 STP）：`ConvertZW3DtoStp.dll` + 3DAST 18.2+ + KMVue 4.5
- PATH 加中望安装路�?- 二维工程图转 PDF：`FileTransferPdf.dll` + `FileTransferToPdf.exe`

### SolidEdge

- 组件�?UG 完全一致（`UgSeRW.dll`�?- 2025+ �?64 位组�?- �?PDF：`SEToPDF_64.dll` + DDBExec 10.0.0.79+

### Excel/Word

- �?32�?- 必须安装 Office（不能只�?WPS�?- Excel COM 接口：DCOM 配置中必须有 `Microsoft Word/Excel 97-2003` 节点
- Excel �?PDF：需 Office + Adobe + `SaveAsPDFandXPS.exe`
- 文件名不能含特殊字符（如罗马字符 Ⅺ）

### Altium_PCB

- �?64�?- 代码�?`dpl_kmfont_64.dll`
- 公共组件 3.4+ 自带

---
