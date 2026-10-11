// 3D 打印成本计算器 —— Electron 主进程
// 本地离线运行，不加载任何远程内容；数据保存在 WebView 的 localStorage 中。
const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const path = require('path');

const isMac = process.platform === 'darwin';

let mainWin = null;

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
    buildMenu();
    createWindow();
    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0) createWindow();
    });
  });

  app.on('window-all-closed', () => {
    if (!isMac) app.quit();
  });
}
