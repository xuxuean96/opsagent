---
type: reference
component: DDB
scenario: 01-附录U：KMVue集成部署完整指南
priority: P2
tags:
- DDB
- 01-附录U：KMVue集成部署完整指南
- reference
status: active
---

# 01-附录U：KMVue集成部署完整指南

## 附录 U：KMVue 集成部署完整指南

### U.1 Windows 环境部署

#### 前端部署
1. 解压KMVUE压缩�?2. 将Nginx和OdaServer放置到本地目�?3. 修改nginx.conf�?   - 配置IP和端�?   - root路径指向dist目录（使用\\�?4. 修改globalConfig.js�?   - 配置接口访问地址和端�?5. 启动nginx.exe（任务管理器显示两个nginx进程�?6. 验证：访问http://IP:PORT/#/sign-in

#### 转轻量化服务部署
1. 安装公共组件（管理员权限�?2. 将ConvertService复制到D:\KMSOFT（与COMMON同级�?3. 改名为convert
4. 配置WebConfig.ini：ConverterMode=1
5. 如果KMVUE与CLOUD分开部署�?   - 在KMVUE机器上放置一套CLOUD run�?   - 单独启动common-file-ext-service.jar

#### ODA服务部署（浏览DWG/DWF�?1. 启动OdaServer.exe
2. 验证DWG浏览功能

### U.2 Linux 环境部署

#### 前端部署
1. 解压KMVUE压缩�?2. 安装Nginx（参考KMVue部署说明�?3. 修改nginx.conf（路径用/�?4. 将dist放到/nginx/html�?5. 启动nginx�?usr/local/nginx/sbin/nginx
6. 验证：访问http://IP:PORT/#/sign-in

#### 转轻量化服务部署
1. 部署C平台�?usr/lib�?usr/lib64
2. 创建LINUX_DDB文件夹，包含DDB和kmvue目录
3. 配置WebConfig.ini：ConverterMode=1
4. 修改start_convertservice2.sh（修正最后一行）
5. 赋予执行权限：chmod 755 -R KMVue/quick_start/*
6. 如果KMVUE与CLOUD分开部署�?   - 放置CLOUD run�?   - 单独启动common-file-ext-service.jar

#### 注意
- Linux暂不支持ODA服务（无法浏览DWG/DWF�?- Linux暂不支持转PDF和签�?- 麒麟系统可能需要手动点击允许权�?
### U.3 CLOUD 系统配置
1. 登录CLOUD系统
2. 系统定制→系统配置→配置工具→文档管理→通用配置→KMVUE集成配置
3. 配置�?   - KMVUE服务前端IP（nginx服务IP�?   - CLOUD服务前端IP（tomcat服务IP�?   - 浏览控件类型�?（KMVue�?
### U.4 验证清单

| 功能 | Windows | Linux |
|------|---------|-------|
| 浏览SCS | �?| �?|
| 浏览PDF | �?| �?|
| 浏览xlsx/docx | �?| �?|
| 浏览DWG | ✅（需ODA�?| �?|
| 浏览DWF | ✅（需ODA�?| �?|
| 转轻量化 | �?| �?|
| 转PDF | �?| �?|
| 签字 | �?| �?|

---
