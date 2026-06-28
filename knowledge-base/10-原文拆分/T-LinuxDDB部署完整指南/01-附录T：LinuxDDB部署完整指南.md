---
type: reference
component: DDB
scenario: 01-附录T：LinuxDDB部署完整指南
priority: P2
tags:
- DDB
- 01-附录T：LinuxDDB部署完整指南
- reference
status: active
---

# 01-附录T：LinuxDDB部署完整指南

## 附录 T：Linux DDB 部署完整指南

### T.1 环境要求

- Linux操作系统（支持QtK版本�?- ldd版本 >= 2.31
- gcc版本 >= 9.3.0

### T.2 部署步骤

#### 步骤 1：准备组�?1. 签发Linux版DDB组件：DDBExec、KMDDBDWG_Linux、libDDBDriver
2. 将组件放入同一目录（如/home/DDBExec�?
#### 步骤 2：准备平台依�?1. 从平台套件中拷贝CONTENT(LINUX)内容�?usr/lib/�?usr/lib64/
2. 根据Linux版本选择QtK或ARM版本

#### 步骤 3：配置文�?1. 将AutoCAD_2D.XML拷贝到Linux系统
2. 将DDBExec.ini拷贝到Linux系统
3. 在DDBExec.ini中新增配置段（注意路径格式为Linux格式�?
#### 步骤 4：运行测�?```bash
cd /home/DDBExec
./DDBExec autocad /home/DDBExec.ini
```

#### 步骤 5：验证结�?- 检查是否生�?4个表缓存文件
- 检查表缓存文件内容是否正确

### T.3 注意事项

1. **DWG文件版本**：仅支持AutoCAD 2007及以上版本（AC1021+�?2. **文件编码**�?   - DDBExec.ini必须是ANSI编码
   - XML配置文件必须是GB2312编码
3. **路径大小�?*：Linux路径大小写敏感，必须与实际完全一�?4. **环境变量**：在/etc/profile中添加PATH和LD_LIBRARY_PATH

### T.4 常见问题

#### 问题 1：GLIBCXX_3.4.21 not found
- **解决**：替换lib目录下的libstdc++.so.6

#### 问题 2：字体显�??
- **解决**：拷贝Windows字体�?usr/share/fonts/，添加ACAD环境变量

#### 问题 3：DPL脚本差异
- **解决**：Linux下空值判断用IsEmpty()，不能用==""

---
