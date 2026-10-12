// 3D 打印成本计算器 —— Electron 主进程
// 本地离线运行，不加载任何远程内容；数据保存在 WebView 的 localStorage 中。
const { app, BrowserWindow, Menu, shell, dialog, net, ipcMain } = require('electron');
const path = require('path');

const isMac = process.platform === 'darwin';
const REPO = 'steveliuyan/3d-print-cost-cn';
const API_BASE = 'https://api.github.com';

let mainWin = null;

/* ===== 检查更新 =====
   统一走页面内弹窗（与 Web / Android 端一致），主进程只提供网络代理：
   contextIsolation 下渲染进程无法直连 GitHub API，改由 IPC + net 规避 CORS。
   仅放行本仓库 releases 相关路径，避免代理被滥用。 */
function githubGet(pathname) {
  return new Promise((resolve, reject) => {
    const allow = new RegExp('^/repos/' + REPO.replace('/', '\\/') + '/releases(\\?|/|$)');
    if (!allow.test(pathname)) { reject(new Error('forbidden path')); return; }
    const req = net.request(API_BASE + pathname);
    req.setHeader('User-Agent', 'print-cost-calculator');
    req.setHeader('Accept', 'application/vnd.github+json');
    let data = '';
    req.on('response', (res) => {
      res.on('data', (c) => { data += c; });
      res.on('end', () => {
        if (res.statusCode < 200 || res.statusCode >= 300) { reject(new Error('HTTP ' + res.statusCode)); return; }
        try { resolve(JSON.parse(data)); } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.end();
  });
}

/* 菜单「检查更新…」→ 通知页面跑统一弹窗（不再使用系统原生对话框） */
function requestCheckUpdate() {
  if (mainWin && !mainWin.isDestroyed()) mainWin.webContents.send('dpc:check-update');
}

function createWindow() {
  mainWin = new BrowserWindow({
    width: 1240,
    height: 860,
    minWidth: 940,
    minHeight: 640,
    backgroundColor: '#f4f5f8',
    title: '3D 打印成本计算器',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      spellcheck: false,
      // 打印预览 / 导出均为本地能力，不需要任何远程权限
      webSecurity: true
    }
  });

  mainWin.once('ready-to-show', () => mainWin.show());
  mainWin.loadFile(path.join(__dirname, 'index.html'));

  // 外链一律交给系统浏览器，应用窗口本身只承载本地页面
  mainWin.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:/i.test(url)) shell.openExternal(url);
    return { action: 'deny' };
  });
  mainWin.webContents.on('will-navigate', (e, url) => {
    if (!url.startsWith('file://')) {
      e.preventDefault();
      if (/^https?:/i.test(url)) shell.openExternal(url);
    }
  });

  mainWin.on('closed', () => { mainWin = null; });
}

function buildMenu() {
  const template = [
    {
      label: '文件',
      submenu: [
        { label: '重新载入', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { type: 'separator' },
        {
          label: '打印 / 另存为 PDF…',
          accelerator: 'CmdOrCtrl+P',
          click: () => { if (mainWin) mainWin.webContents.print({}); }
        },
        { type: 'separator' },
        isMac ? { label: '关闭窗口', role: 'close' } : { label: '退出', accelerator: 'Alt+F4', role: 'quit' }
      ]
    },
    {
      label: '编辑',
      submenu: [
        { label: '撤销', role: 'undo' },
        { label: '重做', role: 'redo' },
        { type: 'separator' },
        { label: '剪切', role: 'cut' },
        { label: '复制', role: 'copy' },
        { label: '粘贴', role: 'paste' },
        { label: '全选', role: 'selectAll' }
      ]
    },
    {
      label: '视图',
      submenu: [
        { label: '放大', role: 'zoomIn' },
        { label: '缩小', role: 'zoomOut' },
        { label: '实际大小', role: 'resetZoom' },
        { type: 'separator' },
        { label: '全屏', role: 'togglefullscreen' },
        { type: 'separator' },
        { label: '开发者工具', accelerator: 'F12', role: 'toggleDevTools' }
      ]
    },
    {
      label: '帮助',
      submenu: [
        {
          label: '检查更新…',
          click: () => requestCheckUpdate()
        },
        { type: 'separator' },
        {
          label: '关于本软件',
          click: () => {
            dialog.showMessageBox(mainWin, {
              type: 'info',
              title: '关于',
              message: '3D 打印成本计算器',
              detail: '版本 ' + app.getVersion() + '\n\n' +
                '本地离线运行：不联网、不上传任何数据，参数与预设仅保存在本机。\n' +
                '支持设备 / 材料预设、自定义分类、CSV 导出、打印报价单与全量备份恢复。'
            });
          }
        }
      ]
    }
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// 单实例，避免重复打开
const gotLock = app.requestSingleInstanceLock();
if (!gotLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (mainWin) {
      if (mainWin.isMinimized()) mainWin.restore();
      mainWin.focus();
    }
  });

  app.whenReady().then(() => {
    /* 更新检查的网络代理（渲染进程经 preload 调用） */
    ipcMain.handle('dpc:fetchJson', (e, p) => githubGet(String(p || '')));
    buildMenu();
    createWindow();
    /* 启动静默检查更新交由页面内统一弹窗处理（3s 后自动触发，仅壳内生效） */
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on('window-all-closed', () => {
    if (!isMac) app.quit();
  });
}
