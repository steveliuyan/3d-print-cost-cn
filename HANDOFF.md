# HANDOFF.md — 3D 打印成本计算器 · 接手交接单

> **用途**：开新对话时，把这份文档（或文末「启动提示词」）交给 AI，它就能在不翻聊天记录的情况下接手本项目。
> 分工：本文档 = **本次交接单**（现状 / 最近干了什么 / 怎么干活 / 启动提示词）；
> `AGENTS.md` = **深度说明书**（技术细节 / 踩坑 / 发版方法论）；`README.md` = **面向用户**的下载与打包说明。

> 最后更新：2026-10-19（v1.9.0 发布后；已按真实环境修正 git / Node 路径与全部基线数字）

---

## 一、30 秒速览

| 项 | 值 |
|---|---|
| 项目根 | **`H:\3d-print-cost-calculator`** |
| 唯一来源 | **`index.html`**（改只改它 → 再 `_sync_clean.py` 同步三副本） |
| 当前版本 | **v1.10.2**（`APP_VERSION`，versionCode **20**；**已上线** https://3d.20050905.xyz，未打 tag/Release） |
| 本地 = 远端 HEAD | `e4f5ae8941939ef7b0fe3387f16d5fcedc31a5d8`（已推送，Pages `built` @ 同 SHA） |
| 回归测试 | **501/501 通过**（`test-presets.js`，jsdom） |
| 三副本 md5 | `ee0c0de4706d6b914e895476b71511f4`（**303,767 B**，逐字节一致） |
| 最新 Release | **v1.9.0 平台活动报名 + 建议零售价主视觉**（tag **15** 个 / Release **15** 个，latest = v1.9.0） |
| 在线版 | **https://3d.20050905.xyz** |
| 应用仓库 | `https://github.com/steveliuyan/3d-print-cost-cn`（公开，MIT） |
| **站点仓库** | **`https://github.com/steveliuyan/myweb`**（= `www.20050905.xyz`，项目页 `project-dpc.html`）⚠️ 与应用仓库是**两个仓库** |
| 三端形态 | 网页（单文件 `index.html`）/ Windows（Electron 便携 exe）/ Android（WebView 壳 APK） |

---

## 二、这是什么

一个**离线单文件**的 3D 打印报价工具：算清材料、设备折旧、电费、人工后处理与失败率摊销，得出单件成本、建议售价与利润；
再进一步支持**订单化多品项报价**（多行项 / 阶梯定价 / 订单级运费·佣金·折扣）、**分享长图**、**STL·3MF 导入估算**。
**同一份 `index.html`** 装进壳里就是 Windows 版和 Android 版；数据全部存本机 `localStorage`，不联网、不上传。

---

## 三、怎么改、怎么验证、怎么发版

```bash
PY="C:/Users/steveliuyan/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
NODE="C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-6/node.exe"
GIT="C:/Users/steveliuyan/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe"   # ⚠️ git 不在 PATH
export NODE_PATH=C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules

# 1) 改代码：只改根目录 index.html（唯一来源）

# 2) 跑回归（基线 501/501）
"$NODE" test-presets.js

# 3) 同步三副本 + 剥离调试属性（务必，否则 pre-commit 拦截）
"$PY" _sync_clean.py          # 输出三行 md5，必须完全一致

# 4) 打包三端
cd android && ./gradlew assembleRelease   # ← 必须后台运行（前台约 2 分钟被 SIGTERM）
cd desktop && node build-win.js && npm run dist   # 产物 dist/desktop/3D打印成本计算器-<ver>-便携版.exe
# 网页版 = 根 index.html 本身

# 5) 发版：提交 → 推送 → 建 tag/Release
"$PY" _sync_clean.py >/dev/null && "$GIT" add -A && "$GIT" commit -m "..."
"$GIT" ls-remote origin main       # 先探连通性；通了直推 "$GIT" push origin main
"$PY" .secrets/_api_push.py        # 不通时走 Git Data API（离线/被墙兜底，SHA 保持一致）
"$PY" .secrets/_api_release.py     # 改脚本内 TAG/HEAD_SHA/ASSETS 后运行，建 tag + Release + 3 附件

# 6) 改品牌标识 / 图标：只改 _gen_icons.py 的 64×64 几何常量，重跑即产出三端全套
"$PY" _gen_icons.py               # 并自动同步 index.html 的 favicon / 顶栏 .mark / 打印头 BRAND_SVG
```

**改完必须能解释为什么全绿**：TDD 流程 = RED（写失败断言）→ minimal GREEN → 变异测试（故意破坏，确认断言能抓住）→ 恢复 → 全量回归。

---

## 四、最近做了什么（v1.8.0 → v1.8.2）

| 版本 | 内容 |
|---|---|
| **v1.8.0** | 订单视图**交互增强**：行项就地编辑 / 历史订单工具条（搜索·状态分档·排序）/ 草稿自动保存 / 客户库；翻单复制、列表内状态流转、按行覆盖「已调」标记；**品牌标识**改为「纯立方体」并收归 `_gen_icons.py` 单一来源。回归 310 → 346。 |
| **v1.8.1** | **分享长图「客户版 / 内部版」开关**（默认客户版）：<br>· **客户版**给客户看——标题「3D 打印报价单」，只呈现**报价**，成本分项按比例上调、**加总恰好 = 报价总额**，**不显示成本 / 利润 / 毛利率**；其中 **`QUOTE_LOCKED = ["电费","运费 / 包装"]` 保持真实值不上调**（透明信息，客户会觉不合理）。<br>· **内部版**保留完整成本 + 成本/售价/利润/毛利率。<br>· 打印 / 保存 PDF 恒为内部明细，不受切换影响。<br>· 顺带把分享长图顶部的品牌标（旧 ¥ 徽标）重画为与打印头同几何的纯立方体。回归 346 → 363。 |
| **v1.8.2** | **修复安卓桌面图标过大**：自适应图标前景层 `safe_frac 0.31 → 0.205`，立方体占启动器可视区 **93% → 61.5%**（与网页/PWA tile 一致）；旧版圆形图标 `0.44 → 0.305` 同比例；新增 3 条图标占比回归断言。回归 363 → **366**。<br>**同时更新个人站点** `myweb/project-dpc.html`：v1.4.2 → v1.8.2、换官方品牌图标（+ favicon）、修正失效的下载链接、功能亮点补 订单化报价 / 客户版·内部版长图 / STL·3MF。 |

| **v1.8.3** | **经营看板 + 全屏动效 + 横屏/平板适配 + 弹窗滚动锁**：顶栏第三视图「经营看板」——纯函数 `dashStats(orders, range, now)`（订单数 / 收入 / 成本 / 利润 / 毛利率 / 客单价 + 月度趋势 + 材料·客户 TOP5，草稿不计入，区间存 `dpc_dash_v1`）+ 6 张 KPI 滚动卡 + 柱状趋势 + 排行条 + **经营月报打印**；顺带修 `orderCustomerName()`（`customer` 是对象，旧代码当字符串会渲染 `[object Object]`）。全套界面动效（Hero 流光 8s / 环图与图例交错画入 / 数字滚动）+ `reduced-motion` 兜底。横屏手机左右分栏、平板竖屏两栏、`≥1200px` 居中放大；`shortEdges` 打孔屏铺满 + 安全区内边距。弹窗滚动穿透修复（`body.modal-open` + `overscroll-behavior` + `MutationObserver`）。回归 366 → **408** → **421**。 |
| **v1.9.0** | **平台活动报名 + 建议零售价主视觉**：订单级 `activity={on,name,disc}`（`.actbox`：开关 / 活动名 / 活动折扣）；**`effDisc = max(阶梯, 整单, 活动)` 取大不叠加**，上限 90%，未报名恒 0；`computeOrder` 增 `discTotal` / `activity` / 每行 `actApplied`，透出到汇总活动条、报价单抬头与「活动优惠」行、长图 info 行、CSV 三字段、行项折扣列「活动」。`#sellPrice` 移入独立 `.retail` 主视觉（36px 靛蓝 + 毛利率/单件利润副指标），文案统一「建议零售价」。回归 421 → **444**。 |

| **v1.10.0** | **可选账号 + 云同步**：顶栏账号区（不登录照常使用，数据只存本机）。注册/验证码/登录/2FA/退出；认证仅靠 HttpOnly cookie，**前端不存任何 token**。同步 10 个既有键（原样 JSON，裸字符串键按字符串），`dpc_meta` 记版本（不参与同步）；`Storage.prototype.setItem` 钩子打 dirty → 3s 防抖 → `POST /sync/batch`（≤20/批、逐项 `base_version`）；失败 5s/15s/60s/300s 退避 + `online` 立即补推；登录后 `GET /sync` 逐键比对，冲突弹「云端/本地/两边都留」并记 `dpc_conflicts`。仅在 3d / 裸域启用（CORS 白名单），`file://` 自动纯离线。**Turnstile**：注册/登录/重发三处各一个控件（sitekey `0x4AAAAAAFcfg4zaO7N3n25b`），必须携带真实 token。回归 444 → **492**。 |

**文件都在哪**：
- 应用逻辑与 UI：根 `index.html`（三端唯一来源）
- 图标/品牌几何唯一来源：`_gen_icons.py`
- 回归测试：`test-presets.js`
- 同步脚本：`_sync_clean.py`
- 发布脚本（不入库）：`.secrets/_api_push.py` / `_api_release.py` / `_rotate_token.py`
- 工作日志（`工作记录`，不入库）：`.workbuddy/memory/MEMORY.md` + `YYYY-MM-DD.md`

---

## 五、硬性约束（务必遵守）

- **不擅自 `git push`、不 `git checkout --`、不清理未提交的 modified 文件**（发版动作先获用户确认）。
  > 例外：用户已授权「后续开发一并由助手负责部署与发布」，即**授权范围内**可直推与发 Release；仍建议先说明再执行。
- 不擅自**卸载 / 清数据 / 回滚**设备。真机只用 `adb install -r -t`。
- **密钥只收粘贴文本，绝不截图 OCR**；密钥不入源码 / 日志 / DB / APK / UI / 请求体。
- **版本号四处联动**：`index.html` `APP_VERSION`、`android/app/build.gradle`（versionCode +1 / versionName）、
  `desktop/package.json`（version + artifactName）、`README.md`；外加 `test-presets.js` 的版本断言。
- 提交前必须先 `_sync_clean.py`（剥宿主注入的 `data-page-node-id`，否则 pre-commit 钩子拦截）。
- 改完必须跑 `test-presets.js` 全量回归。

---

## 六、已知坑（高频，详见 `AGENTS.md` §6）

1. **`data-page-node-id` 污染**：IDE 预览会把该属性注回 `index.html` → 提交被钩子拦截。用原子命令 `_sync_clean.py && git add -A && git commit`。
2. **安卓自适应图标尺寸**：启动器只显示 108dp 画布中央 **72dp 可视区**；立方体高度 = `2 × safe_frac × 108`。
   `safe_frac=0.205` → 占可视区 61.5%（正解）；旧值 `0.31` → 93%（顶满、显大）。有 3 条回归断言钉住此比例。
3. **同一标识出现在多处**（顶栏 `.mark` / favicon / 打印头 `BRAND_SVG` / 分享长图 canvas / 三端图标）：全部由 `_gen_icons.py` 单一来源生成并自动同步，**勿手改 HTML 里这几处**。
4. **Electron**：`preload.js` 必须同时进 `package.json build.files` 与 `build-win.js stageApp()` 白名单，否则 `window.dpc` 不存在。
5. **asar 查看**：用 `desktop/node_modules/@electron/asar`（不是 `asar` 包）；`extract-file` 会解到当前目录，慎用。
6. **深色模式**：深色令牌必须包在 `@media screen{}` 内，保证打印/长图恒浅色（有回归断言守）。
7. **Gradle 必须后台跑**（前台约 2 分钟被 SIGTERM）。
8. **国内网络**：抓外网需 VPN 全局模式；`github.com:443` 直连时通时不通 —— 发版前先 `git ls-remote origin main`，通就直推，不通走 `.secrets/_api_push.py`。

---

## 七、当前待办

- ⏳ **PAT 仍为 classic 且权限过大**（scopes 含 `admin:org` / `admin:enterprise` / `delete_repo` / `workflow`）。
  建议换成 **fine-grained**（仅本仓库 + contents / issues / releases 写权限）。GitHub 无创建 PAT 的 API，只能网页建；
  建好粘贴文本给 Agent，用 `.secrets/_rotate_token.py` 落盘校验，再去 GitHub 撤销旧的。
- ✅ **交接文档已对齐 v1.9.0**（2026-10-19）：AGENTS.md / HANDOFF.md 的版本、基线、证据、环境路径全部换成实测值。
- ✅ **v1.10.2 已上线**（2026-10-20 push `e4f5ae8` → Pages built）；未打 tag、未建 Release、未打包三端。登录/注册已改版：密码眼睛、确认密码、人机验证未完成时的可操作重试。
- ⚠️ **云同步只在线版可用**（`3d.20050905.xyz` / `20050905.xyz`）：服务端 CORS 白名单只有这两个来源，本地 `file://` / localhost 打开时自动纯离线。
- 💡 可选：站点其他页面的 favicon 尚未统一（目前只 `project-dpc.html` 加了）。
- 💡 可选：站点「应用预览」截图仍是较早版本界面，如需可重新截取。

---

## 八、开新对话时的必读清单（按序）

1. 本文 `HANDOFF.md` 的 §一 ~ §七（建立全局印象）；
2. `.workbuddy/memory/MEMORY.md`（长期约定与易踩坑）；
3. `.workbuddy/memory/2026-10-13.md`（最近一次改了什么、证据）；
4. 需要细节 → `AGENTS.md`（深度说明书）；需要更早历史 → 会话检索工具。

---

## 九、开新对话的启动提示词（复制粘贴给新对话即可）

```text
你现在接手一个已有项目，请先别写代码，先读文档建立上下文。

【项目】
- 名称：3D 打印成本计算器
- 位置（项目根）：H:\3d-print-cost-calculator
- 是什么：一个「离线单文件」的 3D 打印报价工具（算材料/设备折旧/电费/人工/失败率摊销 → 单件成本、
  建议售价与利润），并支持订单化多品项报价、分享长图、STL/3MF 导入估算。
  **同一份 index.html 同时分发成网页 / Windows(Electron) / Android(WebView) 三端**，数据只存本机、不联网。
- 仓库：https://github.com/steveliuyan/3d-print-cost-cn （公开，MIT）
- 在线版：https://3d.20050905.xyz
- 注意：个人站点是**另一个仓库** steveliuyan/myweb（= www.20050905.xyz），其 project-dpc.html 是本站项目页。

【当前状态（接手时请以实际文件为准再核对一次）】
- 版本 v1.10.2（versionCode 20）；回归测试 501/501 通过；三副本 md5 ee0c0de4706d6b914e895476b71511f4（303,767 B）。
- 最新 Release：v1.9.0。最近三版做了什么：v1.8.2 修复安卓图标过大；v1.8.3 经营看板（订单统计/月度趋势/
  材料·客户排行/月报打印）+ 全屏动效 + 横屏/平板适配 + 弹窗滚动锁；v1.9.0 平台活动报名（活动折扣与阶梯/整单取大不叠加）
  + 建议零售价主视觉；v1.10.0 可选账号 + 云同步（不登录完全可用，token 不进 localStorage）。

【请先做这三件事，然后停下来等我派活】
1. 读 H:\3d-print-cost-calculator\HANDOFF.md（本次交接单）、.workbuddy\memory\MEMORY.md（长期约定）、
   .workbuddy\memory\2026-10-13.md（最近进展）；需要细节再看 AGENTS.md。
2. 跑一次回归确认基线：在项目根执行
   NODE_PATH=C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules \
   C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-6/node.exe test-presets.js
   期望「结果: 444/444 通过」。
   注意：本机 git 不在 PATH，要用 C:/Users/steveliuyan/.workbuddy/binaries/PortableGit/versions/1.2.0/cmd/git.exe。
3. 用几句话向我复述：这个项目是什么、当前基线、一条改动的标准流程（唯一来源 index.html → 回归 →
   _sync_clean.py 同步三副本 → 打包 → 发版），以及你注意到的硬性约束。

【工作方式（务必遵守）】
- 唯一来源是根目录 index.html，改完必须跑 test-presets.js，并走 TDD：RED → minimal GREEN → 变异测试 → 恢复 → 全量回归。
- 版本号四处联动（index.html / build.gradle / desktop/package.json / README.md）+ test-presets.js 的版本断言。
- 提交前先 _sync_clean.py 剥 data-page-node-id；发版前先 git ls-remote origin main 探连通性。
- 不擅自 push / checkout -- / 清数据 / 回滚设备；密钥只接受粘贴文本，绝不入源码与日志。
- 动手改功能前，先用一小段话说清「要改什么、改哪几处、怎么验证」，等我确认再开工。

复述完就停下，等我说要开发什么。
```

---

> 说明：本交接单随版本更新。每次发版后请顺手刷新 §一 速览（版本/回归/md5/HEAD）与 §四 最近进展。
