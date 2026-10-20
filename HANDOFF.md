# HANDOFF.md — 3D 打印成本计算器 · 接手交接单

> **用途**：开新对话时，把这份文档（至少文末「§十一 启动提示词」）交给 AI，它就能不翻聊天记录直接接手。
> **分工**：本文档 = 现状 + **你接下来该干什么** + 标准流程；`AGENTS.md` = 深度说明书（技术细节/踩坑/发版方法论）；`README.md` = 面向用户的下载与打包说明。
>
> 最后更新：**2026-10-20（v1.11.0 已发版：三端产物 + Release）**

---

## 一、30 秒速览

| 项 | 值 |
|---|---|
| 项目根 | **`H:\3d-print-cost-calculator`** |
| 唯一来源 | **`index.html`**（改只改它 → 再 `_sync_clean.py` 同步三副本） |
| 当前版本 | **v1.11.0**（`APP_VERSION`，versionCode **29**）— 已上线且已发版 |
| 本地 = 远端 HEAD | 以 `git log --oneline -1` 为准（发版基线 `b75f513994ca437adb97bcfd329300709f2a34f1`） |
| 回归测试 | **536/536 通过**（`test-presets.js`，jsdom） |
| 三副本 md5 | `830f827f299113603009760c22967fec`（**330,797 B**，逐字节一致） |
| 最新 Release | **v1.11.0 账号与云同步 + 抬头模板 / 材料价格库**（tag **16** / Release **16**，latest = v1.11.0，3 附件） |
| 在线版 | **https://3d.20050905.xyz**（GitHub Pages + Cloudflare 自定义域） |
| 应用仓库 | `https://github.com/steveliuyan/3d-print-cost-cn`（公开） |
| **站点仓库** | **`https://github.com/steveliuyan/myweb`**（= `www.20050905.xyz`，项目页 `project-dpc.html`）⚠️ 两个仓库，改站点要单独提交 |
| 三端形态 | 网页（单文件 `index.html`）/ Windows（Electron 便携 exe）/ Android（WebView 壳 APK） |

---

## 二、这是什么

**离线单文件**的 3D 打印报价工具：材料 / 设备折旧 / 电费 / 人工后处理 / 失败率摊销 → 单件成本、建议售价、利润；
再支持**订单化多品项报价**（多行项、阶梯定价、活动折扣、订单级运费·佣金）、**经营看板**、**分享长图（客户版/内部版）**、**STL·3MF 导入估算**。
**同一份 `index.html`** 装进壳里就是 Windows 版与 Android 版。

自 v1.10.0 起增加**可选**账号与云同步：**不登录时功能完全不变、数据只存本机**；登录后 12 个键在设备间同步。
服务端是独立仓库/目录（`H:\笔记本服务器\docker\apps\api\`），**本项目只改客户端**。

---

## 三、接手后先做这 3 件事（10 分钟内）

1. **读三份文档**：本文 → `.workbuddy/memory/MEMORY.md`（长期约定）→ `.workbuddy/memory/2026-10-20.md`（最近两天的改动与证据，含踩坑）。细节再查 `AGENTS.md`。
2. **跑回归确认基线**（在项目根）：
   ```bash
   export NODE_PATH=C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules
   C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-6/node.exe test-presets.js
   # 期望：结果: 536/536 通过
   ```
   注意：**本机 git 不在 PATH**，必须用 `C:/Users/steveliuyan/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe`。
3. **核对线上**：`https://3d.20050905.xyz` 页脚应显示 `v1.11.0`；GitHub `/pages/builds/latest` 应为 `built`。

---

## 四、当前状态（做到哪了）

| 能力 | 状态 |
|---|---|
| 成本计算 / 订单化报价 / 看板 / 分享长图 / STL·3MF | 完成并长期稳定 |
| 三端产物 | **v1.11.0 已打包**：web.html 330,797 B / portable.exe 74,271,205 B / apk 1,287,248 B（vc29）；APK 内 `assets/index.html` 与 EXE `app.asar` 内 `index.html` md5 均 = 源码 |
| 可选账号 | 注册（邮箱验证码 + Turnstile）/ 登录 / **找回密码** / 2FA（TOTP）/ 退出，全部可用 |
| 云同步 | **12 个键**：`dpc_v1`、`dpc_cats_v1`、`dpc_presets_v3`、`dpc_quotes_v1`、`dpc_customers_v1`、`dpc_profile_v1`、`dpc_prices_v1`、`dpc_orders_v1`、`dpc_order_draft_v1`、`dpc_dash_v1`、`dpc_theme_v1`、`dpc_view_v1`；`dpc_meta` / `dpc_conflicts` 不同步 |
| 抬头模板 / 默认参数 / 材料价格库 | v1.11.0 新增，页脚「抬头与默认值」入口 |
| 服务端后台 | 已有「云同步数据」页（`/v1/admin/sync*`），可看/改/删/导出/回滚，旧值进 `sync_item_history`；客户端已对齐其改/删语义 |
| 未完成 | 见 §五 |

---

## 五、你接下来该干什么（按优先级，含验收标准）

### P1 订单键 2MB 分片（唯一已知的硬上限风险）

- **为什么**：服务端单键 2MB、账号 50MB。`dpc_orders_v1` 约 1.5KB/单，**约 1200~1400 单会撞 413**，届时同步整个失效。
- **改哪里**：`index.html` 里 `loadOrders/saveOrders` 与 `KEYS` 附近；建议 `dpc_orders_v1` 保留最近 N 月，其余按年拆 `dpc_orders_v1_2025`，`loadOrders()` 合并读取、`saveOrders()` 按年路由写回。
- **验收**：造 2000 单（脚本生成）→ 每个键 < 2MB → 回归全绿；旧数据（单键）读取无感迁移；`?cloud=1` 下实际推一次看 `usage` 字节数。

### P2 登录体验补完（小，用户感知强）

- 「记住邮箱」（只记邮箱，**不记密码、不记 token**）；
- 2FA 设置页把 `otpauth://` 变成**二维码**（当前只有 secret 手输 + 链接）。
- **验收**：登出再打开登录页，邮箱预填、密码为空；二维码能用验证器 App 扫出同一 secret（有断言）。

### P3 站点页 `myweb` 更新到 v1.11.0

- 站点项目页 `project-dpc.html` 仍写 v1.8.2，下载链接指向旧 Release 附件。
- 要改：版本号、下载链接改成 `3d-print-cost-cn-1.11.0-{web.html,portable.exe,apk}`、功能亮点补「账号/云同步、抬头模板、材料价格库」、预览截图换新版。
- ⚠️ `myweb` 是**另一个仓库**，单独提交（推送方式见 `AGENTS.md` §12）。

### P4 安全收尾

- `.secrets/github-token.txt` 里的 PAT 仍是 **classic 且权限过大**（含 `admin:org` / `delete_repo`）。
  换成 fine-grained（仅本仓库 Contents / Releases 写），用 `.secrets/_rotate_token.py <新token>` 落盘校验后撤销旧的。**token 只要文本，不要截图。**

### P5 可选验证（没有阻塞，但值得做一次）

- **两设备真实同步**：窗口 A 保存抬头模板 → 窗口 B 刷新即生效；故意同时改同一键看冲突对话框；
- **后台联调**：管理员在 `/admin` 改 `dpc_prices_v1` → 客户端下一轮同步收到新值（应无冲突）；删除该键 → 客户端自动重建。

---

## 六、标准工作流

```bash
PY="C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe"
NODE="C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
GIT="C:/Users/steveliuyan/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe"
export NODE_PATH=C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules

# 1) 只改根目录 index.html → 2) 回归（基线 536/536）
"$NODE" test-presets.js

# 3) 同步三副本 + 剥干净（否则 pre-commit 会拦）
"$PY" _sync_clean.py      # 输出三行 md5，必须完全一致

# 4) 打包（都用后台跑）
cd android && JAVA_HOME="C:/Program Files/Eclipse Adoptium/jdk-17.0.20.101-hotspot" ./gradlew assembleRelease --no-daemon
#   ⚠️ 别用 Android Studio 自带 jbr（JDK25）→ 报 "Unsupported class file major version 69"
cd ../desktop && ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm run dist

# 5) 提交 + 推送（github 直连不稳时走 API）
"$PY" _sync_clean.py >/dev/null && "$GIT" add -A && "$GIT" commit -m "..."
"$GIT" ls-remote origin main || true      # 通就直推，不通用下面
"$PY" .secrets/_api_push.py

# 6) 发版（改脚本里 TAG / HEAD_SHA / ASSETS 后运行，产物先放到 dist/release/）
"$PY" .secrets/_api_release.py            # 现有模板；v1.11.0 的副本见 .secrets/_api_release_v1110.py

# 7) 图标 / 品牌几何只改 _gen_icons.py，重跑即同步 index.html 的 favicon / 顶栏 .mark / 打印头 BRAND_SVG
"C:/Users/steveliuyan/.workbuddy/binaries/python/envs/default/Scripts/python.exe" _gen_icons.py
```

**TDD 铁律**：RED（写会失败的断言）→ minimal GREEN → 变异测试（故意破坏，确认断言能抓住）→ 恢复 → 全量回归。改动必须能解释"为什么全绿"。

**版本号四处联动**：`index.html` 的 `APP_VERSION`、`android/app/build.gradle`（versionCode+1/versionName）、`desktop/package.json`（version/artifactName）、`README.md`，外加 `test-presets.js` 的版本断言。

---

## 七、硬性约束（违反会出事）

- **唯一来源是 `index.html`**；`android/app/src/main/assets/index.html` 与 `desktop/index.html` 是副本，只能由 `_sync_clean.py` 生成。
- **不登录必须完全可用**；不能把任何 token / 密码写进 `localStorage`（认证只靠 HttpOnly cookie）。
- **不改现有 localStorage 键名与结构**（老用户数据要能直接读）；新数据只加新键。
- **不擅自 `git push` / `git checkout --` / 清数据 / 回滚设备**（用户已授权本项目发布，但动作要说明后再做）。
- 密钥只接受**粘贴文本**，不入源码 / 日志 / DB / APK / UI / 请求体。
- 提交前必须 `_sync_clean.py`（剥掉 IDE 注入的 `data-page-node-id`）。

---

## 八、踩过的坑（浓缩版，细节见 `AGENTS.md` §6）

1. `data-page-node-id` 污染 → 提交被钩子拦；用原子命令 `_sync_clean.py && git add -A && git commit`。
2. 安卓自适应图标：启动器只显示 108dp 画布中央 72dp 可视区，`safe_frac=0.205` 才是 61.5%（旧 `0.31` 显大）；3 条断言钉住。
3. 同一标识 5 处出现（顶栏/favicon/打印头/长图 canvas/三端图标）→ 全部由 `_gen_icons.py` 生成，**勿手改 HTML**。
4. 深色令牌必须包在 `@media screen{}` 内，否则打印变深色（有断言守）。
5. Gradle 前台会 ~2 分钟被 SIGTERM；且 **JAVA_HOME 要用 JDK17**，Android Studio 自带 jbr 是 JDK25 会直接构建失败。
6. 导出 `window.__DPC` 的对象里**不能引用 Cloud 闭包内的函数**（如 `errMsg`），否则 ReferenceError 被外层 try/catch 吞掉 → 整个 `__DPC` 消失、测试全崩。诊断手法：临时把 catch 改成 `window.__DPC_ERR = String(e.stack)`。
7. asar 校验用 `desktop/node_modules/@electron/asar` 的 `extractFile()`（自写偏移解析会差几个字节）。

---

## 九、服务端契约速查（已读源码核实，**别改服务端**，要改就给维护方提示词）

- 基址 `https://api.20050905.xyz/v1`；CORS 白名单仅 `https://3d.20050905.xyz`、`https://20050905.xyz`；cookie `sid`（HttpOnly）+ `X-CSRF-Token`（取 `csrf` cookie）。
- 认证：注册要 `turnstile_token`；已注册邮箱 → `409 email_taken`；找回密码 `POST /auth/password/forgot`（202，未注册也 202）与 `POST /auth/password/reset`（**204 空响应体**）；`resend-code` 也强制 Turnstile。
- 同步：任意键名；单键 ≤2MB / 500 键 / 50MB，超限 `413 quota_exceeded`；`GET /sync` 每键带 `value/version/updated_at`；推送带 `base_version` 冲突 → `409`（批量里是 `results[].status="conflict"` 且带 `server`）。
- 键不存在但 `base_version != 0` → `conflict{value:null,version:0}`（客户端据此重建，见 v1.10.10）。
- 管理后台：`/admin` 页 + `/v1/admin/sync*`（列表 `prefix` 过滤、详情、编辑带 `expected_version` 走乐观锁、`DELETE` 带 JSON body、导出、历史、回滚）。非管理员一律 **404**。

---

## 十、文件地图

| 文件 | 作用 |
|---|---|
| `index.html` | **唯一来源**：全部 UI + 逻辑（单文件、零依赖、ES5） |
| `test-presets.js` | jsdom 回归（536 条断言，含云同步假服务端、UI、引擎、打包契约） |
| `_sync_clean.py` | 剥调试属性 + 同步三副本 |
| `_gen_icons.py` | 品牌几何唯一来源（三端图标 + favicon + 顶栏 + 打印头） |
| `AGENTS.md` | 深度说明书：技术栈、逐版本时间线、验证证据、环境、发版方法论 |
| `README.md` | 面向用户：下载、打包、签名说明 |
| `.secrets/`（不入库） | `github-token.txt`、`_api_push.py`、`_api_release.py`、`_api_release_v1110.py`、`_rotate_token.py` |
| `.workbuddy/memory/` | `MEMORY.md`（长期约定）+ `2026-10-20.md` 等（每天的工作日志与证据） |
| `dist/release/` | 发版附件暂存（`3d-print-cost-cn-1.11.0-{web.html,portable.exe,apk}`） |

---

## 十一、开新对话的启动提示词（整段复制给新对话）

```text
你现在接手一个已在维护的项目，先别写代码：读文档 → 跑回归 → 向我复述，然后等我派活。

【项目】
- 名称：3D 打印成本计算器；位置：H:\3d-print-cost-calculator
- 形态：单文件 index.html（零依赖 ES5），同一份代码分发成 网页 / Windows(Electron) / Android(WebView) 三端
- 能力：成本计算、订单化多品项报价、经营看板、分享长图（客户版/内部版）、STL·3MF 估算，以及「可选」账号与云同步
- 仓库：https://github.com/steveliuyan/3d-print-cost-cn ｜ 在线版：https://3d.20050905.xyz
- 站点是另一个仓库：steveliuyan/myweb（www.20050905.xyz，项目页 project-dpc.html）
- 服务端不在本项目里（H:\笔记本服务器\docker\apps\api），本项目只改客户端

【当前状态（v1.11.0，2026-10-20 已发版）】
- 回归 536/536 通过；三副本 md5 830f827f299113603009760c22967fec（330,797 B）
- 三端产物已打包并发布 Release v1.11.0（web.html / portable.exe 74,271,205 B / apk 1,287,248 B，vc29）
- 云同步 12 个键；管理后台已有「云同步数据」页，客户端已对齐其改/删语义

【请先做这三件事，然后停下】
1. 读 H:\3d-print-cost-calculator\HANDOFF.md（重点 §五「你接下来该干什么」）、
   .workbuddy\memory\MEMORY.md、.workbuddy\memory\2026-10-20.md；细节查 AGENTS.md。
2. 跑回归确认基线（项目根）：
   NODE_PATH=C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules \
   C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-6/node.exe test-presets.js
   期望「结果: 536/536 通过」。git 不在 PATH：C:/Users/steveliuyan/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe
3. 用几句话复述：项目是什么、当前基线、一条改动的标准流程（改 index.html → 回归 → _sync_clean.py → 打包 → 发版），
   以及你注意到的硬性约束（不登录必须可用、token 不进 localStorage、不改旧键名、单文件无构建）。

【工作方式】
- TDD：先写会失败的断言（RED）→ 最小实现（GREEN）→ 故意破坏验证断言能抓住（变异测试）→ 恢复 → 全量回归。
- 版本号四处联动（index.html / android/app/build.gradle / desktop/package.json / README.md）+ test-presets.js 版本断言。
- 提交前先 _sync_clean.py；发版前先 git ls-remote origin main 探连通性，不通走 .secrets/_api_push.py。
- Gradle 打包必须后台跑，JAVA_HOME 用 "C:/Program Files/Eclipse Adoptium/jdk-17.0.20.101-hotspot"（Android Studio 的 jbr 是 JDK25，会构建失败）。
- 用户已授权本项目部署与发版，但每次动作先说明再执行；不擅自 push / checkout -- / 清数据。
- 动手前先用一小段话说清「改什么、改哪几处、怎么验证」，等我确认。

【接手后可选的下一步（HANDOFF §五 有详细验收标准）】
P1 订单键 2MB 分片（约 1200+ 单会撞限额）；P2 记住邮箱 + 2FA 二维码；
P3 站点页 myweb 更新到 v1.11.0；P4 PAT 换 fine-grained；P5 两设备真实同步 / 后台联调。

复述完就停下，等我说要做什么。
```

---

> 每次发版后请顺手刷新：§一 速览（版本/回归/md5/HEAD/Release）、§四 状态表、§五 待办（做完的划掉）。
