---
type: reference
component: DDB
scenario: 01-附录H：同义词与口语映射表（Agent检索增强）
priority: P2
tags:
- DDB
- 01-附录H：同义词与口语映射表（Agent检索增强）
- reference
status: active
---

# 01-附录H：同义词与口语映射表（Agent检索增强）

## 附录 H：同义词与口语映射表（Agent 检索增强）

> 本表用于解决用户口语化提问与技术术语的匹配问题。Agent 检索时应同时匹配以下同义词�?
### G.1 CAD 软件名称映射

| 用户可能说的 | 知识库中的正式名�?| 数据源类�?|
|-------------|------------------|-----------|
| UG, NX, UG/NX, 西门�?| UG_SOLIDEDGE, UgSeRW | UG_SOLIDEDGE / UG_SOLIDEDGE_2D |
| SolidEdge, SE, 西门子SE | UG_SOLIDEDGE（组件相同） | UG_SOLIDEDGE / UG_SOLIDEDGE_2D |
| ProE, Pro/E, Creo, 野火 | PROE, DDBProeTranslator | PROE / PROE_2D |
| SolidWorks, SW,  solidworks | SOLIDWORKS, SWTranslator | SOLIDWORKS / SOLIDWORKS_2D |
| CATIA, 达索, catia | CATIA, CATIATranslator | CATIA / CATIA_2D |
| Inventor,  inventor, 欧特�?| INVENTOR, InvTranslator | INVENTOR / INVENTOR_2D |
| CAXA,  caxa, 电子图板 | CAXA_2D, CAXATranslator | CAXA_2D |
| AutoCAD, CAD, DWG, autocad | AUTOCAD_2D, KmDDBDWG | AUTOCAD_2D |
| 中望, 中望3D, ZW3D, zw3d | ZW3D, ZW3DDriver, ZWTranslator | ZW3D |
| Excel, 表格, xls, xlsx | EXCELTRANSLATOR, NOMALTRANS | EXCELTRANSLATOR / NOMALTRANS |
| Word, 文档, doc, docx | WORDTRANSLATOR | WORDTRANSLATOR |
| Altium, PCB, 电路�?| ALTIUM_PCB | ALTIUM_PCB |

### G.2 功能/操作映射

| 用户可能说的 | 知识库中的正式名�?| 对应 Mode |
|-------------|------------------|----------|
| 导入, 读取, 提取, 展开 | OutXml, 批量导入 | OutXml |
| 签字, 签名, 签章, 签署 | Update（签字模式） | Update |
| 更新属�? 改属�? 属性互�?| Update（属性更新） | Update |
| 转PDF, 导出PDF, 打印PDF | Topdf | Topdf |
| 转STEP, 导出STEP | Tostep | Tostep |
| 轻量�? 转轻量化, SCS | EBOMTranslator, EBOMDriver | OutXml（轻量化�?|
| 表缓�? 缓存�? 14张表 | EBOMDriver（表缓存方式�?| OutXml（表缓存�?|
| 三维, 3D, 模型 | 模型展开, 三维导入 | OutXml（模型） |
| 二维, 2D, 图纸, 工程�?| 工程图展开, 二维导入 | OutXml（工程图�?|
| 族表, 族信�? 族成�?| 参数表属性（族信息） | OutXml |
| 明细�? 明细�? BOM�? 清单 | 明细栏属�?| OutXml |
| 标题�? 图框, 图签 | 标题栏属�?| OutXml |
| 线缆, 线束, Cable | Cable | Cable |
| 标注, 注释, Annot | Annot | Annot |

### G.3 属�?字段映射

| 用户可能说的 | 知识库中的正式名�?| 所在位�?|
|-------------|------------------|---------|
| 零件�? 物料�? 件号, 编码 | 代号 | 标题�?明细�?模型属�?|
| 零件名称, 物料名称, 描述 | 名称 | 标题�?明细�?模型属�?|
| 数量, 件数, 个数 | 数量 | 明细�?|
| 材料, 材质, 牌号 | 材料 | 标题�?明细�?|
| 重量, 质量, 单重, 总重 | 质量（三维）/单重/总重（二维） | 模型属�?明细�?|
| 图号, 图纸编号 | 代号（或图号，取决于配置�?| 标识�?标题�?|
| 版本, 版次, 修订 | 版本�? 阶段 | 文档属�?|
| 设计�? 设计, 制图 | 设计 | 标题栏签字格 |
| 校对�? 校对, 校核 | 校对 | 标题栏签字格 |
| 审核�? 审核, 审查 | 审核 | 标题栏签字格 |
| 批准, 审定, 批准�?| 批准 | 标题栏签字格 |
| 工艺, 工艺�?| 工艺 | 标题栏签字格 |
| 标准�?| 标准�?| 标题栏签字格 |
| 共页, 总页�?| 共页 | 图纸属性拆�?|
| 第页, 当前�?| 第页 | 图纸属性拆�?|

### G.4 问题/错误映射

| 用户可能说的 | 知识库中的关键词 | 排查方向 |
|-------------|----------------|---------|
| 打不开, 启动失败, 闪退 | 加载失败, 连接失败, 注册失败 | 环境/DLL/注册 |
| 乱码, 中文乱码, 编码错误 | 编码, GB2312, ANSI, UTF-8 | 编码设置 |
| 找不到文�? 路径错误 | 系统找不到指定的路径 | 路径格式/权限 |
| 权限不够, 拒绝访问 | 拒绝访问, 管理员权�?| 权限/管理员运�?|
| 卡死, 无响�? 转圈�?| 服务器正在运行中, 进程卡死 | 弹框遮挡/CPU性能 |
| 没反�? 空白, 空文�?| 生成xml为空, 导入成功但无内容 | 配置错误/数据源问�?|
| 签字没显�? 签不�?| 签字失败, 未知错误 | 坐标/字体/Office |
| 连不�? 连接失败 | 连接失败, 超时 | 网络/防火�?端口 |
| 过期, 到期, 授权失效 | read licence error, 许可�?| 授权文件/硬件变更 |

### G.5 配置项口语映�?
| 用户可能说的 | 知识库中的配置项 | 说明 |
|-------------|----------------|------|
| 怎么�? 怎么设置, 在哪里配 | 配置XML, DDB配置文件 | �?AutoCAD_2D.XML �?|
| 接口配什�?| <接口> | 系统配置中的接口节点 |
| 属性对应怎么�?| <处理配置 名称="属性对�?> | 处理配置 |
| 标识格坐标怎么�?| 标识�? 单格, 坐标 | 读写配置中的坐标 |
| 明细栏怎么�?| <明细�?, <�? | 明细栏坐标和列宽 |
| 对象标识是什�?| <对象标识><对象> | Excel结构数据中的唯一标识 |
| 合并属性怎么�?| <处理配置 名称="属性合�?> | 属性合并配�?|
| DPL脚本怎么�?| <DPL脚本> | 属性处�?删除结点 |
| 转PDF怎么�?| TOPDF_CADTYPE | �?Topdf 模式 |
| 表缓存怎么开 | RegisterType=1 | 注册类型=1 |

---
