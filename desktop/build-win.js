#!/usr/bin/env node
/**
 * 构建 Windows 便携版。
 *
 * 关键点：页面永远从工程根的 ../index.html 拷贝（单一来源），
 * 且打包源目录里不放任何 node_modules —— 产物 app.asar 只含
 * main.js / index.html / package.json 三个文件，体积最小。
 *
 * 用法：npm run build:win   （或 node build-win.js）
 */
const fs = require('fs');
const os = require('os');
const path = require('path');
const packager = require('@electron/packager');

const here = __dirname;
const root = path.resolve(here, '..');
const pkg = JSON.parse(fs.readFileSync(path.join(here, 'package.json'), 'utf8'));
const electronVersion = require('electron/package.json').version;

const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'dpc-stage-'));

function stageApp() {
  fs.copyFileSync(path.join(here, 'main.js'), path.join(stage, 'main.js'));
  fs.copyFileSync(path.join(here, 'preload.js'), path.join(stage, 'preload.js'));

  const src = path.join(root, 'index.html');
  if (!fs.existsSync(src)) throw new Error('缺少页面文件：' + src);
  fs.copyFileSync(src, path.join(stage, 'index.html'));

  // 只保留运行期必需字段；devDependencies 仅用于让打包器确定 Electron 版本
  fs.writeFileSync(path.join(stage, 'package.json'), JSON.stringify({
    name: pkg.name,
    productName: pkg.productName,
    version: pkg.version,
    description: pkg.description,
    author: pkg.author,
    license: pkg.license,
    main: pkg.main,
    devDependencies: { electron: pkg.devDependencies.electron }
  }, null, 2));
}

(async () => {
  try {
    stageApp();
    const outDir = path.join(root, 'dist', 'desktop');
    const paths = await packager({
      dir: stage,
      name: pkg.productName,
      platform: 'win32',
      arch: 'x64',
      out: outDir,
      overwrite: true,
      asar: true,
      prune: true,
      appVersion: pkg.version,
      appCopyright: '© 2026 刘焱',
      electronVersion,
      icon: path.join(here, 'build', 'icon.ico'),
      win32metadata: {
        CompanyName: '刘焱',
        FileDescription: pkg.description,
        ProductName: pkg.productName,
        InternalName: pkg.productName,
        OriginalFilename: pkg.productName + '.exe'
      }
    });
    console.log('打包完成:');
    paths.forEach((p) => console.log('  ' + p));
  } finally {
    fs.rmSync(stage, { recursive: true, force: true });
  }
})().catch((e) => {
  console.error('打包失败:', e);
  process.exit(1);
});
