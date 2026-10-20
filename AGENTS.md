# AGENTS.md — 3D 打印成本计算器（项目交接说明书）

> **新对话请先读完这一篇再动手。** 本文档面向「没有上下文的新 AI / 新协作者」，
> 目标是让接手者在不翻聊天记录的情况下，也能知道**做了什么、在哪、怎么改、怎么验证、怎么发版**。
> 最后更新：2026-10-19（v1.9.0 已发布；本次修正了文档与真实代码/环境的全部偏差）

---

## 0. 30 秒速览（接手第一屏）

> 另见 **`HANDOFF.md`**（更精简的本次交接单 + 开新对话的启动提示词）。

| 项 | 值 |
|---|---|
| 项目位置 | **`H:\3d-print-cost-calculator`**（独立项目根；2026-10-12 从工作区迁出） |
| 唯一来源 | **`index.html`**（改只改它，再 `_sync_clean.py` 同步三副本） |
| 当前版本 | **v1.10.2**（versionCode 20；**已上线**，未打 tag / 未建 Release） |
| 本地 HEAD | 以 `git log --oneline -1` 为准；**已发布 = tag `v1.9.0` → `173f1bbd91984ffbcb71cb96a29d6c446877bac4`**（v1.8.3 / v1.8.2 / v1.8.1 / v1.8.0 / v1.5.1 保留） |
| 回归测试 | **501/501 通过**（`test-presets.js`，jsdom） |
| 三副本 md5 | `ee0c0de4706d6b914e895476b71511f4`（303,767 B，逐字节一致） |
| 最新 Release | **v1.9.0 平台活动报名 + 建议零售价主视觉**（tag 15 个 / Release 15 个，latest = v1.9.0） |
| 在线版 | **https://3d.20050905.xyz**（GitHub Pages + Cloudflare 自定义域）；**线上当前 = v1.10.2**，`index.html` md5 `ee0c0de4706d6b914e895476b71511f4`（303,767 B） |
| 仓库 | `https://github.com/steveliuyan/3d-print-cost-cn`（公开）；**站点仓库 = `steveliuyan/myweb`**（`www.20050905.xyz`，项目页 `project-dpc.html`） |
| 唯一待办 | PAT 仍为 classic 权限过大，待换 fine-grained（见 §11） |

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
├─ test-presets.js         ← jsdom 回归测试（501 项断言）
├─ _sync_clean.py          ← 剥调试属性 + 同步三份副本（重要，见 §6.1）
├─ README.md               ← 面向用户的说明（下载 / 打包 / 签名）
├─ HANDOFF.md              ← 精简交接单 + 开新对话的启动提示词（新对话先看这个）
├─ AGENTS.md               ← 本文件（深度说明书）
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
"C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-6/node.exe" test-presets.js
# 期望：结果: 501/501 通过
```

> **必须带 `NODE_PATH`**：`jsdom` 装在 WorkBuddy 托管工作区
> （`C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules`），
> 不在本项目里。不带就会 `Cannot find module 'jsdom'`。
>
> ⚠️ **本机 `git` 不在 PATH**：裸写 `git` 会报「无法识别」，必须用绝对路径
> `C:\Users\steveliuyan\.workbuddy\binaries\PortableGit\versions\1.2.0\cmd\git.exe`。
> Node 的版本目录名也会随托管环境变（当前 **22.22.2-6**；旧文档写的 22.22.2-2 已不存在），跑不通先列 `.../node/versions`。

### 4.2 剥离调试属性 + 同步三份副本

```bash
"C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe" _sync_clean.py
# 输出三行 md5 + 字节数，三份必须完全一致
# 该脚本只用标准库：系统 python（本机 3.14.7）直接跑也行
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

### 4.4 重新生成图标（改品牌标识时）

```bash
PY_ENV="C:/Users/steveliuyan/.workbuddy/binaries/python/envs/default/Scripts/python.exe"
"$PY_ENV" _gen_icons.py        # 需要 Pillow（已装在托管 venv default 里）
```

**图标唯一来源 = `_gen_icons.py`**（内含 64×64 品牌几何常量：`CUBE` / `SEAMS` / `SEAM_W` / `STYLES`）。一次产出：
Web（`favicon.svg`/`favicon.ico`、`icon-192/512.png`、`maskable-512.png`）、
iOS（`apple-touch-icon.png` 180 + 167，满幅无透明）、
Android（`mipmap-*` 5 档 `ic_launcher{,_round}.png`、`drawable/ic_launcher_foreground.xml`、
`values/ic_launcher_background.xml`、`mipmap-anydpi-v26/ic_launcher{,_round}.xml`）、
Windows（`desktop/build/icon.{png,ico}`）、品牌资产（`docs/brand/icon-tile.svg` + `logo-mark.svg` + `icon-preview.png`）。
此外生成器会**自动把内联 favicon data-URI、顶栏 `.mark` 内嵌 SVG、报价单抬头 `BRAND_SVG` 同步进 `index.html`**
（`sync_favicon_uri()` / `sync_topbar_mark()` / `sync_brand_svg()`，正则容忍 IDE 预览回注属性）——改几何只改本脚本，勿手改 HTML。
改完**必须再跑 `_sync_clean.py`**（三副本同步 + 剥离注入属性，含 `logo-preview.html`）。

> ⚠️ **标识缩放占比（`STYLES`，v1.8.2 关键）**：立方体占各自「可视区」比例须统一 ≈61%，否则桌面图标会显大。
> `tile=0.61(线性)` / `touch=0.55` / `round=0.305(径向)` / `maskable=0.40(径向)`；
> **Android 自适应前景 `android_vector(safe_frac=0.205)`** —— 启动器只显示 108dp 画布中央 **72dp 可视区**，
> 立方体高 = `2 × safe_frac × 108`，`0.205 → 占可视区 61.5%`；**旧值 0.31 → 93%**（几乎顶边、显大，用户已报过）。
> `test-presets.js` 有 3 条断言读 `ic_launcher_foreground.xml` 钉住此比例（<75%）。

> 注意：`index.html` 的 favicon 用**内联 data-URI**（保证单文件自洽）；`_gen_icons.py` 会**自动把它同步进 head**
> （正则容忍 IDE 预览回注的多余属性）。`desktop/build/icon.png` 被 `.gitignore` 忽略（Windows 打包只用 `icon.ico`）。
> 生成器需 Pillow：托管 venv `python/envs/default` 内已装（`.../Scripts/python.exe`）。

### 4.5 发版（推送 + Release）

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
| **分享长图（v1.8.1）** | 分享框有 **「客户版（默认）/ 内部版」** 切换。**客户版**（给客户）：标题「3D 打印报价单」，只呈现**报价**；`quoteBreakdown()` 把成本分项按比例**上调到加总 = 报价总额**（利润揉进分项，无成本/利润/毛利率行），其中 **`QUOTE_LOCKED = ["电费","运费 / 包装"]` 保持真实值不上调**，尾差并入末个非锁定项。**内部版**保留成本构成 + 成本/售价/收入/利润/毛利率。**打印 / 保存 PDF 恒为内部明细**，不受切换影响。canvas 品牌标 `drawBrandMark()` 与打印头 `BRAND_SVG` 同几何（纯立方体，无 ¥） |
| **交互增强（v1.8.0）** | **A 档**：① **行项就地编辑**（订单视图内点「编辑」展开 6 项快速表单：数量 / 打印时长 / 耗材用量 / 材料单价 / 损耗率 / 后处理，输入即写回该行 `fields` 并**只刷数字不重建 DOM** 保住焦点）；② **历史订单工具条**（关键词搜索 + 状态分档 chips + 金额/时间排序 + 空态）；③ **草稿自动保存**（编辑 800ms 防抖落盘 `dpc_order_draft_v1`，刷新/重启恢复，界面提示「草稿已保存」，保存后自动清除 + 新建时确认丢弃）；④ **客户库**（`dpc_customers_v1`，上限 50，去重置顶，datalist 复用，选中带出联系方式）。**B 档**：⑤ **品牌标识**（矢量 SVG 内嵌 + Canvas 同构复刻，打印页/分享长图头部统一品牌头，源文件 `docs/brand/logo-mark.svg`）；⑥ **翻单/复制**（订单历史一键复制为新单，新 id/编号/时间）；⑦ **状态流转**（列表内下拉直接改 草稿·已报价·已成交·已归档 并即时持久化）；⑧ **按行覆盖**（被单独调整的行标「已调」） |
| **经营看板（v1.8.3）** | 顶栏视图第三档「经营看板」（`body.view-dash` + `#dashMain`）。纯函数 `dashStats(orders, range, now)` 聚合：订单数 / 收入 / 成本 / 利润 / 毛利率 / 客单价 + **月度趋势** + **材料 TOP5** + **客户 TOP5**（草稿不计入；区间 `30/90/year/all` 存 `dpc_dash_v1`）；渲染 6 张 KPI（复用 `animateNum` 滚动）+ 柱状趋势 + 排行条 + 空态；看板视图下「打印 / PDF」输出**经营月报**（`brandHeadHTML` + 总览/月度/材料/客户四表） |
| **界面动效（v1.8.3）** | Hero 蓝卡**流光**（`::before` 250% 斜向光带 `heroSheen` 8s 慢扫）；环图弧段 `segIn` **交错画入**（`renderDonut` 每段 `--d=idx*70ms`）；图例行 `lgIn` 错峰入场；数字滚动。全部带 `prefers-reduced-motion` 兜底（无限动画显式 `animation:none`） |
| **横屏 / 平板适配（v1.8.3）** | `viewport-fit=cover`；三档 `@media screen`：① 横屏手机 `(orientation:landscape) and (max-height:560px)`——顶栏收紧、输入区/结果区**左右分栏**；② 平板竖屏 `820–1080px`——两栏 + `.side` 吸顶；③ `≥1200px`——容器 1440px 居中放大。Android `themes.xml` 开 `windowLayoutInDisplayCutoutMode=shortEdges`，页面用 `env(safe-area-inset-*)` 让开打孔屏 |
| **弹窗滚动锁（v1.8.3）** | 遮罩打开时 `body.modal-open{overflow:hidden;padding-right:var(--sbw)}` 防背景穿透滚动；`.ov-body/.modal-body/.pk-body` 加 `overscroll-behavior:contain`；JS 用 `MutationObserver` 监听 body 子树 class 统一同步（所有 open/close 入口无需逐个改），打印样式里解除锁避免只印一页 |
| **平台活动报名（v1.9.0）** | 订单级 `.actbox`：开关 `#ordActOn` + 活动名 `#ordActName` + 活动折扣 `#ordActDisc`；存 `orderLevel.activity={on,name,disc}`（老订单无字段按未报名兼容）。**折扣口径 `effDisc = max(阶梯, 整单, 活动)`，取大不叠加**，上限 90%。`computeOrder` 输出 `discTotal` / `activity` / 每行 `actApplied`；透出到订单汇总活动条、报价单抬头与汇总「活动优惠」、长图 info 行、CSV 三字段、行项折扣列「活动」 |
| **可选账号 / 云同步（v1.10.0）** | 顶栏账号区（未登录「登录 / 注册」，登录后邮箱首字母 + 下拉菜单）。**不登录时一切功能照旧、数据只存本机**。注册（邮箱验证码）/ 登录 / 两步验证（TOTP，展示 secret + otpauth 链接）/ 退出；**认证只靠 HttpOnly cookie，前端不接触也不存储任何 token**。同步对象是**下述 10 个既有键**（一个不多一个不少），`value` 是该键原样解析后的值（裸字符串键按字符串传）；每键版本与 dirty 记在 `dpc_meta`（**不参与同步**）。写 `localStorage` 走 `Storage.prototype.setItem` 钩子打 dirty → **3 秒防抖** → `POST /sync/batch`（≤20 项/批，每项带 `base_version`）→ 成功写回版本。失败保留 dirty 并按 **5s→15s→60s→300s** 退避（最多 10 次），`online` 事件立即补推。登录后 `GET /sync` 逐键比对：服务端更新且本地干净 → 覆盖并**调用页面现有渲染函数**重绘；本地有未推送改动 → 记 `dpc_conflicts` + 红点 + 三选一对话框（用云端 / 用本地 / 两边都留→云端另存 `key.conflict.<ts>`）。409 一律不静默覆盖。**仅在 `3d.20050905.xyz` / `20050905.xyz` 启用**（服务端 CORS 白名单），`file://` 或 localhost 打开自动纯离线，`?cloud=1` 可临时调试。**人机验证**：注册 / 登录 / 重发验证码三处各渲染一个 Turnstile 控件（sitekey `0x4AAAAAAFcfg4zaO7N3n25b`），请求必须携带真实 `turnstile_token`（服务端开启后空 token 一律 `400 captcha_failed`）；令牌一次性，请求返回后 `turnstile.reset()` 重新挑战，脚本加载失败时静默降级并给出「重新验证」提示 |
| **建议零售价主视觉（v1.9.0）** | `#sellPrice` 从小 KPI（19px）移入独立 `.retail` 主视觉：36px 靛蓝数字 + 左色条 + 毛利率 / 单件利润副指标；打印与长图文案统一「建议零售价」 |

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
| **v1.8.0** | **交互增强（A/B 档）+ 品牌标识**：**A 档**——A1 行项就地编辑（6 项表单，输入即写回 `ln.fields` 并 `refreshLineNumbers()` 只刷数字不重建 DOM）、A2 历史订单工具条（搜索 + 状态 chips + 排序 + 空态）、A3 草稿自动保存（`dpc_order_draft_v1`，800ms 防抖 / 恢复 / 保存即清 / 新建确认）、A4 客户库（`dpc_customers_v1`，去重置顶 + datalist + 带出联系方式）；**B 档**——B5 品牌标识（内嵌 `BRAND_SVG` 矢量 + Canvas `drawBrandMark()` 复刻，打印页/长图统一品牌头）、B6 翻单复制、B7 列表内状态流转、B8 按行覆盖「已调」标记。配套矢量 logo 源文件 `docs/brand/logo-mark.svg` + 预览页 `docs/brand/logo-preview.html`。版本号四处联动 1.7.0 → 1.8.0（build.gradle vc12→13）。**纯前端，零新依赖**。回归 310 → **342**。**品牌图标**：由 `_gen_icons.py` 重绘三端全套（Web/iOS/Android 自适应/Windows），后续修正**顶栏漏改 + 徽标比例失衡**（几何收归单一来源、徽标内收居中），回归 → **346** |
| **v1.8.1** | **分享长图「客户版 / 内部版」+ 品牌标统一**：① 分享框加分段开关（默认**客户版**）；`quoteBreakdown(items,totalCost,revenue,locked)` 把成本分项按比例**上调到加总 = 报价总额**，客户版**无成本/利润/毛利率**；**`QUOTE_LOCKED=["电费","运费 / 包装"]` 锁真实值、不上调**（透明信息），尾差并入末个非锁定项；`shareSummaryRows()` 客户版只回「报价总额」一行；② 打印 / PDF **恒为内部明细**，不受切换影响；③ 分享长图顶部品牌标（旧 ¥ 徽标）重画为与打印头 `BRAND_SVG` **同几何的纯立方体**。文件：`index.html`（`drawShareImage`/`drawOrderShareImage`/`shareMode`/`shareKind`）。**纯前端，零新依赖**。回归 346 → **363** |
| **v1.8.2** | **修复安卓桌面图标过大 + 站点更新**：① `_gen_icons.py` 自适应前景 **`safe_frac 0.31 → 0.205`**（立方体占启动器 72dp 可视区 **93% → 61.5%**，与网页/PWA tile 一致）；旧版圆形 `round 0.44 → 0.305` 同比例；② `test-presets.js` 新增 **3 条图标占比断言**（解析 `ic_launcher_foreground.xml`）。版本号四处联动 1.8.1 → 1.8.2（build.gradle vc14→15）。**纯前端 + 资源**，零新依赖。回归 363 → **366**。③ 同步更新个人站点 `myweb/project-dpc.html`（v1.4.2 → v1.8.2、换官方品牌图标 + favicon、修正失效下载链接、功能亮点补 订单化报价 / 客户版·内部版长图 / STL·3MF），站点仓库提交 `c08b7fc` |
| **v1.8.3** | **经营看板 + 全屏动效 + 横屏/平板适配 + 弹窗滚动锁**：① 第三视图「经营看板」——纯函数 `dashStats(orders, range, now)`（订单数/收入/成本/利润/毛利率/客单价 + 月度趋势 + 材料·客户 TOP5，草稿不计入，区间存 `dpc_dash_v1`）+ 6 张 KPI 滚动卡 + 柱状趋势 + 排行条 + **经营月报打印**；顺带修 `orderCustomerName()`（`customer` 是 `{name,contact}` 对象，旧代码当字符串用会渲染 `[object Object]`）。② 全套界面动效（Hero 流光 / 环图与图例交错画入 / 数字滚动）+ `reduced-motion` 兜底。③ 横屏手机左右分栏、平板竖屏两栏、`≥1200px` 收窄居中；`shortEdges` 打孔屏铺满 + 安全区内边距。④ 弹窗滚动穿透修复（`body.modal-open` + `overscroll-behavior` + `MutationObserver` 统一同步）。版本 1.8.2 → 1.8.3（vc15→16）。回归 366 → 378（动效）→ **408**（看板 + 滚动锁）→ **421**（适配） |
| **v1.9.0** | **平台活动报名 + 建议零售价主视觉**：① 订单级 `activity={on,name,disc}`；`effDisc = max(阶梯, 整单, 活动)` **取大不叠加**、上限 90%、未报名恒 0；`computeOrder` 增 `discTotal` / `activity` / 每行 `actApplied`；透出到汇总条、报价单抬头与「活动优惠」汇总行、长图 info 行、CSV（三字段）、行项折扣列「活动」。② `#sellPrice` 移入 `.retail` 主视觉（36px 靛蓝 + 左色条 + 毛利率/单件利润），文案统一「建议零售价」。版本 1.8.3 → 1.9.0（vc16→17）。回归 421 → **444**。发布：API 推 `173f1bb`、Release 3 附件、站点页更新 `5b3c679` |
| **v1.10.0** | **可选账号 + 云同步（客户端）**：顶栏账号区 + 注册/验证码/登录/2FA/退出 + 十键增量同步。`Storage.prototype.setItem` 钩子标记 dirty（不改动任何现有 34 处调用点、不改旧键名与结构）→ 3s 防抖批量推（≤20/批、逐项 `base_version`）→ `dpc_meta` 记版本；5s/15s/60s/300s 指数退避 + `online` 立即补推；登录后 `GET /sync` 逐键比对，冲突记 `dpc_conflicts` 并弹「云端/本地/两边都留」；`dpc_view_v1` 等裸字符串键按字符串往返。**来源门控**：仅 3d / 裸域启用（服务端 CORS 白名单），本地打开自动纯离线。版本 1.9.0 → 1.10.0（vc17→18）。回归 444 → **492** |
| **v1.10.1 / v1.10.2** | **登录/注册弹窗改版**：① 密码框**眼睛切换**（登录、注册、确认密码三处，`aria-pressed` 同步）；② 注册新增**确认密码**，前端校验「两次不一致 / 不足 10 位」→ 不发请求；③ 人机验证**未拿到 token 时不发请求**，改为提示「人机验证还没完成，请稍等一下再试」并给出「重新进行人机验证」按钮（8s 上限，可重试）；④ 弹窗紧凑化（缩短标签、加提示行、面板 460px / 92vh，常规窗口无需滚动）。1.10.0 → 1.10.2（vc18→20）。回归 492 → **501** |

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

**v1.8.0（交互增强 A/B 档 + 品牌标识）**：RED 先失败（新增 v1.8 断言在实现前不成立）→ minimal GREEN → 全绿；
变异 **3 组全部被捕获**（M1 客户库去重禁用 → `A4 重复客户去重` FAIL；M2 行项写回 `ln.fields[key]=inp.value` 禁用 →
`A1 改值即触发该行重算` FAIL〔该断言为变异暴露的**覆盖缺口**后补强：原断言只查 DOM 结构，变异竟漏过，遂增设「成本/汇总文本必须变化」〕；
M3 保存后 `clearDraft` 的 `localStorage.removeItem` 禁用 → `A3 保存订单后草稿被清除` FAIL）
→ 恢复 → 全量回归 **342/342**。三副本逐字节一致 222,712 B，md5 `4924a963c2a2a6fc0091d7fc5c627636`。
源码在变异前后与备份 `diff` 逐字节一致（确认变异已完全还原）。

**v1.8.0 品牌标识修正（顶栏漏改 + 比例失衡）**：用户反馈「网页顶栏图标没换」+「logo 比例失衡、右下角徽标压边」。
根因：① 顶栏 `.mark` 仍是旧版「仅立方体」硬编码 SVG（从未随 v1.8.0 品牌重绘更新）；
② `logo-mark.svg` 的 ¥ 徽标（`cx=48 cy=48 r=11.5`）右缘到 59.5，**越过外框描边内边（58）**，且整体包围盒中心 (38, 35.5) ≠ 画布中心 (32,32) → 视觉压边 + 重心偏右下；
③ `logo-mark.svg`（徽标 48,48,r11.5）与应用图标几何（47,47,r10）**两套画法**，故「不像等比例缩小」。
修正：几何收归 `_gen_icons.py` 单一来源常量（立方体平移 + 徽标 `r 11.5→9` 内收），令**包围盒中心 = (32,32)、四边留白对称 (L/R 6.75, T/B 4.2)、徽标离框 ≥4**；
顶栏标识改由 `build_mark_inner_svg()` 生成并 `sync_topbar_mark()` 自动同步进 `index.html`；`_gen_icons.py` 同时负责生成 `logo-mark.svg`。
新增 **4 条品牌一致性断言**（顶栏几何 / favicon 含新徽标 / 打印头 BRAND_SVG 几何），专门守「单面漏改」——
这正是旧顶栏漏改溜过回归的**覆盖缺口**。变异 **3 组全部被捕获**（M1 顶栏 `cx 42.25→48` → 几何断言 FAIL；
M2 删顶栏徽标圆 → 「已换新徽标」+ 几何 2 条 FAIL；M3 打印头徽标半径回退 `r=9→11.5` → BRAND_SVG 几何断言 FAIL）
→ 恢复 → 全量回归 **346/346**。三副本逐字节一致 223,724 B，md5 `36149f9fdef386a3815a6afe2a1ee091`。
另修 `_sync_clean.py`：一并剥离 `docs/brand/logo-preview.html` 的 IDE 注入属性（否则 pre-commit 拦截）。

**v1.8.1（分享长图 客户版/内部版）**：RED 先失败（新增 12 条 ＋ 3 条锁定断言在实现前不成立）→ minimal GREEN → 全绿；
变异 **2 组被捕获**（M1 `quoteBreakdown` 的 k 恒 1（不上调）→ `分项 ≠ 真实成本` FAIL；M2 `isLock` 恒 false → 电费/运费锁定 2 条 FAIL）
→ 恢复 → 全量回归 **363/363**。三副本逐字节一致 227,022 B，md5 `98db2e5a54b19adecec7001f6dfc05a3`。
**真实渲染核验**（`@napi-rs/canvas` 无头实绘，非模拟）：客户版 电费 **¥0.36 = 内部版真实值**，
`10.09+5.81+0.36+6.72+2.69+2.29 = 27.96 = 报价总额`，无利润/毛利率；内部版保留 成本 10.62 / 利润 17.33 · 62.0%。
APK（vc14）1,186,276 B / EXE 74,270,166 B，asar 内 index.html md5 与源一致。

**v1.8.2（安卓图标尺寸修正）**：新增 3 条断言先 RED（366 中 2 条 FAIL / 居中断言 PASS）→ 调 `safe_frac` 至 GREEN；
变异：把 `safe_frac` 改回 0.31（重跑 `_gen_icons.py`）→ `占可视区 ~61.5%` 与 `不顶满 <75%` **2 条 FAIL（364/366）** →
恢复 → 全量回归 **366/366**。三副本逐字节一致 227,022 B，md5 `823abb51e3e5ea2a19a5b20affe5f5ad`。
**真机核验**：`adb install -r -t`（vc15）后截启动器桌面，立方体留白由「几乎顶边」变为「与相邻应用一致」。
APK 1,183,436 B（内嵌 index.html md5 = 源）；EXE 74,271,338 B（asar 内 index.html md5 = 源，version 1.8.2）。

**v1.8.3（经营看板 + 动效 + 横屏/平板适配 + 滚动锁）**：看板 20 条 + 滚动锁 6 条断言先 RED（`dashStats` 不存在 → TypeError）→ GREEN **408/408**；
变异 4 组均被捕获（去掉草稿过滤 / `MutationObserver` 的 `subtree=false` / 只认 `modal` 遮罩 等）→ 恢复。
动效 12 条断言 RED → **378/378**（变异：8s→0.8s / 去 donut `--d` / 去 `.lg` 动画，3 组全被穿透）。
横屏/平板 11 条断言 RED → **421/421**（变异：横屏分栏退回单栏 / 去掉 `shortEdges` / 顶栏按钮竖排）。
三副本 md5 `e08c407ea80c6a60b5ac73b9c18f5a37`（246,725 B），适配后 `91fc5168…`（`_sync_clean.py` 输出）。
**真机 / 模拟器实测**（M2102J2SC 1080×2340@440）：竖屏 OK；`user_rotation=1` 横屏左右分栏、无黑边；
`wm size 1600x2560 + density 240`（≈1066dp）平板竖屏两栏 OK；`2560x1600` 大屏居中放大 OK（测完已复位）。

**v1.9.0（平台活动 + 建议零售价主视觉）**：新增 `runV19Tests` 23 条断言，RED 16 条 → GREEN **444/444**（一次全绿）；
变异 3 处（`effDisc` 去掉活动 / 汇总去掉活动条 / 零售价 36→22px）全部被捕获 → 恢复（md5 回 `44b8b1b4…`）→ 全量 444。
**接手复核（2026-10-19 实测，逐项本机验证）**：回归 **444/444，0 FAIL，exit 0**；
三副本 md5 `1ae37c077ade73083b27c50c929140eb`（258,163 B）；`data-page-node-id` 0 处；
APK 内嵌 `assets/index.html` md5 = 源码（APK 1,214,616 B）；
EXE `app.asar` 内 `index.html` / `main.js` / `preload.js` md5 全部 = 源码（含 4 文件，preload 在位）；
Release 附件 74,275,209 / 258,163 / 1,214,616 B 与本地 `dist/release/` 完全对应、`state=uploaded`；
Pages `built` @ `173f1bb`；线上站点页 `project-dpc.html` 已到 v1.9.0（`5b3c679`）。

**v1.10.0（可选账号 + 云同步）**：新增 `runCloudTests` **43 条**断言（jsdom + 注入 fetch + 注入定时器，真实页面代码）：
契约 10 键、`product:"dpc"`、`credentials:"include"`、`X-CSRF-Token` 取自 csrf cookie、**token 不落任何 localStorage 键**、
3s 防抖、≤20/批、`base_version`、版本回写、409 冲突三选一、拉取覆盖 + 现有重渲染、5s/15s 退避、`online` 补推、
退出保留数据、断网 + 空存储计算照常、2FA setup 展示 secret、**双「设备」共享假服务端的端到端 A→B 同步**。
RED：先只注入测试 → `444/445`（唯一新增断言失败）→ 注入实现 → `482/482` → 补端到端 3 条 → **487/487**。
变异 **4 组全部被捕获**（M1 批量上限 20→1 → 2 条 FAIL；M2 推送成功不写版本 → 3 条 FAIL；
M3 去掉 CSRF 头 → 1 条 FAIL；M4 拉取不写回本地 → 2 条 FAIL）→ 原样恢复 → 487/487。
三副本 md5 `93cef3b2c588c2ef2aaf315b4737d8e8`（298,017 B），`data-page-node-id` 0 处。
**线上接口冒烟（2026-10-20，生产）**：`GET /v1/health` 200（`mail:smtp`；接入前 `turnstile:false`，用户 2026-10-20 开启）；
`GET /v1/me`、`GET /v1/sync`、`POST /v1/sync/batch` 未登录均 **401**；
`OPTIONS /v1/sync/dpc_v1` **204** 且 `access-control-allow-origin: https://3d.20050905.xyz`、
`allow-credentials: true`、`allow-headers` 含 `X-CSRF-Token` —— 证明浏览器 cookie 会话 + CSRF 头链路按契约可用。
**Turnstile 接入（服务端开启后补齐）**：新增 5 条断言（sitekey 值 / 三个容器同 sitekey / 登录·注册·重发都带真实 token / `captcha_failed` 文案）；
先 RED `487/492` → 实现后 GREEN **492/492**。生产实测：空 token 的 `POST /auth/register` 与 `POST /auth/login` 均
`400 {"error":{"code":"captcha_failed","message":"缺少人机验证"}}`；`challenges.cloudflare.com/turnstile/v0/api.js` 302 可达。
**上线与真实浏览器实测（2026-10-20）**：`git push` → Pages `built` @ `a104e84`；线上 `https://3d.20050905.xyz/index.html`
md5 `93cef3b2c588c2ef2aaf315b4737d8e8`（298,017 B，与源码一致），`APP_VERSION=1.10.0`、sitekey 在线上文件内。
用 CDP 驱动本机 Edge（独立 user-data-dir，真实指纹）实测：账号弹窗打开、Turnstile 控件加载、**取到真实 token**（`1.elc24Dhv4V…`），
用故意错误的口令提交 → 界面显示 **「邮箱或密码错误」**（服务端 `invalid_credentials`，说明 captcha 已放行，链路打通）；
另用空 token 提交 → 服务端 `400 captcha_failed` → 界面显示「人机验证未通过或已过期，请重新验证后再试」；
`localStorage` 中检索 `sid|token|csrf` 键名与 token 值均为空。
**未执行**：真实注册→收码→验证（生产 `MAIL_MODE=smtp`，验证码只进邮箱，本机无该邮箱访问权）；
登录态下 DevTools 的 `sid` HttpOnly/Secure 核对与两台真机同步（需已登录账号）。

**v1.10.1 / v1.10.2（登录/注册改版）**：新增 9 条断言（眼睛切换×3 / 确认密码存在 / 两次不一致不发请求 / 密码不足 10 位不发请求 /
人机验证未完成时不发请求且有重试入口 / 三个容器同 sitekey 等），RED `496/501` → 实现后 **501/501**。
真机 CDP 实测（线上 1.10.2）：注册步骤三字段齐全、3 个眼睛按钮、`type` 在 password↔text 间切换、`aria-pressed` 正确；
两次不一致提示「两次输入的密码不一致」、短密码提示「密码至少 10 位（服务端要求）」；
用 CDP 阻断 `challenges.cloudflare.com` 后点登录 → 显示「人机验证还没完成，请稍等一下再试」且「重新进行人机验证」按钮可见（不再卡在等待文案）。
截图：`.workbuddy/ui-register-1102.png`、`.workbuddy/ui-captcha-retry.png`。

## 11. 未完成 / 待办

- ⏳ **PAT 仍为 classic**：2026-10-12 已换新 token 并用 `.secrets/_rotate_token.py` 落盘校验（归属 `steveliuyan` ✓、有 push ✓、被 .gitignore 忽略），
  但**仍是 classic 型且权限极大**（scopes 含 `admin:enterprise` / `admin:org` / `delete_repo` / `workflow`…），应换为 fine-grained。
  GitHub 无创建 PAT 的 API，只能网页建；建好后用 `.secrets/_rotate_token.py <新token>` 落盘校验，
  再到 <https://github.com/settings/tokens> 撤销旧的。**新 token 请粘贴文本给 Agent，勿发截图。**
- ✅ **已发版**：v1.5.1 / v1.6.0 / v1.7.0 / v1.8.0 / v1.8.1 / v1.8.2 / **v1.8.3 / v1.9.0** 均已打包 + 建 Release（各 3 附件）。
  最新 = **v1.9.0**（提交 `173f1bb`；tag 15 个 / Release 15 个）；产物在 `dist/release/3d-print-cost-cn-1.9.0-{web.html,…-portable.exe,.apk}`。
- ✅ **v1.10.2 已上线**（2026-10-20：`950ba12`→`e4f5ae8`，Pages `built`；线上 md5 = 源码）。
  **未打 tag / 未建 Release / 未打包三端**；需要时补 tag + Release + 三端产物。
- 💡 登录/注册后续可做：找回密码（契约里未提供接口，需服务端先加）、记住邮箱、2FA 二维码（当前展示 secret 手输）。
- 💡 **可选**：个人站点 `myweb` 其他页面的 favicon 尚未统一（目前只 `project-dpc.html` 加了）；站点「应用预览」截图仍为较早版本界面。
- 💡 **订单视图**：行项**就地编辑** v1.8.0 已落地（点「编辑」展开 6 项快速表单，输入即写回并重算；「取回」仍保留，用于把该行参数搬回单件页）。
- 💡 **报价历史「清空全部」**按钮 v1.7.0 前是**死按钮**（无事件），v1.7.0 已补上 `confirm` + 清空逻辑。
- ✅ **v1.5.1 已发版**（提交 `dde8b9ca8b` 已推送；APK/EXE 已核验；Release 已发布；Pages 已构建）。
  产物在 `dist/release/{web.html, 3d-print-cost-cn-1.5.1-portable.exe, 3d-print-cost-cn-1.5.1.apk}`。
- 💡 可选项：`http://` 已能 301 跳 `https://`；GitHub Pages 后台可能有域名 DNS 校验警告，不影响访问。
- 💡 迁移遗留：`desktop/node_modules` 未随仓库带（被 .gitignore 忽略），新机器首次打包前需 `npm install`。

## 12. 关联项目

**个人站点 `myweb`**（= `www.20050905.xyz`）—— 本应用的项目页在其中：`steveliuyan/myweb` 仓库的 `project-dpc.html`
（商城风格：应用图标 / 下载按钮 / 应用预览 / 功能亮点 / 版本信息）。
- ⚠️ **与应用仓库是两个仓库**，改站点要单独提交到 `myweb`。
- ⚠️ 克隆必须落在**工作区内**（沙箱禁写工作区外；克隆到 `/h/myweb` 会失败并留幻影目录）；推送用 token URL：
  `git push https://x-access-token:TOKEN@github.com/steveliuyan/myweb.git HEAD:main`。
- 应用图标资源：把 `icon-192.png` 拷为站点 `dpc-icon.png`，并作页面 `favicon` / `apple-touch-icon`；
  下载链接须指向当前 Release 的**实际附件名**（旧版 `web.html` 等已失效）。

**比价助手 `price-compare-cn`** —— 另一个还没实现的新项目，设计文档在：
`H:\workbuddy\2026-10-11-01-15-23\price-compare-cn\docs\superpowers\specs\2026-10-11-price-compare-cn-design.md`
（本地优先的商品比价工具：粘贴链接 → 本地 Node 抓取助手解析 → 比价表 / 历史 / 分享；
京东接 `catbus-cli`，其余走分层解析器。**尚未开始编码**。另有 `H:\EnglishLearningSoftware` 为在研英语学习 App。）

---

## 13. 环境速查

| 项 | 路径 |
|---|---|
| 托管 Node | `C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-6/node.exe`（v22.22.2；**目录名会随环境变，跑不通先列 `versions`**） |
| 托管 Python | `C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe`（另：系统 `python` = 3.14.7，`_sync_clean.py` 只用标准库） |
| 托管 Python（含 Pillow） | `C:/Users/steveliuyan/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（`_gen_icons.py` 用） |
| **git（不在 PATH！）** | `C:\Users\steveliuyan\.workbuddy\binaries\PortableGit\versions\1.2.0\cmd\git.exe` |
| jsdom（NODE_PATH） | `C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules` |
| Android SDK | `C:/adb`（`local.properties` 里 `sdk.dir=C:/adb`） |
| 构建工具 | `C:/adb/build-tools/35.0.0/{aapt2.exe, apksigner.bat}` |
| git remote | `https://github.com/steveliuyan/3d-print-cost-cn.git` |

> 国内网络：PC/Android 抓外网需 **VPN 全局模式**（规则模式不通）。
> Gradle 前台运行会被 SIGTERM（约 2 分钟），**必须后台运行**。

---

## 14. 被墙时如何推送 / 发版（重要）

本机 `github.com:443` 的**连通性随网络/VPN 状态波动**：2026-10-13 与 2026-10-19 实测可直连
（v1.8.2/v1.9.0 均直推成功），也曾长时间直连超时、`ssh.github.com:443` 被 RST。
**发版前先 `git ls-remote origin main` 探一次**：通就 `git push`（天然 SHA 一致，最快）；不通再走
**GitHub Git Data API**（只需 `api.github.com` / `uploads.github.com`）：

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
├─ 2026-10-12.md    ← 迁移、推送、发版、更新体验重做、订单化 v1.7.0、品牌
└─ 2026-10-13.md    ← v1.8.0 交互增强、v1.8.1 客户版/内部版长图、v1.8.2 图标修正 + 站点更新；
                       后续未另建文件，**v1.8.3 / v1.9.0（2026-10-14 ~ 10-17）继续追加在本文件末尾**
```

**新对话接手时的推荐动作**：
1. 读 `HANDOFF.md`（本次交接单 + 启动提示词）→ 再读本文件 §0 速览与 §8 功能清单；
2. 读 `.workbuddy/memory/MEMORY.md`（长期约定）+ 最近一份 `YYYY-MM-DD.md`（最近改了什么、证据）；
3. 跑一次 §4.1 的回归测试，确认基线是 **501/501**；
4. 需要更多历史（跨项目、或日志没写到的细节）再用**会话检索**工具回忆。

> 写日志的规矩：**只记有长期价值的事实**（改了什么、为什么、证据、待办），
> 不记临时路径、一次性搜索结果、工具报错。日志**追加**，不覆盖。
