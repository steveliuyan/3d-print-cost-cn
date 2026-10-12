# AGENTS.md — 3D 打印成本计算器

> 本文件是给「新对话里的 AI」看的项目交接说明。**先读完这一篇再动手。**
> 最后更新：2026-10-12

---

## 1. 这是什么

一个**离线单文件**的 3D 打印报价工具：算清材料、设备折旧、电费、人工后处理与失败率摊销，
得出单件成本、建议售价与利润。**同一份 `index.html` 同时分发成 网页 / Windows 桌面 / Android 三端。**

- 仓库：`https://github.com/steveliuyan/3d-print-cost-cn`（公开）
- 在线版：**https://3d.20050905.xyz**（GitHub Pages + Cloudflare 自定义域）
- 当前版本：**v1.5.0**
- 项目位置：`H:\3d-print-cost-calculator`
  （2026-10-12 从 `H:\workbuddy\2026-10-11-01-15-23\3d-print-cost-calculator` 复制而来，作为独立项目）

## 2. 技术栈与形态

| 端 | 载体 | 说明 |
|---|---|---|
| 网页 | 根 `index.html` | 单文件、零依赖、纯 vanilla JS，数据存 `localStorage` |
| Windows | `desktop/`（Electron 33） | 打包成便携版单文件 exe |
| Android | `android/`（WebView 壳） | 单 Activity + 单 WebView，assets 里放同一份 `index.html` |

**没有构建期依赖**：网页版双击即用。桌面/安卓只是把同一份 HTML 装进壳里。

## 3. 目录

```
3d-print-cost-calculator/
├─ index.html              ← 唯一来源：改只改这个
├─ test-presets.js         ← jsdom 回归测试（234 项断言）
├─ _sync_clean.py          ← 剥调试属性 + 同步三份副本（重要，见 §6）
├─ README.md               ← 面向用户的说明
├─ AGENTS.md               ← 本文件
├─ .secrets/               ← 凭据（被 .gitignore 忽略，绝不入库）
├─ desktop/                ← Electron 工程（main.js / preload.js / build-win.js；node_modules 可再生）
├─ android/                ← Android WebView 工程
└─ dist/                   ← 构建产物（不入库；本次迁移未带）
```

## 4. 快速开始（最重要的一节）

### 跑回归测试

```bash
cd H:/3d-print-cost-calculator
NODE_PATH="C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules" \
  "C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-2/node.exe" test-presets.js
# 期望：结果: 234/234 通过
```

> **必须带 `NODE_PATH`**：`jsdom` 装在 WorkBuddy 托管工作区
> （`C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules`），
> 不在本项目里。不带就会 `Cannot find module 'jsdom'`。

### 剥离调试属性 + 同步三份副本

```bash
"C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe" _sync_clean.py
# 输出三行 md5，三份必须一致
```

### 重新打包

```bash
python _sync_clean.py                              # 先同步
cd android && ./gradlew assembleRelease            # APK（Windows 用 gradlew.bat）
cd ../desktop && npm install                       # 首次要装依赖
node rebuild-asar.js                               # 目录版：只换 app.asar
npm run dist                                       # 便携版单文件 exe
```

## 5. 开发铁律（用户明确要求）

1. **`index.html` 是唯一来源**。改只改它，然后跑 `_sync_clean.py` 同步到
   `android/app/src/main/assets/index.html` 与 `desktop/index.html`。
2. **TDD 流程**：RED（真实 runtime 跑出失败）→ minimal GREEN → **变异测试**（故意破坏，确认断言会失败）→ 恢复 → 全量回归。
3. **不擅自 `git push`**；不 `git checkout --`；不清理未提交的 modified 文件。
   提交前核对 local SHA 与 remote SHA。
4. **版本号四处联动**：`index.html` 的 `APP_VERSION`、`android/app/build.gradle`
   （`versionCode` +1 / `versionName`）、`desktop/package.json`（`version` + `artifactName`）、`README.md`。
5. `test-presets.js` 里的版本断言（footer 版本号）也要跟着改。
6. 改完要跑 `test-presets.js`，且**改动必须能解释为什么是全绿**。

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
改动主题时**不要破坏这个包装**（有一条回归断言专门守它）。

### 6.5 Electron / 打包

- electron-builder 需镜像：`ELECTRON_MIRROR=npmmirror`。
- `build-win.js` 只产**未打包目录**；要便携 exe 得 `npm run dist`。
- `asar extract-file <asar> index.html` 会把文件解到**当前目录**，在工程根执行会覆盖真 `index.html`；只查看请用 `asar list`。

### 6.6 域名 / 证书（记录备查）

- `3d.20050905.xyz` 走 Cloudflare **橙云代理**，HTTPS 由 CF 边缘证书提供；
  该 zone 的边缘证书 SAN 含 `20050905.xyz` + `*.20050905.xyz`，**不必等源站证书**。
- 已开 **Always Use HTTPS**（SSL/TLS → Edge Certificates）。
- 换代理状态后本地有 DNS 缓存（TTL 300），测试要么等、要么换通道。
- `curl` 取页面 grep 不到内容时，先怀疑**响应被 gzip 压缩**，加 `--compressed`。

## 7. 凭据（都在本机，均被 .gitignore 忽略）

| 位置 | 内容 | 说明 |
|---|---|---|
| `.secrets/github-token.txt` | GitHub PAT（classic，`ghp_…`） | 推仓库 / 建 Release 用。**待轮换为 fine-grained**（见 §9） |
| `.secrets/_api_push.py` | 经 API 推送（保持 SHA 一致） | github.com 被墙时的推送手段，用法见 §12 |
| `.secrets/_api_release.py` | 建 tag / Release / 传附件 | 同上 |
| `.secrets/_rotate_token.py` | 校验并落盘新 token | 参数为新 PAT，校验用户与 push 权限 |
| `android/keystore.properties` | APK 签名口令 | 与下面的 jks 配套 |
| `android/app/dpc-release.jks` | APK 签名密钥库 | **丢了就无法给已安装用户升级**，务必备份 |

> ⚠️ 这三样**永远不要提交或外发**。`.secrets/`、`*.jks`、`keystore.properties` 都在 `.gitignore` 里。
> 另外：WorkBuddy 的 GitHub **连接器**本身已安全保存了一份凭据（AES-256-GCM 加密），
> 新对话里只要连接器处于 connected 状态即可直接用，不必读 `.secrets/`。

## 8. 这个对话里干了什么（2026-10-11 ~ 10-12）

| 版本 | 内容 |
|---|---|
| v1.4.1 | 3MF 改用内置纯 JS inflate 解压（不依赖 `DecompressionStream`，兼容所有环境） |
| v1.4.2 | **打印修复**：分享长图不再被打成第三页；iOS 打印改用分享菜单引导 |
| — | 部署到子域 **3d.20050905.xyz**（GitHub Pages CNAME + Cloudflare CNAME 记录 + 橙云 + 强制 HTTPS），逐字节验证 200/140,097B 与本地一致 |
| — | `myweb/project-dpc.html` 的「在线使用」链接由 github.io 改为 3d.20050905.xyz |
| v1.5.0 | **深色模式**：浅色 / 深色 / 跟随系统三档。顶栏分段控件；`<head>` 内联防闪脚本；~30 处硬编码浅色提升为设计令牌；深色令牌包在 `@media screen` 内保证打印恒浅色 |
| — | **推送**：github.com 被墙（SSH 也被 RST），改走 **GitHub Git Data API**。发现远端/本地曾分叉成两条内容等价平行链，按「以本地为准」把 12 个提交以**完全一致 SHA** 重建到远端 → 远端 main = 本地 HEAD = `7c1152292e`。CNAME 保留、8 个 tag/Release 完好 |
| — | **打包 + 发版**：APK（vc9 / 1.5.0，签名证书 `O=DPC`）与 Electron portable exe 打包完成，发布 **v1.5.0 Release**（3 附件：exe/apk/web.html） |
| — | **更新体验重做（TDD，回归 196 → 234）**：① 更新弹窗重做——发布说明改轻量 Markdown 渲染（小节/列表/二级缩进/粗体/行内代码/「下载：」弱化注脚），四态（检查中转圈 / 发现新版 / 已是最新 / 失败+重试），头部版本徽标 `v当前 → v新版`，平台产物行（web.html / .apk / .exe + 体积 KB/MB，按平台自动切换）；② 新增**更新日志面板**（页脚「更新日志」），拉 `/releases?per_page=30`，首条展开、点击条目折叠/展开；③ **Electron 统一为应用内弹窗**（新增 `desktop/preload.js` 暴露 `window.dpc.fetchJson`，主进程 `ipcMain.handle('dpc:fetchJson')` + `net` 代理规避 CORS；菜单「检查更新…」改为 `webContents.send('dpc:check-update')`）；④ **Android** `updateApp(url, version)` 增加版本号参数，用于下载通知文案 |
| — | 修复 Electron 老 bug：「立即升级」在 Windows 上误打开 APK（现按平台挑 EXE） |

**验证证据**：v1.5.0 回归 **196/196 通过**；变异测试两次均被抓住（改错点击处理 → 5 条 FAIL；
把 `@media screen` 改成 `@media screenX` → 打印保护断言 FAIL）。
三份副本逐字节一致：147,578 B，md5 `980a7db2da78ecfa17c0ce29c13ec1ae`。
APK 内 `assets/index.html` md5 同为此值；EXE 74,227,927 B / APK 1,057,560 B。

**更新体验重做证据**：回归 **234/234 通过**（新增 38 条断言）。变异测试 4 组全部被捕获：
M1 二级标题正则收紧 `#{2,6}`→`#{3,6}` → `## 渲染为小节标题` FAIL；
M2 更新日志首条不再默认展开 → `最新一条默认展开` FAIL；
M3 Android 桥丢掉版本号 → `原生桥带上新版本号` FAIL；
M4 去掉 Electron `window.dpc` 分支 → 3 条 Electron 断言 FAIL。
三份副本逐字节一致：159,160 B，md5 `9f927e975490e518351078d05cfd3347`（v1.5.1）。

## 9. 未完成 / 待办

- ⏳ **轮换 classic PAT**：`.secrets/github-token.txt` 里那份 classic PAT 权限极大
  （含 `admin:enterprise` / `admin:org` / `delete_repo` / `workflow`…），应换为 fine-grained。
  GitHub 无创建 PAT 的 API，只能网页建；建好后用 `.secrets/_rotate_token.py <新token>` 落盘校验，
  再到 <https://github.com/settings/tokens> 撤销旧的。**新 token 请粘贴文本给 Agent，勿发截图。**
- ✅ 已 push 完成（见下方 §8 末）；✅ 已重新打包 APK/EXE 并发布 v1.5.0 Release。
- ⏳ **更新体验重做（v1.5.1）尚未发版**：代码已落地、回归 234/234，版本号已四处联动升到 **1.5.1**
  （`index.html` APP_VERSION / `android/app/build.gradle` versionCode 10 + versionName 1.5.1 /
  `desktop/package.json` version + artifactName / `README.md`），`test-presets.js` 的版本断言也已同步。
  **待办**：重新打包 APK/EXE → 发布 v1.5.1 Release。
- 💡 Electron 打包新增 `desktop/preload.js`：`package.json` 的 `build.files` 与 `build-win.js`
  的 `stageApp()` 都已加进白名单，**别漏**，否则打包后 `window.dpc` 不存在、更新检查会静默失败。
- 💡 可选项：`http://` 已能 301 跳 `https://`；GitHub Pages 后台可能有域名 DNS 校验警告，不影响访问。

## 10. 关联项目

**比价助手 `price-compare-cn`** —— 另一个还没实现的新项目，设计文档在：
`H:\workbuddy\2026-10-11-01-15-23\price-compare-cn\docs\superpowers\specs\2026-10-11-price-compare-cn-design.md`
（本地优先的商品比价工具：粘贴链接 → 本地 Node 抓取助手解析 → 比价表 / 历史 / 分享；
京东接 `catbus-cli`，其余走分层解析器。**尚未开始编码**。）

---

## 11. 环境速查

| 项 | 路径 |
|---|---|
| 托管 Node | `C:/Users/steveliuyan/.workbuddy/binaries/node/versions/22.22.2-2/node.exe`（v22.22.2） |
| 托管 Python | `C:/Users/steveliuyan/.workbuddy/binaries/python/versions/3.13.12/python.exe` |
| jsdom（NODE_PATH） | `C:/Users/steveliuyan/.workbuddy/binaries/node/workspace/node_modules` |
| git remote | `https://github.com/steveliuyan/3d-print-cost-cn.git` |

> 国内网络：PC/Android 抓外网需 **VPN 全局模式**（规则模式不通）。

---

## 12. 被墙时如何推送 / 发版（重要）

本机 `github.com:443` **直连超时**、`ssh.github.com:443` 被 **RST**，`git push/fetch` 全部不可用；
只有 `api.github.com`（及 `codeload` / `raw`）可达。因此推送与发版一律走 **GitHub Git Data API**：

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
- 完整方法论已沉淀为技能：`github-api-push-blocked`（含 `api_push.py` / `create_release.py` / `rotate_token.py`）。
- 正常 `git push` 恢复可用后（VPN 全局模式）仍优先用原生 git。
