# AGENTS.md — 3D 打印成本计算器（项目交接说明书）

> **新对话请先读完这一篇再动手。** 本文档面向「没有上下文的新 AI / 新协作者」，
> 目标是让接手者在不翻聊天记录的情况下，也能知道**做了什么、在哪、怎么改、怎么验证、怎么发版**。
> 最后更新：2026-10-12（v1.7.0 订单化开发完成，待打包发版）

---

## 0. 30 秒速览（接手第一屏）

| 项 | 值 |
|---|---|
| 项目位置 | **`H:\3d-print-cost-calculator`**（独立项目根；2026-10-12 从工作区迁出） |
| 唯一来源 | **`index.html`**（改只改它，再 `_sync_clean.py` 同步三副本） |
| 当前版本 | **v1.7.0** |
| 本地 HEAD | 以 `git log --oneline -1` 为准（v1.7.0 基线提交，本文档更新会再领先少量提交） |
| 功能提交 | v1.7.0 订单化（见 §9）；tag `v1.5.1` → `dde8b9ca8b`（最新已发布） |
| 回归测试 | **310/310 通过**（`test-presets.js`，jsdom） |
| 三副本 md5 | 以 `_sync_clean.py` 输出为准（三份必须完全一致） |
| 最新 Release | **v1.5.1 更新体验重做**（待发 v1.6.0 / v1.7.0） |
| 在线版 | **https://3d.20050905.xyz**（GitHub Pages + Cloudflare 自定义域） |
| 仓库 | `https://github.com/steveliuyan/3d-print-cost-cn`（公开） |
| 唯一待办 | 打包 + 发版 v1.6.0 / v1.7.0；PAT 仍为 classic 权限过大，待换 fine-grained（见 §11） |

---

## 1. 这是什么

一个**离线单文件**的 3D 打印报价工具：算清材料、设备折旧、电费、人工后处理与失败率摊销，
得出单件成本、建议售价与利润。**同一份 `index.html` 同时分发成 网页 / Windows 桌面 / Android 三端。**

## 2. 技术栈与形态

| 端 | 载体 | 说明 |
|---|---|---|
| 网页 | 根 `index.html` | 单文件、零依赖、纯 vanilla JS，数据存 `localStorage` |
| Windows | `desktop/`（Electron 33） | 打包成便携版单文件 exe |
| Android | `android/`（WebView 壳） | 单 Activity + 单 WebView，assets 里放同一份 `index.html` |

**没有构建期依赖**：网页版双击即用。桌面/安卓只是把同一份 HTML 装进壳里。

## 3. 目录

```
H:\3d-print-cost-calculator\
├─ index.html              ← 唯一来源：改只改这个
├─ test-presets.js         ← jsdom 回归测试（310 项断言）
├─ _sync_clean.py          ← 剥调试属性 + 同步三份副本（重要，见 §6.1）
├─ README.md               ← 面向用户的说明（下载 / 打包 / 签名）
├─ AGENTS.md               ← 本文件
├─ .gitignore              ← 忽略 dist/、node_modules/、.secrets/、*.jks、.workbuddy/
├─ .secrets/               ← 凭据与发版脚本（绝不入库）
├─ .workbuddy/memory/      ← 工作日志 =「聊天记录」的落地（见 §15）
├─ desktop/                ← Electron 工程（main.js / preload.js / build-win.js / rebuild-asar.js）
│                            node_modules 不入库，首次用前 npm install
├─ android/                ← Android WebView 工程（build.gradle / app/src/main/assets/index.html）
└─ dist/                   ← 构建产物（不入库）
```

## 4. 快速开始（最重要的一节）

### 4.1 跑回归测试

```bash
cd H:/3d-print-cost-calculator
export NODE_PATH="C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules"
"C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-2/node.exe" test-presets.js
# 期望：结果: 310/310 通过
```

> **必须带 `NODE_PATH`**：`jsdom` 装在 WorkBuddy 托管工作区
> （`C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules`），
> 不在本项目里。不带就会 `Cannot find module 'jsdom'`。

### 4.2 剥离调试属性 + 同步三份副本

```bash
"C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe" _sync_clean.py
# 输出三行 md5 + 字节数，三份必须完全一致
```

### 4.3 重新打包

```bash
PY="C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe"
$PY _sync_clean.py                              # ① 先同步

cd android && ./gradlew assembleRelease         # ② APK（长时间，务必后台跑）
#   → android/app/build/outputs/apk/release/app-release.apk

cd ../desktop && npm install                    # ③ 首次要装依赖（迁移后 node_modules 不在）
npm run dist                                    # ④ 便携版单文件 exe（后台约 1.5 min）
#   → ../dist/desktop/3D打印成本计算器-<ver>-便携版.exe
```

### 4.4 发版（推送 + Release）

见 **§14**。一句话：`_api_push.py` 推提交 → 改 `_api_release.py` 的 TAG/HEAD_SHA/ASSETS → 跑它。

## 5. 开发铁律（用户明确要求，务必遵守）

1. **`index.html` 是唯一来源**。改只改它，然后跑 `_sync_clean.py` 同步到
   `android/app/src/main/assets/index.html` 与 `desktop/index.html`。
2. **TDD 流程**：RED（真实 runtime 跑出失败）→ minimal GREEN → **变异测试**（故意破坏，
   确认断言真会失败）→ 恢复 → 全量回归。**每一步都要有证据。**
3. **不擅自 `git push`**；不 `git checkout --`；不清理未提交的 modified 文件。
   提交前核对 local SHA 与 remote SHA。
4. **版本号四处联动**：`index.html` 的 `APP_VERSION`、`android/app/build.gradle`
   （`versionCode` +1 / `versionName`）、`desktop/package.json`（`version` + `artifactName`）、`README.md`。
5. `test-presets.js` 里的**版本断言**（footer 版本号 / 徽标 `v1.5.x` / `已是最新版本 vX`）也要跟着改。
6. 改完必须跑 `test-presets.js`，且**改动必须能解释为什么是全绿**。
7. 密钥**只接受粘贴文本**（截图 OCR 不可信）；密钥绝不写进源码 / 日志 / DB / APK / UI。

## 6. 已知坑（踩过的，别再踩）

### 6.1 `data-page-node-id` 属性污染 ⚠️ 高频

WorkBuddy 的 IDE **预览面板会在渲染 HTML 时，往每个标签回写 `data-page-node-id="…"` 调试属性**
（一次可达 400+ 处，体积 +几 KB）。后果：

- `git commit` 会被 **pre-commit 钩子拦下**（报 `✗ index.html —— N 处 data-page-node-id`）。
- 提交/打包前**必须先跑 `_sync_clean.py`**。
- 由于预览是实时回注的，最稳的提交姿势是**一条命令原子完成**：

```bash
python _sync_clean.py >/dev/null && git add -A && git commit -m "..."
```

（`_sync_clean.py` 会先剥源文件的属性，再同步到另两份。）

### 6.2 打印第三页 bug（v1.4.2 已修）

分享长图弹窗 `#shareBox` 也是 `.ov` 且保持 `open`，旧规则 `body.pp .ov{display:block!important}`
会把它一起打进 PDF，形成"第三页是长图"。修法：

```css
body.pp .ov:not(#pprev){display:none!important}
body.pp #pprev{position:static!important; display:block!important}
```

### 6.3 iOS 打印无声失败（v1.4.2 已处理）

iOS Safari **不实现 `window.print()`**（静默无反应）。现在用 `isIOS()` 检测，
弹提示引导用户走 Safari 底部「分享」→「打印」。

### 6.4 深色模式的打印/长图边界（v1.5.0）

深色令牌整块包在 `@media screen{ html[data-theme="dark"]{…} }` 里 —— **打印时深色令牌不生效**，
打印/PDF 恒为浅色白底报价单。分享长图是 canvas 手绘，固定浅色，**刻意不跟随主题**。
改动主题时**不要破坏这个包装**（有回归断言专门守它）。

### 6.5 Electron / 打包

- electron-builder 需镜像：`ELECTRON_MIRROR=npmmirror`。
- `build-win.js` 只产**未打包目录**；要便携 exe 得 `npm run dist`。
- `asar extract-file <asar> index.html` 会把文件解到**当前目录**，在工程根执行会覆盖真 `index.html`；
  只查看请用 `asar list`，核对内容用 `@electron/asar` 的 `extractFile()` 读进内存比 md5。
- **`preload.js` 必须在两处白名单里**：`desktop/package.json` 的 `build.files`
  与 `desktop/build-win.js` 的 `stageApp()`。漏了 → 打包后 `window.dpc` 不存在 → 更新检查静默失败。
- 校验 asar：`dist/desktop/win-unpacked/resources/app.asar` 内 `index.html`/`main.js`/`preload.js` 的 md5 应与源码一致。

### 6.6 域名 / 证书（记录备查）

- `3d.20050905.xyz` 走 Cloudflare **橙云代理**，HTTPS 由 CF 边缘证书提供；
  该 zone 的边缘证书 SAN 含 `20050905.xyz` + `*.20050905.xyz`，**不必等源站证书**。
- 已开 **Always Use HTTPS**（SSL/TLS → Edge Certificates）。
- 换代理状态后本地有 DNS 缓存（TTL 300），测试要么等、要么换通道。
- **国内直连 `3d.20050905.xyz` 会 `HTTP 000`（需 VPN 全局模式）**；线上验证请走 GitHub API
  的 `/pages/builds/latest`（看 `status` 与 `commit`），不要只靠 curl。
- `curl` 取页面 grep 不到内容时，先怀疑**响应被 gzip 压缩**，加 `--compressed`。

## 7. 凭据（都在本机，均被 .gitignore 忽略）

| 位置 | 内容 | 说明 |
|---|---|---|
| `.secrets/github-token.txt` | GitHub PAT（`GITHUB_TOKEN=…`） | 推仓库 / 建 Release 用。**待轮换为 fine-grained**（见 §11） |
| `.secrets/_api_push.py` | 经 API 推送（保持 SHA 一致） | github.com 被墙时的推送手段，用法见 §14 |
| `.secrets/_api_release.py` | 建 tag / Release / 传附件 | 改内部 `TAG` / `HEAD_SHA` / `RELEASE_BODY` / `ASSETS` 后运行 |
| `.secrets/_rotate_token.py` | 校验并落盘新 token | 参数为新 PAT，校验用户名与 push 权限 |
| `android/keystore.properties` | APK 签名口令 | 与下面的 jks 配套 |
| `android/app/dpc-release.jks` | APK 签名密钥库 | **丢了就无法给已安装用户升级**，务必备份 |

> ⚠️ 这几样**永远不要提交或外发**。`.secrets/`、`*.jks`、`keystore.properties` 都在 `.gitignore` 里。
> 另外：WorkBuddy 的 GitHub **连接器**本身已安全保存了一份凭据（AES-256-GCM 加密），
> 新对话里只要连接器处于 connected 状态即可直接用，不必读 `.secrets/`。

## 8. 功能清单（这个软件现在有什么）

| 模块 | 能力 |
|---|---|
| 成本计算 | 材料 / 设备折旧 / 电费 / 人工 / 后处理；失败率**摊销法**；佣金反推挂牌价；单件成本、建议售价与利润 |
| 预设管理 | 设备预设、材料预设、自定义分类；增删改 + 导入导出 |
| 报价操作 | 批量件数 + 批量优惠；保存报价、报价历史（载入 / 删除）、分享长图（Canvas） |
| **订单化报价（v1.7.0）** | **多品项订单**：一单多行项（设备×材料×数量，每行存完整 18 字段参数快照）；**订单抬头**（报价单编号 `DPC-YYYYMMDD-NNN` 日流水 / 状态四态 草稿·已报价·已成交·已归档 / 客户 / 联系方式 / 有效期）；**订单级参数**（运费按件分摊、平台佣金、加价倍率、整单折扣）；**阶梯定价**（3 档 `满 N 件 → 打折%`，与整单折扣**取大不叠加**）；订单级**打印 / CSV / 分享长图**（多行项明细表）；顶栏「单件速算 / 订单报价」分段切换（记住上次视图）。旧 `dpc_quotes_v1` 单条快照**启动时一次性幂等迁移**为订单（旧键保留可回滚） |
| 三端导出 | 打印报价单（A4 预览）/ 导出 CSV / 导出兜底；Android 端长图可直接存相册、原生打印桥 |
| 模型估算 | STL（二进制 / ASCII）与 3MF（Stored / Deflate）导入，算体积、包围盒、按密度与填充率估用量；**切片 3MF（Bambu Studio / OrcaSlicer `Metadata/slice_info.config`）直接读实测耗材克数与打印时长**，无切片数据时回退几何估算 |
| 主题 | 浅色 / 深色 / 跟随系统三档；**深色仅屏幕**，打印与长图恒浅色 |
| **更新体验（v1.5.1）** | **应用内更新弹窗**（三端统一）：发布说明轻量 Markdown 渲染、四态（检查中 / 发现新版 / 已是最新 / 失败+重试）、头部版本徽标 `v当前 → v新版`、平台产物行（按端显示 web.html / .apk / .exe + 体积）；**历史更新日志面板**（页脚「更新日志」，可翻看所有版本） |

## 9. 版本时间线（做了什么）

| 版本 | 内容 |
|---|---|
| v1.4.1 | 3MF 改用内置纯 JS inflate 解压（不依赖 `DecompressionStream`，兼容所有环境） |
| v1.4.2 | **打印修复**：分享长图不再被打成第三页；iOS 打印改用分享菜单引导 |
| — | 部署到子域 **3d.20050905.xyz**（GitHub Pages CNAME + Cloudflare CNAME 记录 + 橙云 + 强制 HTTPS），逐字节验证与本地一致 |
| — | `myweb/project-dpc.html` 的「在线使用」链接由 github.io 改为 3d.20050905.xyz |
| v1.5.0 | **深色模式**：三档主题。顶栏分段控件；`<head>` 内联防闪脚本；~30 处硬编码浅色提升为设计令牌；深色令牌包在 `@media screen` 内保证打印恒浅色 |
| — | **推送**：github.com 被墙（SSH 也被 RST），改走 **GitHub Git Data API**。发现远端/本地曾分叉成两条内容等价平行链，按「以本地为准」把 12 个提交以**完全一致 SHA** 重建到远端。CNAME 保留、tag/Release 完好 |
| — | **打包 + 发版 v1.5.0**：APK（vc9）+ Electron portable exe，3 附件 Release |
| — | **更新体验重做（TDD，回归 196 → 234）**：① 更新弹窗重做——发布说明改轻量 Markdown 渲染（小节/列表/二级缩进/粗体/行内代码/「下载：」弱化注脚），四态，头部版本徽标，平台产物行（按端切换 + 体积 KB/MB）；② 新增**更新日志面板**（页脚「更新日志」），拉 `/releases?per_page=30`，首条展开、可折叠；③ **Electron 统一为应用内弹窗**（新增 `desktop/preload.js` 暴露 `window.dpc.fetchJson`；主进程 `ipcMain.handle('dpc:fetchJson')` + `net` 代理规避 CORS，路径白名单；菜单「检查更新…」改 `webContents.send`）；④ **Android** `updateApp(url, version)` 增版本号参数用于下载通知 |
| — | 修复 Electron 老 bug：「立即升级」在 Windows 上误打开 APK（现按平台挑 EXE） |
| **v1.5.1** | **发版完成**：版本号四处联动升 1.5.1；APK `1,069,404 B`（vc10，证书 `O=DPC`，内部 assets/index.html md5 与源码一致）、EXE `3D打印成本计算器-1.5.1-便携版.exe` `74,231,176 B`（asar 内三文件 md5 全一致）；发布 **v1.5.1 Release**（3 附件 201，tag/release 各 9→10，latest=v1.5.1）；GitHub Pages 已构建（commit `dde8b9ca8b`） |
| **v1.6.0** | **切片 3MF 实测用量读取 + 生产扩展 3MF 支持**：新增 `parseSliceInfo()` 解析 Bambu Studio / OrcaSlicer 的 `Metadata/slice_info.config`（`weight` 克 / `prediction` 秒，`filament used_g` 兜底）；`stlRender` 增显「切片实测 X 克 / 时长」，「填入用量」优先用实测值；无切片数据 / 解析失败**静默回退几何估算**。**关键修复**：支持 3MF **生产扩展**——主 model 用 `<component p:path>` 引用外部 object 文件、`build item`/`component` 的 4×3 仿射 `transform` 逐级复合（拓竹 Studio 导出即此结构，旧实现只读主文件 → 报"无法解析"）；`inflateRaw` 改为**按 ZIP 中央目录 usize 预分配**输出缓冲，显著加速大模型解压。版本号四处联动 1.5.1 → 1.6.0（`APP_VERSION` / build.gradle vc10→11 / desktop package.json+artifactName / README）。**纯前端，零新依赖**。回归 196 → **245** |
| **v1.7.0** | **订单化（多品项报价）**：① **引擎参数化**——把 `compute()` 里「从 DOM 读 18 个 `data-field`」剥出为**纯函数 `computeFrom(fields)`**，`compute()` 退化为 `computeFrom(fieldSnapshot())` 薄封装（v1.6 单件行为逐字节不变）；② 新增 `computeOrder(order)`（多行聚合，**订单级运费按件分摊进各行成本基础**以保持与单件口径一致）、`tierDisc/effDisc`（阶梯与整单折扣取大）、`dpc_orders_v1` 存储与 `migrateQuotes()`（旧 `dpc_quotes_v1` → 订单，幂等、旧键保留）；③ **订单视图 UI**（顶栏分段切换）+ 报价历史面板改造为订单列表；④ 订单级打印 / CSV / 分享长图；⑤ `buildBackup()` **补上订单**（v1.6 及以前备份不含报价历史，顺带修坑）。版本号四处联动 1.6.0 → 1.7.0（build.gradle vc11→12）。**纯前端，零新依赖**。回归 245 → **310** |

## 10. 验证证据（每次发版都要能给出这种证据）

**v1.5.0**：回归 196/196；变异测试 2 组被抓住（改错点击处理 → 5 条 FAIL；`@media screen`→`screenX` → 打印保护 FAIL）。
三副本逐字节一致 147,578 B，md5 `980a7db2da78ecfa17c0ce29c13ec1ae`。

**v1.5.1（更新体验重做）**：回归 **234/234**（新增 38 条断言）。变异测试 **4 组全部被捕获**：

| # | 故意破坏 | 被抓住的断言 |
|---|---|---|
| M1 | 二级标题正则 `#{2,6}` → `#{3,6}` | `Markdown：## 渲染为小节标题` FAIL |
| M2 | 更新日志首条不再默认展开 | `更新日志：最新一条默认展开` FAIL |
| M3 | Android 桥丢掉版本号 | `更新：原生桥带上新版本号` FAIL |
| M4 | 去掉 Electron `window.dpc` 分支 | 3 条 Electron 断言 FAIL |

三副本逐字节一致 159,160 B，md5 `9f927e975490e518351078d05cfd3347`（v1.5.1）。
APK/EXE 产物内部文件 md5 亦与源码一致（见 §9 v1.5.1 行）。

**v1.6.0（切片用量读取 + 生产扩展 3MF）**：RED 断言先失败（237/240）→ minimal GREEN → 全绿；
变异 **3 组被捕获**（M1 去掉 `stlRender` 的「切片实测」拼接 → 重量/时长 FAIL；M2 `stlFill` 改用 `stlEstimate` → 填入 FAIL；
M3 `tfParse` 恒返回单位阵 → transform 缩放断言 FAIL；M4 跳过 `components` 遍历 → 4 条外部对象断言 FAIL）
→ 恢复 → 全量回归 **245/245**。三副本逐字节一致 165,957 B，md5 `f679cd72beb279c466f1e1e5cd43e1fc`。
**真实样本端到端核验**：用户提供的拓竹 3MF（`3D/Objects/object_3.model` 外部对象，96015 顶点 / 192170 三角形，
build transform 缩放 1.1355412）→ 应用输出 **体积 131.71 cm³ · 包围盒 92.8 × 91.2 × 100 mm**，
与**独立 Python 参考实现逐位一致**。测试用**内存构造的 ZIP**（含 Stored/多条目/生产扩展/transform 各种组合）驱动，不依赖外部样本文件。

**v1.7.0（订单化）**：RED 先失败（新增 A1–A9 断言在改造前不成立）→ minimal GREEN → 全绿；
变异 **5 组全部被捕获**（M1 聚合时不把运费分摊入行 → A1 成本/收入/利润 4 条 FAIL；
M2 阶梯 `>=` 改 `>` → A3 三条 FAIL；M3 迁移丢 `fields` → A4 快照断言 FAIL；
M4 `effDisc` 忽略阶梯只看整单折扣 → A3 1 条 + 订单视图「阶梯命中 25%」FAIL；M5 保存订单恒新增不做 upsert → 「重复保存不新增」FAIL）
→ 恢复 → 全量回归 **310/310**。三副本逐字节一致（`_sync_clean.py` 输出 200,945 B，三份同 md5）。
**等价性核验**：`computeOrder(单行订单) === compute()` 逐项（总成本 / 收入 / 利润 / 均件成本 / 毛利率）`toFixed(2)` 相等 —— 保证 v1.6 单件行为**零回归**。

## 11. 未完成 / 待办

- ⏳ **PAT 仍为 classic**：2026-10-12 已换新 token 并用 `.secrets/_rotate_token.py` 落盘校验（归属 `steveliuyan` ✓、有 push ✓、被 .gitignore 忽略），
  但**仍是 classic 型且权限极大**（scopes 含 `admin:enterprise` / `admin:org` / `delete_repo` / `workflow`…），应换为 fine-grained。
  GitHub 无创建 PAT 的 API，只能网页建；建好后用 `.secrets/_rotate_token.py <新token>` 落盘校验，
  再到 <https://github.com/settings/tokens> 撤销旧的。**新 token 请粘贴文本给 Agent，勿发截图。**
- ⏳ **v1.7.0 待打包 + 发版**（与 v1.6.0 合并一次发版即可，v1.6.0 尚未打包）：
  代码已本地提交，回归 **310/310**；下一步 `_sync_clean.py` → Gradle APK（vc12）→ `npm run dist` 便携 exe → `_api_push.py` 推提交 → `_api_release.py` 发 v1.7.0（3 附件）。
- ⏳ **v1.6.0 待打包 + 发版**：见上（若一次发 v1.7.0，v1.6.0 的改动会被一并带出）。
- 💡 **订单视图已知取舍**：行项**不做就地编辑**——用「取回」（把该行参数填回单件页并移除该行）改完再「加入订单」重新加回。若后续觉得琐碎，可加"编辑行"入口。
- 💡 **报价历史「清空全部」**按钮 v1.7.0 前是**死按钮**（无事件），v1.7.0 已补上 `confirm` + 清空逻辑。
- ✅ **v1.5.1 已发版**（提交 `dde8b9ca8b` 已推送；APK/EXE 已核验；Release 已发布；Pages 已构建）。
  产物在 `dist/release/{web.html, 3d-print-cost-cn-1.5.1-portable.exe, 3d-print-cost-cn-1.5.1.apk}`。
- 💡 可选项：`http://` 已能 301 跳 `https://`；GitHub Pages 后台可能有域名 DNS 校验警告，不影响访问。
- 💡 迁移遗留：`desktop/node_modules` 未随仓库带（被 .gitignore 忽略），新机器首次打包前需 `npm install`。

## 12. 关联项目

**比价助手 `price-compare-cn`** —— 另一个还没实现的新项目，设计文档在：
`H:\workbuddy\2026-10-11-01-15-23\price-compare-cn\docs\superpowers\specs\2026-10-11-price-compare-cn-design.md`
（本地优先的商品比价工具：粘贴链接 → 本地 Node 抓取助手解析 → 比价表 / 历史 / 分享；
京东接 `catbus-cli`，其余走分层解析器。**尚未开始编码**。另有 `H:\EnglishLearningSoftware` 为在研英语学习 App。）

---

## 13. 环境速查

| 项 | 路径 |
|---|---|
| 托管 Node | `C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-2/node.exe`（v22.22.2） |
| 托管 Python | `C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe` |
| jsdom（NODE_PATH） | `C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules` |
| Android SDK | `C:/adb`（`local.properties` 里 `sdk.dir=C:/adb`） |
| 构建工具 | `C:/adb/build-tools/35.0.0/{aapt2.exe, apksigner.bat}` |
| git remote | `https://github.com/steveliuyan/3d-print-cost-cn.git` |

> 国内网络：PC/Android 抓外网需 **VPN 全局模式**（规则模式不通）。
> Gradle 前台运行会被 SIGTERM（约 2 分钟），**必须后台运行**。

---

## 14. 被墙时如何推送 / 发版（重要）

本机 `github.com:443` **直连超时**、`ssh.github.com:443` 被 **RST**，`git push/fetch` 全部不可用；
只有 `api.github.com`（及 `codeload` / `raw` / `uploads.github.com`）可达。因此推送与发版一律走
**GitHub Git Data API**：

```bash
PY="C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe"
$PY .secrets/_api_push.py       # 把本地提交推到远端，逐提交 SHA 与本地完全一致
$PY .secrets/_api_release.py    # 建 tag/Release 并上传附件（改脚本内 TAG/HEAD_SHA/ASSETS）
```

要点：
- **别信本地 `origin/main`**——直连不通时它不会更新，远端实际 HEAD 可能已领先/分叉。用
  `curl -H "Authorization: Bearer $TOKEN" https://api.github.com/repos/steveliuyan/3d-print-cost-cn/git/ref/heads/main` 取真值。
- 推送脚本对每个提交**逐字段复制** tree/parents/author/committer/message，保证远端 SHA == 本地 SHA；
  SHA 不一致会**中止且不动远端 ref**。
- 发版后核对：`/releases/latest` 的 `tag_name`、附件 `size` 与 `state=uploaded`、`/tags` 与 `/releases` 计数、
  `/pages/builds/latest` 的 `status=built` 与 `commit`。
- 完整方法论已沉淀为技能：`github-api-push-blocked`（含 `api_push.py` / `create_release.py` / `rotate_token.py`）。
- 正常 `git push` 恢复可用后（VPN 全局模式）仍优先用原生 git。

---

## 15. 工作日志 /「聊天记录」在哪

聊天记录无法直接搬运，但**每天的开发过程都落成了追加式日志**，内容等价于「聊天记录摘要」：

```
H:\3d-print-cost-calculator\.workbuddy\memory\
├─ MEMORY.md        ← 长期稳定的事实与硬性约定（最该先看的那张「备忘卡」）
├─ 2026-10-11.md    ← 当天：三端初版、v1.1~v1.5 的迭代过程
└─ 2026-10-12.md    ← 迁移、推送、发版、更新体验重做、v1.5.1 全流程
```

（同一份副本也在工作区 `H:\workbuddy\2026-10-11-01-15-23\.workbuddy\memory\`，两边内容 md5 一致。）

**新对话接手时的推荐动作**：
1. 读本文件 §0 速览与 §8 功能清单，建立全局印象；
2. 读 `.workbuddy/memory/MEMORY.md`（长期约定）+ 最近一份 `YYYY-MM-DD.md`（最近改了什么、证据）；
3. 跑一次 §4.1 的回归测试，确认基线是 310/310；
4. 需要更多历史（跨项目、或日志没写到的细节）再用**会话检索**工具回忆。

> 写日志的规矩：**只记有长期价值的事实**（改了什么、为什么、证据、待办），
> 不记临时路径、一次性搜索结果、工具报错。日志**追加**，不覆盖。
