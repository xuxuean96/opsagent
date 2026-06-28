---
type: reference
component: DDB
scenario: 01-五、KMVue集成环境部署
priority: P2
tags:
- DDB
- 01-五、KMVue集成环境部署
- reference
status: active
---

# 01-五、KMVue集成环境部署

## 五、KMVue 集成环境部署

### 5.1 Windows 环境

| 步骤 | 内容 |
|------|------|
| 1. 前端部署 | 解压 KMVue 包，�?Nginx + OdaServer |
| 2. Nginx 配置 | `nginx.conf` 设置 IP/端口/dist 路径 |
| 3. globalConfig.js | 配置前端接口地址 |
| 4. web.xml | Tomcat 配置（浏览单零件/二维图纸时需要） |
| 5. CLOUD 配置 | 系统配置→KMVue 集成配置（前端IP/后端IP/控件类型=2�?|
| 6. Oda 服务 | 启动 Oda 服务（浏�?DWG/DWF 需要） |
| 7. 转轻量化 | 公共组件 + ConvertService + 文件批处理服�?|

### 5.2 Linux 环境

| 步骤 | 内容 |
|------|------|
| 1. 前端部署 | Nginx + dist �?`/usr/local/nginx/html` |
| 2. Nginx 配置 | �?Windows，路径用 `/` |
| 3. globalConfig.js | �?Windows |
| 4. web.xml | �?Windows |
| 5. CLOUD 配置 | �?Windows |
| 6. Oda 服务 | **Linux 暂不支持** |
| 7. C 平台 | `.so` �?`/usr/lib` �?`/usr/lib64` |
| 8. Linux DDB | DDB 组件 + KMVue 目录 |
| 9. ConvertService | `WebConfig.ini` �?`ConverterMode=1` |
| 10. 转换脚本 | `start_convertservice2.sh` 最后一行改�?`./KMWebConvertProcess $1` |
| 11. 权限 | `chmod 755 -R KMVue/quick_start/*` |
| 12. 文件批处�?| �?Windows（common-file-ext-service.jar�?|

### 5.3 KMVue 关键路径

| 路径 | 内容 |
|------|------|
| `D:\KMSOFT\KMVue\` | KMVue 主目�?|
| `D:\KMSOFT\KMVue\WebConfig.ini` | 转换配置 |
| `D:\KMSOFT\COMMON\EBOMKMCloud_64.dll` | 表缓存组�?|
| `D:\KMSOFT\COMMON\DDB\EBOMTranslator.dll` | DDB 接口组件 |
| `D:\KMSOFT\COMMON\DDB\DDBExec.dpl` | DPL 脚本（可�?`kmdp_Browser()`�?|
| `D:\KMSOFT\KMAPS\readmodel.ini` | 3DAST 配置 |

---
