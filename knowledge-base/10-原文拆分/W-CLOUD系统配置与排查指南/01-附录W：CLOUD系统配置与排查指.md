---
type: reference
component: CLOUD
scenario: 01-附录W：CLOUD系统配置与排查指
priority: P2
tags:
- CLOUD
- 01-附录W：CLOUD系统配置与排查指
- reference
status: active
---

# 01-附录W：CLOUD系统配置与排查指

## 附录 W：CLOUD 系统配置与排查指�?
> 本章节内容来自《一些典型问题的解决方法-2026.6.5汇总》，为最新现场实战经验�?
### W.1 服务启动问题

#### 服务号速查�?
遇到"未发现服务[服务号],请稍后重�?"提示时，根据服务号查找对应服务：

| 服务�?| 服务名称 | 服务jar |
|--------|----------|---------|
| 9300 | 快速搜索服�?| component-quicksearch-server |
| 9800 | 多语言服务 | km-global-service |
| 7300 | 任务计划服务 | km-job-queue |
| 6800 | 业务服务 | plm-service |
| 6801 | 元数据服�?| common-mdm-service |
| 6802 | 组织服务 | common-org-service |
| 7000 | 文件服务 | wpfile |
| 6700 | 静态缓存服�?| common-workflow-service |
| 9600 | 数据导入服务 | plm-data-import-service |
| 8600 | activiti服务 | common-activiti-service |
| 7900 | 对象服务 | plm-agent |

#### 服务启动报错通用排查

**"数据库连接失�?**
1. 查看 run/config 目录�?dpConfig.ini 是否填写错误
2. 使用数据库连接工具登录对应账户，检查密码是否到�?3. 修改密码：`alter user 用户�?identified by 密码;`
4. 设置密码永不过期：`ALTER PROFILE DEFAULT LIMIT PASSWORD_LIFE_TIME UNLIMITED;`

**"访问注册中心失败"**
1. 查看 run/config/wpConfig.yaml 中注册中心地址是否正确
2. 使用 `telnet ip 端口` 测试连通�?
**"JAR文件扫描失败"**
1. 删除 run 包文件夹名中的中文特殊字符（�?(、�?等）
2. �?run 包移动至根目录下（如 D:\run�?
**"A fatal error has been detected by the Java Runtime Environment"**
- 原因：C 平台未更新或与系统架构不匹配
- 解决：重新部署系统对应架构的 C 平台

**"未满足的链接错误"**
- 解决：更新公共组件或 C 平台

**"未发现服务[对象服务]"�?900�?*
- plm-agent 日志报等待目标服务超�?- plm-service 日志存在 JAR 文件扫描失败
- 解决：将 run 包移动至根目�?
#### 服务启动顺序优化

**偶尔连不上加密卡**
- 启动服务前，单独启动注册中心先连接加密卡
- 或在注册中心服务后加延时命令�?  - Linux：`timeout /t 10 /nobreak >nul`
  - Windows：`timeout 10`

**部分服务"数据库连接异�?，部分正�?*
- 解决：所有服务添加内存栈配置（Xms, Xmx�?- 例：`start "业务服务" cmd /k java -jar -Xms1g -Xmx1g -XX:ParallelGCThreads=8 plm-service-5.2.jar`
- 或将服务放在启动命令前半部分，a 端放在后半部分，中间加延�?
#### CLOUD 正常使用后服务突然终�?
1. 检�?run 目录下是否有 hs_err 开头的文件
2. 若存在且�?jvm.dll 字符�?   - 调大内存栈（Xmx, Xms�?   - plm-server �?plm-agent �?1:5 比例启动
   - 一�?plm-agent �?10~20 人使�?   - 单个 jar 内存默认 4~8G
3. 若不�?jvm.dll：将日志发回公司，尝试调大内存栈重启
4. 若无 hs_err 文件：联系技术支�?
#### Linux 系统启动日志刷新很慢（几十秒一次）

1. 输入 `hostname` 查询主机�?2. 输入 `vi /etc/hosts`
3. 在每行最后添加主机名
4. 保存退出（wq!），重启服务

#### Kylin Linux V10(Halberd) 启动报错 C [UNICODE.so+0x9d0]

- 原因：Kylin V10 Halberd �?gconv 库问�?- 解决：替换为 Kylin V10(Lance) �?gconv

### W.2 登录问题排查

#### 登录不了（未修改配置，重启后突然�?
1. 查看全部服务日志，检查是否有"数据库连接失�?
2. 若有，用数据库工具检查用户密码是否到�?3. 到期则修改密�?
#### 登录�?mpm 页面不显示内�?
**方法一**：停止中间件→删�?kmsoft 文件夹→重启中间�?
**方法�?*�?.2版本）：删除操作系统中之前部�?tomcat 时添加的环境变量

#### 登录报错 java.lang.NullPointerException（含 MessageBox�?
�?PDM 库执行：
```sql
update plm_config set cvalue = 0 where cconfig_node = 'RECORD_LOG_LACK_LEVEL_TIPS_SWITCH';
commit;
```

#### 输入密码无误却提示密码错误（按一个字符密码位数增加两位）

- 原因：输入法设置了全�?- 解决：修改为半角

#### 6.0 版本登录提示"当前系统未设置涉密等�?

- 未设置密级前：仅 maintainer 可登�?- 配置路径：参见《安全管理》操作手�?1.3.9 系统密级章节

#### 奇安信浏览器登录提示本地 WebSocket 建立失败

- 关闭选项：可信安全→安全隔离防护�?开启跨域安全隔�?�?开启站点安全隔离按�?

### W.3 流程相关问题

#### 流程提交时很�?
- 原因：流程中提交前后做了大量二开功能
- 解决：将二开功能放入异步队列执行

#### 流程节点流转阻塞（节点还是工作中，提�?已提交不可重复提�?�?
- 原因：流程后事件异常导致阻塞
- 解决�?  1. 修改数据�?pdm_taskeventinfo 表：`cflag` �?-1 改为 0，`exceptionmessage` 改为空串
  2. 重试该节点提�?  3. 重试�?cflag �?1 则成�?  4. 如再次异常需人工排查
- 4.0.1+ 版本有程序重试机�?
#### 步骤无法提交，状态显�?异常"

- task 用户�?pdm_taskeventinfo �?exceptionmessage 列查看异常信�?- 5.2+ 版本：网格上有异常处理重试按�?- 异常包含 .dpl、ExecExtendFunction.handlerAfterTaskSubmitted、DPL注册异常等均为二开异常

#### 工作对象列表无法添加对象

- 工作流模板定义中，执行人权限集合需授予"添加/移除工作对象"权限

### W.4 系统配置迁移

部分配置�?yaml 迁移到系统配置（系统配置-通用配置-平台配置）：

- 主题切换：右上角系统工具栏下拉框可用功能
- 切换为正式环境：右上角系统工具栏下拉框可用功�?- 网格上方搜索工具栏：网格上下工具栏显示模�?- 打印的宽度偏移量：打印配置（5.0+�?- 对象列表默认行数：默认所有网格最大显示行�?- 无操作退出时间：默认无操作退出时间（单位秒）

**注意**：如果同名配置同时存在于系统配置�?yaml 中，需删除 run 目录下的 wpConfig.yaml（只保留 run/config 目录下的�?
### W.5 WORD 签字注意事项（DDB模式�?
#### 模板注意事项

1. 所有模板上的域**不能从其他文档复�?*，必须自定义
2. 图片签字耗性能：尽量放在前 1~5 个表格内，不要放最�?3. 表格中嵌套签字区域：签字节点与签字域区域**必须用格子隔开**
4. 表格太多时（单格总数超过配置值）：将内容表格与签字表�?*拆分**
5. 图片签字的域**尽量命名不一�?*，不要同一个域多处使用
6. Excel 签字：office 不支持多页签存在相同签字域，需集中在一个页�?
#### 性能提升开�?
```xml
<!-- 关闭页眉页脚签字，提升性能 -->
<读写配置 数据源类�?"WORDTRANSLATOR" 页眉页脚限定="0" picturesignauto="yes" 签字格唯一="yes" pictureheight="16" 表格内单格总数="400"/>
```

- `页眉页脚限定="0"`：关闭页眉页脚签�?- `表格内单格总数="400"`：限制签字表格格子数
- `picturesignauto="yes"`：图片自动缩�?- `picturesize="0.5"`：图片高度为域格子高度的 50%，宽度等比缩�?- `pictureheight="24"`：无格子域的图片高度控制
- `签字格唯一="yes"`：签字格唯一

#### 稳定性保护（清除 WORD 临时模板�?
�?DDB_PreH.dpl 签字脚本中添加：
```
// 清除 WORD 临时模板 normal.dotm
try
{
    fileTemp="C:\\Users\\sysadmin\\AppData\\Roaming\\Microsoft\\Templates\\Normal.dotm";
    fileDelete(fileTemp);
}
catch(...)
{}
```

### W.6 Windows 加密卡连接失败排�?
#### 测试命令

```cmd
D:\KMSOFT\COMMON\GetProductInforDlg.exe 31 3 1 5501 5600 192.168.30.140 D:\1.ini
```

参数说明�?- `31`：soft.id
- `3`：product.info
- `1`：permit.number
- `5501`：绑定端口起�?- `5600`：加密卡端口
- `192.168.30.140`：加密卡服务�?IP
- `D:\1.ini`：生成的校验文件

#### 判断结果

- **校验成功**：ini 文件有内�?�?检�?CLOUD yaml 中加密卡配置
- **校验失败**：ini 文件无内�?错误 �?按顺序排�?
#### 排查步骤

1. 检�?GetProductInforDlg.exe 修改日期是否�?2024 年后
   - 若不是：卸载公共组件→删�?COMMON 目录→重新安�?2. 查询加密卡服务器端口是否开放，IP 是否正确

#### Windows 加密卡启动提示套接字错误

- 查看右下角无加密卡图标，但任务管理器中有加密卡后�?- **解决**：停掉加密卡后台，重新启�?
#### Windows 加密卡启动闪退

- 检查加密卡是否过期或未激�?
### W.7 窗口和界面问�?
#### 资源管理器搜索框第一次无返回结果

- 原因：网格开启了按列搜索，无聚焦列时第一次不返回
- 解决：选择需要搜索的列后再搜�?
#### 我的工作/我的任务列表不显示列

- 列头右键→列设置→列显示调整→点击【删除】图标→恢复所有列
- 如果所有列都不显示：删 T_layout_grid 表中对应用户 id 的私有方案配�?
#### 打开对象报错（网格绑定串含关键字�?
- 原因：列名或下拉选项�?`;:()` 等符�?- 解决：去掉这些符�?
#### 表格属性编辑自动插入行

- 检�?wpConfig.yaml �?`showGridBlankRow` 配置
- true 会插入一行，不需要改�?false

---
