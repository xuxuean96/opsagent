---
type: reference
component: DDB
scenario: 01-附录O：update.xml入口参数编写指南
priority: P2
tags:
- DDB
- 01-附录O：update.xml入口参数编写指南
- reference
status: active
---

# 01-附录O：update.xml入口参数编写指南

## 附录 O：update.xml / 入口参数编写指南

### O.1 update.xml 基本格式

```xml
<?xml version="1.0" encoding="gb2312"?>
<bomData type="数据源类�?>
    <part 文件�?"文件路径">
        <标题栏属�?属性名1="�?" 属性名2="�?"/>
        <DDB配置文件 DDB配置文件="配置文件路径"/>
    </part>
</bomData>
```

### O.2 各CAD软件 update.xml 示例

#### DWG 文字签字
```xml
<?xml version="1.0" encoding="gb2312"?>
<bomData type="AUTOCAD_2D">
    <part 文件�?"D:\test\drawing.dwg">
        <标题栏属�?设计="张三" 校核="李四"/>
        <DDB配置文件 DDB配置文件="D:\test\AutoCAD_2D.xml"/>
    </part>
</bomData>
```

#### DWG 图片签字
```xml
<?xml version="1.0" encoding="gb2312"?>
<bomData type="AUTOCAD_2D">
    <part 文件�?"D:\test\drawing.dwg">
        <标题栏属�?设计="D:\sign\zhangsan.jpg"/>
        <DDB配置文件 DDB配置文件="D:\test\AutoCAD_2D.xml"/>
    </part>
</bomData>
```

#### Word 文字签字
```xml
<?xml version="1.0" encoding="gb2312"?>
<bomData type="WORD">
    <part 文件�?"D:\test\doc.docx">
        <标题栏属�?设计="张三" 日期="2024-01-01"/>
        <DDB配置文件 DDB配置文件="D:\test\Word.xml"/>
    </part>
</bomData>
```

#### Inventor 工程图签�?```xml
<?xml version="1.0" encoding="gb2312"?>
<bomData type="INVENTOR_2D">
    <part 文件�?"D:\test\drawing.idw">
        <标题栏属�?设计1="张三" 校审1="李四"/>
        <DDB配置文件 DDB配置文件="D:\test\Inventor.xml"/>
    </part>
</bomData>
```

### O.3 入口参数 XML 格式

#### 单文件模�?```xml
<ddbdata>
    <parameters name="" type="打开零部�?>
        <parameter name="C:\1.prt"/>
    </parameters>
</ddbdata>
```

#### 多文件模�?```xml
<ddbdata>
    <parameters name="" type="打开零部�?>
        <parameter name="C:\1.prt"/>
        <parameter name="D:\2.asm"/>
    </parameters>
</ddbdata>
```

### O.4 常见格式错误

| 错误 | 原因 | 解决 |
|------|------|------|
| 输入参数格式不正�?| XML头信息缺失或编码错误 | 添加`<?xml version="1.0" encoding="gb2312"?>`，保存为UTF-8 |
| 属性名以数字开�?| XML不支持数字开头属性名 | 添加前缀，如"A123" |
| 特殊字符未转�?| &�?�?等未转义 | &�?amp; <�?lt; >�?gt; "�?quot; |
| 编码错误 | 保存为ANSI而非UTF-8 | 用记事本打开，另存为UTF-8 |

---
