# 3D 打印成本计算器

一个**离线单文件**的 3D 打印报价工具：算清材料、设备折旧、电费、人工后处理与失败率摊销，
得出单件成本、建议售价与利润。同一份 `index.html` 同时打包成 **网页 / Windows 桌面 / Android** 三端。

- **零依赖**：一个 HTML 文件，双击即用，不联网、不上传数据
- **完整预设**：11 个设备 + 50 个材料预设（拓竹 / 大简 / 三慈 / 通用），可自行增删改
- **实时计算**：成本构成环形图 + 明细表，参数改了立刻出结果
- **数据自主**：全部存在本机，支持导出 CSV、打印 / 存 PDF、**全量备份与恢复**
- **模型估算**：导入 STL / 3MF 自动估用量；若文件来自拓竹 Studio / OrcaSlicer 切片，直接读**切片实测耗材克数与打印时长**（无需手填）
- **深浅色主题**：浅色 / 深色 / 跟随系统三档一键切换，偏好本地记忆（打印与分享长图恒为浅色，保证报价单观感）

## 功能

| 模块 | 说明 |
|---|---|
| 打印参数 | 层高、填充率、尺寸、支撑、失败率等 |
| 材料成本 | 卷价 / 克重 / 用量，支持按件或按克计价 |
| 设备折旧 | 机器价格、寿命小时数、维护费按时摊销 |
| 能耗 | 功率 × 时长 × 电价 |
| 人工与后处理 | 工时费率、后处理耗时、耗材 |
| 定价 | 平台佣金反推挂牌价、目标毛利率 |

关键算法：失败率用摊销法 `失败成本 = 基础成本 × p ÷ (1 − p)`；
挂牌价按佣金反推 `挂牌价 = 基础售价 ÷ (1 − 佣金率)`。

## 下载安装

到 [**Releases**](https://github.com/steveliuyan/3d-print-cost-cn/releases/latest) 直接下载，无需自己构建：

| 平台 | 文件 | 说明 |
|---|---|---|
| 网页 | `3d-print-cost-cn-1.18.0-web.html` | 双击用浏览器打开即用，零依赖、离线 |
| Windows | `3d-print-cost-cn-1.18.0-portable.exe` | 单文件绿色版（约 71 MB），双击运行，免安装 |
| Android | `3d-print-cost-cn-1.18.0.apk` | 约 1 MB；需在系统里允许「安装未知来源应用」。应用内置「检查更新」，可在应用内直接在线升级 |

Android 也可以直接用 adb 安装：

```bash
adb install -r -t 3d-print-cost-cn-1.18.0.apk
```

---

## 目录结构

```
3d-print-cost-calculator/
├─ index.html              ← 唯一来源（改只改这个）
├─ test-presets.js         ← jsdom 回归测试（346 项断言）
├─ _sync_clean.py          ← 剥离预览注入并同步三份副本
├─ _gen_icons.py           ← 三端图标唯一来源（Pillow；favicon / iOS / Android / Windows）
├─ desktop/                ← Electron 桌面工程
│  ├─ main.js              ← 主进程（窗口 / 菜单 / Ctrl+P 打印 / 外链走系统浏览器）
│  ├─ preload.js           ← 预加载脚本（暴露 window.dpc：更新检查等桥接）
│  ├─ build-win.js         ← Windows 打包脚本
│  ├─ rebuild-asar.js      ← 只重建 app.asar（DLL 未变时的快路径）
│  ├─ build-icon.py        ← 旧版桌面图标脚本（已被根目录 _gen_icons.py 取代，仅留作参考）
│  ├─ build/icon.ico       ← 应用图标
│  └─ package.json
├─ android/                ← Android WebView 工程
│  ├─ app/src/main/assets/index.html     ← 页面副本（构建前拷贝）
│  ├─ app/src/main/java/com/dpc/printcost/MainActivity.java
│  └─ keystore.properties  ← 本机签名配置（不入库）
└─ dist/                   ← 构建产物（不入库）
```

## 1. 网页版

直接用浏览器打开 `index.html` 即可，无需服务器。所有数据存在浏览器 `localStorage`。

---

## 2. Windows 桌面版

### 构建

```bash
cd desktop
npm install
npm run build:win          # 产物：../dist/desktop/3D打印成本计算器-win32-x64/
```

打包脚本会把工程根的 `index.html` 拷进临时目录再打包，`app.asar` 内只有
`main.js` / `preload.js` / `index.html` / `package.json` 四个文件。

### 使用

两种形态任选其一：

| 形态 | 路径 | 特点 |
|---|---|---|
| **单文件便携版** | `dist/desktop/3D打印成本计算器-1.18.0-便携版.exe` | 71 MB，双击即用；每次启动会自解压到临时目录，首次打开稍慢 |
| **免安装目录版** | `dist/desktop/3D打印成本计算器-win32-x64/` | 269 MB，启动最快；整个文件夹拷到任意位置都可用 |

无需安装、无需 Node。

- `Ctrl + P` = 打印 / 另存为 PDF（用系统打印对话框）
- `Ctrl + R` = 重新载入，`F12` = 开发者工具（排查问题用）
- 相比网页版，桌面版**下载与打印不受浏览器沙箱限制**，导出 CSV / 备份文件会正常弹出保存框

---

## 3. Android 版

### 构建

```bash
cd android
# 需要 JDK 17；local.properties 里 sdk.dir 指向本机 Android SDK
./gradlew assembleRelease        # 首次会自动下载 Gradle 8.13
```

产物：`app/build/outputs/apk/release/app-release.apk`

> Windows 下用 `gradlew.bat`；`local.properties` 已被 `.gitignore` 排除，
> 克隆后按 `sdk.dir=你的SDK路径` 自行创建。

### 安装

```bash
adb install -r -t android/app/build/outputs/apk/release/app-release.apk
```

### 实现要点

- 单 `Activity` + 单 `WebView`，页面以 `assets/index.html` 打包进 APK
- 用 `WebViewAssetLoader` 把 assets 映射到 `https://appassets.androidplatform.net/`，
  获得正常 Web 源 —— `localStorage`（参数 / 预设 / 分类）才能可靠持久化
- **导出链路走原生桥**：WebView 默认**不处理** `<a download>` + Blob 下载，且页面非 iframe
  （前端的 `isEmbedded()` 兜底不会触发），表现为「点导出 CSV / 备份毫无反应」。
  因此 Java 侧注入 `window.AndroidBridge.saveText(name, mime, content)`，前端 `download()` 优先调用：
  - Android 10+（API 29）：经 `MediaStore.Downloads` 写入系统「下载」目录
  - API 24–28：写入应用专属下载目录（免运行时权限）
  - 保存后弹原生 Toast 告知路径
- **打印走原生打印任务**：WebView **不支持 `window.print()`**（调用后毫无反应）。
  壳里另挂 `AndroidBridge.printPage()`，前端 `doPrint()` 优先调用，由 `PrintManager` +
  `web.createPrintDocumentAdapter()` 拉起系统打印对话框 —— 打印机一栏选**「保存为 PDF」**即可导出 PDF。
  桌面浏览器仍用 `window.print()`。
- `WebChromeClient.onShowFileChooser` + `onActivityResult` 让 `<input type="file">`
  能弹出系统文件选择器 —— **「恢复备份 / 导入预设」必需**
- `WebChromeClient` 接管 `alert` / `confirm`，否则「恢复备份」的二次确认不会显示
- 返回键 = WebView 回退，无历史时退出；有文件选择挂起时先取消选择

### Android 签名

仓库**不含**任何签名密钥。想产出已签名的 release APK，请自备密钥库：

```bash
cd android/app
"C:/Program Files/Zulu/zulu-17/bin/keytool" -genkeypair -v \
  -keystore dpc-release.jks -alias dpc \
  -keyalg RSA -keysize 2048 -validity 10000
```

然后在 `android/keystore.properties` 里填入（该文件已被 `.gitignore` 排除）：

```properties
storeFile=app/dpc-release.jks
storePassword=你的口令
keyAlias=dpc
keyPassword=你的口令
```

- 未创建 `keystore.properties` 时，`assembleRelease` 依然可以跑通，只是产出**未签名** APK。
- 签名方案：APK Signature Scheme **v2 + v3**（`app/build.gradle` 中已固定）。
- 密钥库请务必另行妥善备份 —— 丢了就无法给已安装用户升级。

> ⚠️ 千万不要把 `*.jks` / `keystore.properties` 提交到公开仓库：
> 拿到密钥的人可以签出与你同签名的 APK 来覆盖安装。

---

## 4. 打包版本信息

| 产物 | 版本 | 说明 |
|---|---|---|
| `index.html` | 1.18.0 | 参数 / 预设 / 分类 / CSV / 打印报价单 / 备份恢复 / Android 原生导出与打印桥 / 窄屏预览自适应 / 浅色·深色·跟随系统三档主题 / 应用内更新弹窗与历史更新日志 / STL·3MF 导入估算、切片 3MF 实测用量读取 / 订单化多品项报价（行项 · 抬头编号客户有效期状态 · 阶梯定价 · 订单打印/CSV/长图）/ **经营看板（订单统计：收入·成本·利润·毛利率·客单价 + 月度趋势 + 材料/客户排行 + 经营月报打印）** / **平台活动报名（活动名称 + 活动折扣，与整单/阶梯折扣取大不叠加，报价单与长图标注）** / **建议零售价主视觉（独立高亮块，字号 36px + 毛利率/单件利润）** / **全套界面动效（Hero 流光 · 环图与排行交错画入 · 数字滚动）** / **弹窗滚动锁（遮罩打开时不再穿透滚动背景页）** / **可选账号与云同步（v1.10.0：登录/注册 + 邮箱验证码 + 两步验证 + 十键增量同步 + 冲突三选一；不登录完全可用，token 不进 localStorage）** |
| Windows 桌面版 | 1.18.0 | Electron 33，win32-x64；启动时自动检查更新，「帮助 → 检查更新…」亦可手动触发；更新提示为**应用内弹窗**（与网页 / Android 一致，不再用系统原生对话框） |
| Android APK | 1.18.0 (versionCode 29) | minSdk 24 / targetSdk 35，`com.dpc.printcost`；内置「检查更新」在线升级（下载通知带版本号）；报价长图可直接存入系统相册 |

**可选账号与云同步（v1.10.0）**：在 https://3d.20050905.xyz 顶栏点「登录 / 注册」即可开启。
不登录时一切功能照旧、数据只在本机。登录后 10 个本地键会增量同步到 `api.20050905.xyz`（会话走 HttpOnly cookie，前端不接触 token）；
遇到版本冲突会弹窗让你选「用云端 / 用本地 / 两边都留」。注册、登录、重发验证码都带 Cloudflare Turnstile 人机验证。本地双击打开（`file://`）不启用云同步。

## 5. 改完页面后怎么重新打包

```bash
python _sync_clean.py                              # 把根 index.html 同步到 android assets 与 desktop/
cd android && ./gradlew assembleRelease            # APK
cd ../desktop && node rebuild-asar.js              # 目录版：只换 app.asar（DLL 未变时最快）
npm run dist                                       # 便携版单文件 exe
```

打包前建议先跑一遍回归：

```bash
node test-presets.js     # 期望 492/492 通过
```

> **为什么要有 `_sync_clean.py`**：`index.html` 是唯一来源，但 Android 需要一份在
> `app/src/main/assets/` 下、Electron 需要一份在 `desktop/` 下，改动后必须同步。
> 该脚本还会顺手剥掉编辑器/预览工具注入的 `data-page-node-id="..."` 调试属性
> （某些带 DOM 编辑能力的预览面板会往文件里回写这类属性，一次可达数百处、体积 +20KB）。
>
> 另注：`asar extract-file <asar> index.html` 会把文件解到**当前工作目录**，
> 在工程根执行会覆盖真正的 `index.html`。只查看请用 `asar list`。

---

## 许可证

[MIT](LICENSE) —— 随便用，改了什么也欢迎提 PR。
