#!/usr/bin/env node
/* 仅重建 app.asar 并就地覆盖（运行时 DLL 未变，避免 packager 整目录覆盖触发沙箱批量删除守卫） */
const fs = require('fs');
const os = require('os');
const path = require('path');
const asar = require(path.join(__dirname, 'node_modules', '@electron', 'asar'));

const here = __dirname;
const root = path.resolve(here, '..');
const pkg = JSON.parse(fs.readFileSync(path.join(here, 'package.json'), 'utf8'));

const stage = fs.mkdtempSync(path.join(os.tmpdir(), 'dpc-asar-'));
fs.copyFileSync(path.join(here, 'main.js'), path.join(stage, 'main.js'));
fs.copyFileSync(path.join(here, 'index.html'), path.join(stage, 'index.html'));
fs.writeFileSync(path.join(stage, 'package.json'), JSON.stringify({
  name: pkg.name, productName: pkg.productName, version: pkg.version,
  description: pkg.description, author: pkg.author, license: pkg.license,
  main: pkg.main,
  devDependencies: { electron: pkg.devDependencies.electron }
}, null, 2));

const target = path.join(root, 'dist', 'desktop', pkg.productName + '-win32-x64', 'resources', 'app.asar');
const tmpAsar = path.join(stage, 'app.asar');

asar.createPackage(stage + '/', tmpAsar).then(() => {
  const buf = fs.readFileSync(tmpAsar);
  fs.writeFileSync(target, buf);
  console.log('app.asar 已重建并覆盖:');
  console.log('  target :', target);
  console.log('  bytes  :', buf.length);
  console.log('  files  :', asar.listPackage(tmpAsar).join(' | '));
  const ih = asar.extractFile(tmpAsar, 'index.html');
  console.log('  index.html:', ih.length, 'bytes md5', require('crypto').createHash('md5').update(ih).digest('hex'));
  fs.rmSync(stage, { recursive: true, force: true });
}).catch((e) => { console.error('失败:', e); process.exit(1); });
