---
type: reference
component: DDB
scenario: 01-二、DDB测试桩全流程使用
priority: P2
tags:
- DDB
- 01-二、DDB测试桩全流程使用
- reference
status: active
---

# 01-二、DDB测试桩全流程使用

## 二、DDB 测试桩全流程使用

### 2.1 测试桩简�?
DDB 测试桩（`DDBExec.exe` / `DDBExec_64.exe`）是 DDB 框架�?GUI 调试工具和命令行执行器，位于公共组件目录 `C:\KMSOFT\COMMON\DDB\`（或 `C:\Program Files\Common Files\KMSOFT\DDB\`）�?
### 2.2 有界面模式（GUI�?
**启动方式**：创建桌面快捷方式，目标末尾�?`\t` 参数�?```
"C:\KMSOFT\COMMON\DDB\DDBExec.exe" \t
```

**操作流程**�?1. 启动后弹出测试界�?2. 选择「数据源类型」（PROE / CATIA / AUTOCAD_2D / EXCEL 等）
3. 选择「操作模式」（OutXml / Update / Topdf 等）
4. 设置 DDB 配置文件路径（XML�?5. 设置数据源参�?XML 或文件路�?6. 点击「生�?XML�?7. 查看输出：`D:\test.xml`（默认输出路径）
8. 失败时查看日志：`KmDdbLog.Txt`（在 DDB 目录下）

**保存/加载测试方案**：方案保存在 `DDBTester.ini` �?`[SCHEME_xxx]` 段�?
### 2.3 无界面模式（CLI / 生产环境�?
**命令行格�?*�?```
DDBExec.exe <SectionName> <IniFilePath> [PreDplFile] [Mode]
```

**参数说明**�?| 参数 | 说明 |
|------|------|
| `SectionName` | DDBExec.ini 中的段名（如 `autocad`、`catia`�?|
| `IniFilePath` | DDBExec.ini 全路�?|
| `PreDplFile` | 前处�?DPL 脚本（可选） |
| `Mode` | `0`=用户正常模式，`1`=32位自动，`2`=64位自�?|

**DDBExec.ini 格式**�?```ini
[autocad]
Mode=OutXml
DataType=AUTOCAD_2D
ConfigFile=D:\test\AutoCAD_2D.XML
sDataSrcFile=D:\test\input.xml
OutputFile=D:\test\output.xml

[catia]
Mode=OutXml
DataType=CATIA
ConfigFile=D:\test\DDB(CATIA).XML
sDataSrcFile=D:\test\input.xml
OutputFile=D:\test\output.xml
```

**数据源参�?XML 格式**（`sDataSrcFile`）：
```xml
<ddbdata>
  <parameters type="打开">
    <parameter name="D:\path\to\model.prt"/>
  </parameters>
</ddbdata>
```

### 2.4 RegisterType（注册模式）详解

| �?| 含义 | 说明 |
|----|------|------|
| `0` | 注册模式 | 需�?COM 注册，传统方�?|
| `1` | 表缓存模式（无UI�?| 不需要注册，静默执行 |
| `2` | 表缓存模式（有调试UI�?| 弹出调试窗口 |

> KMCloud/eCol 导入时通常�?`RegisterType=1`（表缓存方式）�?
### 2.5 操作模式（Mode）一�?
| Mode | 功能 | 适用类型 |
|------|------|---------|
| `OutXml` | 提取信息生成 XML | 所�?|
| `Update` | 更新文件（签�?属性） | 所�?|
| `Cable` | 读取电缆信息 | ProE |
| `Annot` | 读取注释信息 | CATIA |
| `Topdf` | 转换�?PDF | DWG/CATIA/UG/Inventor/中望 |
| `SingleOutXml` | 单维度输�?| 所�?|
| `Message` | 异步消息 | Cadence |
| `Tostep` | �?STEP | NX |
| `EPlanTemplateCreate` | 创建模板 | EPlan |
| `OpenProject` | 打开项目 | CATIA |

### 2.6 日志文件

| 文件 | 位置 | 内容 |
|------|------|------|
| `KmDdbLog.Txt` | DDBExec.exe 同目�?| 主日�?|
| `KmDdbLog_<用户�?_Pid<PID>.Txt` | 同上 | 按用�?进程隔离 |
| `DDBError.txt` | XML 配置文件同目�?| 错误详情 |
| `DDBError.log` | 同上 | 无界面模式日�?|

**日志模式**（位掩码）：
| �?| 含义 |
|----|------|
| 1 | 提示显示 |
| 2 | 错误显示 |
| 4 | 重要信息 |
| 8 | 中间�?|
| 64 | 写入日志文件 |
| 128 | 每次写入后刷�?|

### 2.7 表缓存导入（14张缓存表�?
| 表名 | 内容 |
|------|------|
| `Buf_Part` | 零件信息 |
| `Buf_DocAttr` | 文档属�?|
| `Buf_ModelAttr` | 模型属�?|
| `Buf_StructAttr` | 结构属�?|
| `Buf_TitleAttr` | 标题栏属�?|
| `Buf_ItemAttr` | 明细栏属�?|
| `Buf_ParaTable` | 参数�?|
| `Buf_ParaTableRowData` | 参数表行数据 |
| `Buf_RootInfo` | 根信�?|
| `Buf_Root` | 根节�?|
| `Buf_StructRelation` | 结构关系 |
| `Buf_SysDocAttr` | 系统文档属�?|
| `Buf_ErroInfo` | 错误信息 |
| (缩略图表) | 文件�?ISPART=2/TYPE=缩略�?REFID |

> 查看缓存表：�?`DDBExec.dpl` 中调�?`kmdp_Browser()` 打开缓存表浏览器�?
### 2.8 缩略图生�?
- 缩略图通过 `NXPrt.exe` + `ConvertConfig.ini`（在 `common\ddb` 目录）生�?- 命令行：`NXPrt.exe <模型文件全路�? bmp`
- 必须安装对应 CAD 软件（版�?�?模型文件版本�?- 仅支持轻量化/表缓存轻量化导入模式

### 2.9 Linux DDB 测试

**部署步骤**�?1. 签发�?Linux �?DDB + DDBDriver + KMDDBDWG_Linux 放入同一目录（如 `/home/DDBExec`�?2. 平台套件 CONTENT(Linux) �?`.so` 拷到 `/usr/lib/`
3. DWG 图纸、XML 配置、DDBExec.ini 放到 Linux 任意位置
4. 执行：`cd /home/DDBExec && ./DDBExec autocad /home/DDBExec.ini`
5. 生成�?14 个缓存表文件�?`/home/kmloud/` 目录

**Linux 注意事项**�?- 仅支�?AutoCAD 2007+（AC1021+�?- DDBExec.ini �?XML 配置路径**大小写敏�?*
- `ldd --version` �?2.31，`gcc --version` �?9.3.0
- 需设置 `export LD_LIBRARY_PATH=/usr/lib64:$LD_LIBRARY_PATH`
- DPL 脚本中空值判断用 `IsEmpty()` 替代 `==""`

---
