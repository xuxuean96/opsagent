---
type: reference
component: DDB
scenario: 01-附录M：转PDF完整指南
priority: P2
tags:
- DDB
- 01-附录M：转PDF完整指南
- reference
status: active
---

# 01-附录M：转PDF完整指南

## 附录 M：转 PDF 完整指南

### M.1 DWG �?PDF

#### 方法一：AcadToPDF.exe（推荐）

**命令行格式：**
```
"AcadToPDF.exe全路�? "DWG文件全路�? "PDF输出全路�? 22933 --paper Custom --paper-width 297 --paper-height 210 --plotstyle acad.ctb
```

**参数说明�?*
- `22933`：打印样式代�?- `--paper Custom`：自定义纸张
- `--paper-width 297`：纸张宽度（mm�?- `--paper-height 210`：纸张高度（mm�?- `--plotstyle acad.ctb`：打印样式文�?
**打印样式文件位置�?*
- AutoCAD打印样式管理器打开的目录（非安装目录）
- 例：`C:\Users\Administrator\AppData\Roaming\Autodesk\AutoCAD 2022\R24.1\chs\Plotters\Plot Styles`

**带打印样�?vs 不带打印样式�?*
- 带打印样式：命令行中打印样式可带可不带路�?- 不带打印样式：必须安装AutoCAD，且打印样式文件必须在AutoCAD打印样式管理目录

**字体问题�?*
- 如果转换后字体显示为??
- 将对应字体拷贝到`D:\KMSOFT\COMMON\kmcadplat\fonts`
- 添加环境变量`ACAD`，值为字体路径

#### 方法二：调用中望机械版（特殊符号丢失时）

**适用场景�?*
- 中望CAD图纸转PDF时，某些符号丢失
- 但用中望机械版打开打印正常

**配置�?*
- 在XML配置中添加：`TOPDF_CADTYPE="ZWCADJXB"`
- 需要安装中�?D机械�?021/2022/2023
- 公共组件安装�?.2及以后版本支�?
**命令行调用：**
```
"ZWDWGTOPDF.EXE全路�? "DWG文件全路�? "PDF输出全路�?
```

### M.2 CATIA 2D �?PDF

**配置方法�?*
1. 确保CATIA二维工程图只有一�?2. 配置XML中的标识格坐标（必须精确�?3. 运行Topdf模式

**多页处理�?*
- 默认不支持多页转PDF
- 解决：删除多余页，或在CATIA中设置只转当前页

### M.3 中望 2D �?PDF

**配置方法�?*
1. DDB框架使用a74及以上版�?2. 放置FileTransferPdf.dll到ZW3D安装目录
3. 数据源类型新�?ZW3D_2D"
4. 支持多页PDF：`MultiPDF="yes"`

### M.4 SolidEdge �?PDF

**配置方法�?*
1. 安装SolidEdge2021
2. 安装公共组件3.8及以上版�?3. 使用DDBExec_64�?4. 运行Topdf模式

### M.5 Excel �?PDF

**前提条件�?*
1. 安装Office
2. 安装Adobe
3. 安装SaveAsPDFandXPS.exe（Office2007安装盘中�?
**常见问题�?*
- 未安装打印机：安装任意打印机
- 未安装SaveAsPDFandXPS.exe：从Office安装盘安�?
---
