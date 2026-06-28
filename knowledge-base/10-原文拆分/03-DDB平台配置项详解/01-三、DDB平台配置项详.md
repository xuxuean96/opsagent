---
type: reference
component: DDB
scenario: 01-三、DDB平台配置项详
priority: P2
tags:
- DDB
- 01-三、DDB平台配置项详
- reference
status: active
---

# 01-三、DDB平台配置项详

## 三、DDB 平台配置项详�?
### 3.1 XML 配置文件结构

```xml
<?xml version="1.0" encoding="GB2312"?>
<数据设计�?配置版本="1">
  <系统配置 名称="扩展部件">
    <!-- 接口配置 -->
  </系统配置>
  <读写配置 ...>
    <!-- CAD 读取规则 -->
  </读写配置>
  <处理配置 名称="属性对�?>
    <!-- 属性映�?-->
  </处理配置>
  <处理配置 名称="组装结构�?>
    <!-- BOM 结构 -->
  </处理配置>
  <处理配置 名称="属性合�? 保留属�?"数量;材料;备注;名称" 合并到零�?"�? 覆盖="�?/>
</数据设计�?
```

### 3.2 关键配置�?
#### 接口配置（`<接口>`�?
| 接口�?| 用�?| 依赖组件 |
|--------|------|---------|
| `EBOMTranslator.EBOMRW` | 轻量化导�?| EBOMTranslator.dll |
| `EBOMDriver.EBOMRW` | 表缓存轻量化导入 | EBOMKMCloud_64.dll + EBOMDriver |
| `DDBProeTranslator.ProeRW` | ProE/Creo 模型 | DDBProeTranslator.dll/_64.dll |
| `UgSeRW.UgSeBomRW` | UG/SE 模型 | UgSeRW.dll / UgSeRW_64.dll |
| `SWTranslator.SWBomRW` | SolidWorks 模型 | SWTranslator.dll |
| `CATIATranslator.CATIABomRW` | CATIA 模型 | CATIATranslator.dll/_64.dll |
| `ExcelTranslator.ExcelBomRW` | Excel | ExcelTranslator.dll |
| `WordTranslator.WordBomRW` | Word | WordTranslator.dll |
| `KmDDBDWG.DwgBom` | DWG 图纸 | KmDDBDWG.dll |
| `ZW3DDriver.ZWRW` | 中望3D 2023 | ZW3DDriver_64.dll |
| `ZWTranslator.ZWRW` | 中望3D 2025 | ZWTranslator.dll/_64.dll |

#### 标识格配置（DWG/Inventor/CAXA�?
| 配置�?| 说明 |
|--------|------|
| 标识格左下X/Y | 标识格左下角坐标 |
| 标识格右上X/Y | 标识格右上角坐标 |
| `合并线精�?"0.0001"` | 内外框距离接�?时添加此�?|
| `TOPDF_CADTYPE="ZWCADJXB"` | 使用中望机械版转 PDF |

> **标识格规�?*：不能跨格；不能选「阶段」或「版本」（因它们在图纸上是一个整体文本「阶段版本」）；坐标精度直接影�?PDF 图幅�?
#### 比例说明

| 比例 | 含义 | XML 坐标计算 |
|------|------|-------------|
| `1 : 2` | 图形放大一�?| 实际坐标 ÷ 2 |
| `2 : 1` | 图形缩小一�?| 实际坐标 × 2 |

> 比例�?DDB 框架自动计算：`XML坐标�?: DWG实际坐标值`�?
#### 属性合并配�?
```xml
<处理配置 名称="属性合�? 保留属�?"数量;材料;备注;名称" 合并到零�?"�? 覆盖="�?/>
```
- `合并到零�?"�?`：修�?childPart 节点属�?- `合并到零�?"�?`：修�?Part 节点属�?
#### 对象标识配置

| 配置�?| 影响 |
|--------|------|
| 代号 | 用代号区分对象唯一�?|
| 图号 | 用图号区分（代号相同会合并） |

> **注意**：如果配置「代号」但数据源中无代号列，所有对象会合并成一个�?
#### 缓存表赋值配�?
```xml
<!-- �?生成装配结构"的明细栏子对象属性对应中 -->
代号=图号   <!-- 左边=Buf_Part字段, 右边=Buf_ItemAttr字段 -->
```

### 3.3 3DAST readmodel.ini 关键配置

| 配置�?| �?| 作用 |
|--------|-----|------|
| `[OutPutSCSFile]` | 1 | 输出 SCS 文件 |
| `[KMCloud]` | 1 | 输出缓存数据 |
| `[AsmFeature]` | 1 | 装配特征输出 |
| `[OutPutFeatureFile]` | 1 | 输出 hsf 特征文件 |
| `[OutPutSabFile]` | 1 | 输出 sab 文件 |
| `[ReadRiSetData]` | 0 | 不读注释节点（避免多�?part�?|
| (去重�? | 1 | 去掉3DAST生成的多余一层节�?|

### 3.4 dpMsgServerConfig.ini

```ini
[集成平台设置]
支持本机多用户通信=0    ; Catia+3DMPS 需设为0，否则打不开模型
```

### 3.5 WebConfig.ini（KMVue 用）

```ini
[PartConvert]
ConverterMode=1    ; 1=开启轻量化转换
```

---
