---
type: reference
component: DDB
scenario: 01-附录E：各CAD软件完整部署清单（实施用
priority: P2
tags:
- DDB
- 01-附录E：各CAD软件完整部署清单（实施用
- reference
status: active
---

# 01-附录E：各CAD软件完整部署清单（实施用

## 附录 E：各 CAD 软件完整部署清单（实施用�?
### E.1 DWG 部署清单

### D.1 DWG 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装公共组件安装盘（3.0+�?| 目录存在 `C:\KMSOFT\COMMON\DDB\` |
| 2 | 注册 `KmDDBDWG.dll` | `regsvr32 KmDDBDWG.dll` 成功 |
| 3 | 字体 `isocp.shx` �?`kmcadplat\fonts` | 文件存在 |
| 4 | 环境变量 `ACAD` 指向字体目录 | `echo %ACAD%` 显示正确路径 |
| 5 | 配置 `AutoCAD_2D.XML`（坐标或块模式） | �?DDBExec GUI 测试 |
| 6 | 验证：GUI 测试桩选择 AUTOCAD_2D，生�?XML | 输出 `D:\test.xml` 有内�?|

**常见问题**�?- 族信息不�?�?字体缺失，检�?`ACAD` 环境变量
- 明细栏提取失�?�?行高不一致或线条断开
- 路径问题 �?必须用单斜杠，不能双斜杠
- �?PDF 字体异常 �?添加 `TOPDF_CADTYPE="ZWCADJXB"` + 安装中望2D机械�?
### D.2 UG/NX 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 UG NX（建�?8.5/11/12�?| UG 能正常打开模型 |
| 2 | 安装公共组件 | `C:\KMSOFT\COMMON\DDB\` 存在 |
| 3 | 注册 `TransferAttribute_64.dll`�?4位时�?| `regsvr32` 成功 |
| 4 | PATH �?`LIBUFUN.DLL` 路径 | �?Dependencies.exe 检�?`UgSeRW_64.dll` 依赖 |
| 5 | UG8.0 �?`UGII_UTF8_MODE=1` | 环境变量存在 |
| 6 | 配置 XML（接�?`UgSeTranslator.UgSeRW`�?| GUI 测试通过 |
| 7 | 轻量化：安装 3DAST，`readmodel.ini` �?`[OutPutSCSFile]=1` `[KMCloud]=1` | 生成 `.scs` 文件 |

**常见问题**�?- `加载失败。没有找到UG SOLIDEDGE读写接口动态库` �?PATH �?LIBUFUN.DLL 路径
- UG11/12 �?`UGII_ROOT_DIR` �?手动�?`NXBIN` 路径�?PATH
- 文件打不开（UG 错误 640150）→ 检查加密软件是否拦�?- 签字乱码 �?删除 `UGII_UTF8_MODE` 再试

### D.3 SolidWorks 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 SolidWorks�?004+�?| SW 能正常打开 |
| 2 | 安装公共组件 | 目录存在 |
| 3 | 注册 `SWTranslator.dll` | `regsvr32` 成功 |
| 4 | 复制 `KMPDM_SwAddin.dll` �?`addins` 目录并注�?| 文件存在 |
| 5 | 打开 SW，勾�?工具→插件→KMPDM_SwAddin | 插件加载 |
| 6 | 系统属�?文档属性设�?`yes` | �?SW 中确�?|
| 7 | 配置 XML（接�?`SWTranslator.SWBomRW`�?| GUI 测试通过 |
| 8 | 工程图签字：定义文本�?`$PRPSHEET:{设计}` | 签字测试 |

**常见问题**�?- 名称/代号为空 �?系统属�?"no"，改�?"yes"
- 管理员权限问�?�?最新版 `SWTranslator.dll` 已修复，但测试桩仍需管理�?
### D.4 ProE/Creo 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 Creo�?.0+，推�?7.0�?| Creo 能正常打开 |
| 2 | `DDBProeTranslator.dll` �?`DDB\Creo3` 目录 | 文件存在 |
| 3 | 设置 `PRO_COMM_MSG_EXE` 环境变量 | 指向 `pro_comm_msg.exe` |
| 4 | PATH �?`parametric.exe` 所在目�?| 命令行能运行 `parametric.exe` |
| 5 | 设置 `KMSoftPath` | �?`COMMON\DDB` |
| 6 | 正版 Creo：用 `protk_unlock.bat` 解锁 DLL | 解锁成功 |
| 7 | 机器名改为英文（不能中文�?| `hostname` 显示英文 |
| 8 | Creo 7.0：删�?`Wow6432Node\PTC` 空节�?| 注册表清�?|
| 9 | 配置 XML（接�?`DDBProeTranslator.ProeRW`�?| GUI 测试通过 |
| 10 | v4.0+ �?`DDBProeTranslator_64.dll` | 64 位测试桩 |

**常见问题**�?- `连接Creo环境失败,错误码：-1` �?检查环境变量、机器名中文、Wow6432Node 空节�?- `License request failed` �?MAC 地址变更，更�?`ptc_licfile.dat`
- `找不到指定的模块。加载KmProeData.dll` �?XML 配置了二次开发脚本但 DLL 不存�?- 正版解锁失败 �?检�?`protk_unlock.bat` �?`PTC_D_LICENSE_FILE` 路径

### D.5 CATIA 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 CATIA（V5 R14+�?| CATIA 能正常打开 |
| 2 | 安装公共组件 | 目录存在 |
| 3 | PATH �?CATIA 安装路径 | 能运�?CATIA |
| 4 | 注册 `CATIATranslator.dll` / `_64.dll` | `regsvr32` 成功 |
| 5 | 配置 XML（接�?`CATIATranslator.CATIARW`�?| GUI 测试通过 |
| 6 | 二维工程图：确保只有一页（或设置多页输出） | �?PDF 测试 |
| 7 | 轻量化：�?`KM3DSUPERBROWSER` 环境变量 + 安装 3DAST | 生成 `.scs` |
| 8 | 轻量�?PDF 冲突：组件拷�?CATIA 安装路径或复�?3DAST iop �?KMAPS | 两种方法选其一 |

**常见问题**�?- `未找到注册类 -2147221164` �?二维工程图有多页，删除多余页或设置多页输�?- �?PDF �?3DAST 冲突 �?方法1：组件拷�?CATIA 目录；方�?：复�?iop �?KMAPS

### D.6 Inventor 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 Inventor（R9+，推�?2023�?| Inventor 能正常打开 |
| 2 | 安装公共组件 | 目录存在 |
| 3 | 复制插件�?`addins` 目录并注�?| 文件存在 |
| 4 | 配置 XML（接�?`InvTranslator.InvRW`�?| GUI 测试通过 |
| 5 | 二维工程图：只需标题栏坐标和标识格坐�?| 不需要明细栏 |
| 6 | 标识格不能选带 `<>` 的文本框 | 坐标测量时注�?|

**常见问题**�?- `服务器正在运行中` �?无界面模式执行了 `DDB_PreH.dpl`，改名或删除；平�?v053.28+ 已修�?- i3 CPU 可能报错 �?建议 i5+ 配置

### D.7 CAXA 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 CAXA 电子图板 2013�?2位） | CAXA 能正常打开 |
| 2 | 安装公共组件 | 目录存在 |
| 3 | 加载插件 `CAXAAddin2013.crx` | 插件管理器中显示 |
| 4 | 配置 XML（接�?`CAXATranslator.CAXAInfo`�?| GUI 测试通过 |
| 5 | 签字时确保命令行窗口开�?| 右键菜单勾�?命令�? |
| 6 | 图纸必须绘制在模型空间（不能在布局中） | 检查图�?|

**常见问题**�?- 生成 XML 乱码 �?文件不存�?坐标错误/画在布局�?CDRAFT_M.exe 残留/加密软件
- 插件加载后模块管理器不显�?�?检查是�?64 �?CAXA（仅支持 32 位）
- 签字签不�?�?命令行窗口未开�?
### D.8 Excel/Word 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 Office�?010+，不能只�?WPS�?| Excel/Word 能正常打开 |
| 2 | 安装公共组件 | 目录存在 |
| 3 | 注册 `ExcelTranslator.dll` / `WordTranslator.dll` | `regsvr32` 成功 |
| 4 | DCOM 配置中确认有 `Microsoft Word/Excel 97-2003` 节点 | 组件服务中查�?|
| 5 | Excel �?PDF：安�?Adobe + `SaveAsPDFandXPS.exe` | 打印功能正常 |
| 6 | 配置 XML（接�?`ExcelTranslator.DDBExcel` / `WordTranslator.DDBWord`�?| GUI 测试通过 |

**常见问题**�?- `无效指针` / Excel 崩溃 �?未安�?Office 或注册表�?`EXCEL.Application` CLSID
- `Microsoft Office 无法验证此产品的许可证` �?Office 许可证过期，重装或升�?- `参数错误 / 未安装打印机` �?需 Office + Adobe + `SaveAsPDFandXPS.exe`
- 文件名含特殊字符（如 `Ⅺ`）→ 改名后再�?
### D.9 中望3D 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装中望3D�?023/2025/2026�?| 中望能正常打开 |
| 2 | 2023：破解版必须 | 确认破解 |
| 3 | 安装公共组件 4.0+ | 目录存在 |
| 4 | 2023：`ZW3DDriver_64.dll` �?`COMMON\DDB` | 文件存在 |
| 5 | 2025：`ZWTranslator.dll` / `_64.dll` �?`COMMON\DDB` 并注�?| `regsvr32` 成功 |
| 6 | PATH 加中望安装路�?| 命令行能找到 |
| 7 | 安装 3DAST�?6.1/17.6/18.2�?| 版本匹配 |
| 8 | `readmodel.ini` �?`[OutPutSCSFile]=1` `[KMCloud]=1` | 配置正确 |
| 9 | 配置 XML（接�?`ZW3DDriver.ZWRW` �?`ZWTranslator.ZWRW`�?| GUI 测试通过 |
| 10 | 2026 STP：`ConvertZW3DtoStp.dll` 放中�?`apilibs` | 文件存在 |

**常见问题**�?- 2023 必须破解�?�?否则导入报错
- 插件菜单不显�?�?检�?`apilibs` 目录�?`User.zcui` 配置
- �?PDF 符号丢失 �?安装中望2D机械版或配置 `TOPDF_CADTYPE`

### D.10 SolidEdge 部署清单

| 步骤 | 操作 | 验证 |
|------|------|------|
| 1 | 安装 SolidEdge（V14+ �?2021+�?| SE 能正常打开 |
| 2 | 安装公共组件 | 目录存在 |
| 3 | 组件�?UG 完全一致（`UgSeRW.dll`�?| 文件存在 |
| 4 | 2025+ �?64 位组�?| 确认位数 |
| 5 | �?PDF：`SEToPDF_64.dll` + DDBExec 10.0.0.79+ | 版本匹配 |
| 6 | 配置 XML（接�?`UgSeTranslator.UgSeRW`�?| GUI 测试通过 |

---
