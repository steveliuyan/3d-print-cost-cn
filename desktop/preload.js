// 3D 打印成本计算器 —— Electron 预加载脚本
// contextIsolation 下，页面无法直连 GitHub API（CORS / CSP），
// 这里只暴露两件最小能力：API 代理 与 菜单触发的「检查更新」通知。
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('dpc', {
  // 代理 GitHub API GET（主进程 net，无 CORS 限制）
  // path 形如 /repos/{owner}/{repo}/releases/latest 或 /repos/.../releases?per_page=30
  fetchJson: (path) => ipcRenderer.invoke('dpc:fetchJson', String(path || '')),

  // 主进程菜单「检查更新…」→ 回到页面内统一弹窗
  onCheckUpdate: (cb) => {
    if (typeof cb === 'function') ipcRenderer.on('dpc:check-update', () => cb());
  }
});
