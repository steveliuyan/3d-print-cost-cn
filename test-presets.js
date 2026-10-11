const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  url: 'http://localhost/',
  pretendToBeVisual: true
});
const w = dom.window, d = w.document;

w.confirm = function () { return true; };
w.print = function () {};

const out = [];
function ok(name, cond, extra) {
  out.push((cond ? 'PASS  ' : 'FAIL  ') + name + (extra !== undefined ? '   [' + extra + ']' : ''));
  if (!cond) process.exitCode = 1;
}
function click(el) { el.dispatchEvent(new w.MouseEvent('click', { bubbles: true })); }
function change(el) { el.dispatchEvent(new w.Event('change', { bubbles: true })); }
function input(el) { el.dispatchEvent(new w.Event('input', { bubbles: true })); }
function field(id) { return d.querySelector('[data-field="' + id + '"]'); }

setTimeout(function () {

  /* ===== 0. Android WebView 原生导出桥（回归：真机导出 CSV / 备份 / 预设 无反应） =====
     真机 WebView 默认不处理 <a download> + Blob 下载，且页面非 iframe，
     isEmbedded() 为 false → 旧实现静默失败。必须优先走 JS 桥写入系统「下载」目录。 */
  (function () {
    var calls = [], anchors = 0, prints = 0, bridgePrints = 0;
    var dom2 = new JSDOM(html, {
      runScripts: 'dangerously',
      url: 'https://appassets.androidplatform.net/assets/index.html',
      pretendToBeVisual: true,
      beforeParse: function (win) {
        win.AndroidBridge = {
          saveText: function (f, m, c) { calls.push({ f: f, m: m, c: c }); },
          printPage: function () { bridgePrints++; return true; }
        };
        win.confirm = function () { return true; };
        win.print = function () { prints++; };
      }
    });
    var w2 = dom2.window, d2 = w2.document;
    w2.URL.createObjectURL = function () { anchors++; return 'blob:x'; };

    d2.getElementById('btnCsv').dispatchEvent(new w2.MouseEvent('click', { bubbles: true }));
    ok('Android：导出 CSV 走原生桥 saveText', calls.length === 1 && /\.csv$/.test(calls[0].f),
       calls[0] && calls[0].f);
    ok('Android：CSV 内容含 BOM 与成本表头',
       !!(calls[0] && /^\ufeff/.test(calls[0].c) && /成本项目/.test(calls[0].c)));
    ok('Android：CSV 不再走 <a download>', anchors === 0, 'anchors=' + anchors);

    d2.getElementById('btnBackup').dispatchEvent(new w2.MouseEvent('click', { bubbles: true }));
    ok('Android：备份全部数据走原生桥', calls.length === 2 && /备份.*\.json$/.test(calls[1].f),
       calls[1] && calls[1].f);
    var bj2 = null;
    try { bj2 = JSON.parse(calls[1].c); } catch (e) {}
    ok('Android：备份内容为合法 dpc-backup JSON', !!bj2 && bj2.type === 'dpc-backup');
    ok('Android：备份未走 <a download>', anchors === 0, 'anchors=' + anchors);

    /* 打印 / 保存 PDF：Android WebView 不支持 window.print()，必须走原生打印桥 */
    var ppBtn2 = d2.getElementById('ppPrint');
    ppBtn2.dispatchEvent(new w2.MouseEvent('click', { bubbles: true }));
    ok('Android：点「打印 / 保存为 PDF」走原生打印桥', bridgePrints === 1, 'bridge=' + bridgePrints);
    ok('Android：未调用无效的 window.print()', prints === 0, 'prints=' + prints);
    ok('Android：打印前已挂 body.pp 打印模式', d2.body.classList.contains('pp'));

    /* 无桥的普通浏览器：应仍走原生 <a download> 路径 */
    var dom3 = new JSDOM(html, {
      runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
      beforeParse: function (win) { win.confirm = function () { return true; }; }
    });
    var w3 = dom3.window, d3 = w3.document, anchors3 = 0, prints3 = 0;
    w3.URL.createObjectURL = function () { anchors3++; return 'blob:y'; };
    w3.URL.revokeObjectURL = function () {};
    w3.HTMLAnchorElement.prototype.click = function () {};
    w3.print = function () { prints3++; };
    d3.getElementById('btnCsv').dispatchEvent(new w3.MouseEvent('click', { bubbles: true }));
    ok('普通浏览器：仍走 <a download> 下载', anchors3 === 1, 'anchors=' + anchors3);
    d3.getElementById('ppPrint').dispatchEvent(new w3.MouseEvent('click', { bubbles: true }));
    ok('普通浏览器：打印仍走 window.print()', prints3 === 1, 'prints=' + prints3);

    /* 窄屏（手机）预览不应再横向溢出：A4 固定宽度需在窄屏降级为流式 */
    ok('窄屏预览有响应式降级（不再固定 210mm 溢出）',
       /@media\s+screen\s+and\s+\(max-width:\s*900px\)\{[\s\S]{0,600}?\.pp-page\{[^}]*width:100%/.test(html));
  })();

  /* 1. 初始化渲染 */
  const devOpts = d.querySelectorAll('#devSel option').length;
  const matOpts = d.querySelectorAll('#matSel option').length;
  ok('设备下拉已渲染', devOpts >= 12, devOpts + ' 项');
  ok('材料下拉已渲染', matOpts >= 51, matOpts + ' 项');
  ok('设备分组存在', d.querySelectorAll('#devSel optgroup').length >= 3);
  ok('材料分组含拓竹/大简/三慈',
     /拓竹/.test(d.querySelector('#matSel').innerHTML) &&
     /大简/.test(d.querySelector('#matSel').innerHTML) &&
     /三慈/.test(d.querySelector('#matSel').innerHTML));
  ok('默认单件成本已计算', /¥\d/.test(d.getElementById('unitCost').textContent), d.getElementById('unitCost').textContent);

  /* 2. 选择预设自动填参数 */
  const devSel = d.getElementById('devSel');
  devSel.value = 'b-p1s';
  change(devSel);
  ok('选拓竹 P1S 填入设备价格 2799', field('printerPrice').value === '2799', field('printerPrice').value);
  ok('选拓竹 P1S 填入功率 280', field('power').value === '280', field('power').value);

  const matSel = d.getElementById('matSel');
  matSel.value = 'sc-pla-matte';
  change(matSel);
  ok('选三慈 PLA 哑光 填入单价 55', field('spoolPrice').value === '55', field('spoolPrice').value);
  ok('卡片标题显示预设名', /三慈 PLA 哑光/.test(d.getElementById('matPick').textContent),
     d.getElementById('matPick').textContent);

  /* 3. 改动参数 -> 标记「已修改」 */
  field('spoolPrice').value = '48';
  input(field('spoolPrice'));
  ok('改价后标题标记「已修改」', /已修改/.test(d.getElementById('matPick').textContent),
     d.getElementById('matPick').textContent);

  /* 4. 保存菜单：更新当前预设 */
  var popBtn = d.querySelector('#matPop [data-act="update"]');
  field('spoolPrice').value = '48';
  input(field('spoolPrice'));
  click(d.getElementById('matSave'));
  ok('保存菜单可打开', d.getElementById('matPop').classList.contains('open'));
  ok('更新按钮指向当前预设', /三慈 PLA 哑光/.test(popBtn.textContent), popBtn.textContent);
  click(popBtn);
  var saved = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  var rec = (saved.material || []).filter(function (x) { return x.id === 'sc-pla-matte'; })[0];
  ok('更新写入自定义存储', !!rec && rec.price === 48, JSON.stringify(rec));
  ok('更新后标题不再显示已修改', !/已修改/.test(d.getElementById('matPick').textContent),
     d.getElementById('matPick').textContent);

  /* 5. 管理弹窗：编辑内置设备预设 */
  click(d.getElementById('btnPreset'));
  ok('预设管理弹窗打开', d.getElementById('modal').classList.contains('open'));
  var tabs = d.querySelectorAll('.tab');
  click(tabs[1]);
  ok('切到材料页', d.getElementById('pane-material').classList.contains('active'));
  ok('已改内置项显示「内置 · 已改」', /内置 · 已改/.test(d.getElementById('list-material').innerHTML));
  ok('已改内置项有恢复默认按钮', !!d.querySelector('#list-material [data-revert]'));

  click(d.querySelector('#list-material [data-edit="material|sc-pla-matte"]'));
  ok('编辑表单展开', d.getElementById('form-material').classList.contains('open'));
  ok('表单提示内置将被覆盖为自定义版', /不会影响原始数据/.test(d.getElementById('form-material').innerHTML));

  var nameInput = d.querySelector('#form-material [data-pf="name"]');
  var priceInput = d.querySelector('#form-material [data-pf="price"]');
  ok('表单预填当前值', priceInput.value === '48', priceInput.value);
  priceInput.value = '52';
  click(d.querySelector('#form-material [data-save="material"]'));
  saved = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  rec = (saved.material || []).filter(function (x) { return x.id === 'sc-pla-matte'; })[0];
  ok('编辑保存生效', !!rec && rec.price === 52, JSON.stringify(rec));
  ok('表单已关闭', !d.getElementById('form-material').classList.contains('open'));

  /* 6. 恢复默认 */
  click(d.querySelector('#list-material [data-revert="material|sc-pla-matte"]'));
  saved = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  rec = (saved.material || []).filter(function (x) { return x.id === 'sc-pla-matte'; })[0];
  ok('恢复默认移除覆盖层', !rec, JSON.stringify(saved.material));
  ok('恢复后下拉不再带改标记', !/＊改/.test(d.querySelector('#matSel').innerHTML));

  /* 7. 新建自定义预设 */
  click(d.querySelector('[data-add="material"]'));
  d.querySelector('#form-material [data-pf="name"]').value = '我的神秘耗材';
  d.querySelector('#form-material [data-pf="brand"]').value = '我的材料';
  d.querySelector('#form-material [data-pf="price"]').value = '123';
  click(d.querySelector('#form-material [data-save="material"]'));
  saved = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  var mine = (saved.material || []).filter(function (x) { return x.name === '我的神秘耗材'; })[0];
  ok('新建自定义预设已保存', !!mine && mine.price === 123, JSON.stringify(mine));
  ok('新建后下拉选中该项', field('spoolPrice').value === '123', field('spoolPrice').value);
  ok('列表显示「我的」徽标', /我的/.test(d.getElementById('list-material').innerHTML));

  /* 8. 删除自定义预设 */
  var delBtn = d.querySelector('#list-material [data-del]');
  click(delBtn);
  saved = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  ok('删除自定义预设生效',
     !(saved.material || []).some(function (x) { return x.name === '我的神秘耗材'; }),
     JSON.stringify(saved.material));

  /* 9. 复制内置为我的 */
  click(tabs[0]);
  var copyBtn = d.querySelector('#list-device [data-copy]');
  click(copyBtn);
  saved = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  ok('复制内置为我的预设', (saved.device || []).length >= 1, JSON.stringify(saved.device));

  /* 10. 数据持久化与重载 */
  ok('当前参数已写入 dpc_v1', !!w.localStorage.getItem('dpc_v1'));

  /* ===== 11. 预设详情条（v5：字段即可编辑输入） ===== */
  d.getElementById('matSel').value = 'dj-pla-matte';
  change(d.getElementById('matSel'));
  var md = d.getElementById('matDetail');
  ok('材料详情条常驻显示', !!md && md.querySelector('[data-field]'));
  ok('详情条含分类名', /大简 DAJIAN/.test(md.textContent), md.textContent.trim());
  ok('主页分类为纯展示（不可点）',
     !d.getElementById('matCat').classList.contains('catlink') &&
     d.getElementById('matCat').classList.contains('catname'));
  click(d.querySelector('#modal [data-close]'));
  ok('先关闭预设管理弹窗', !d.getElementById('modal').classList.contains('open'));
  click(d.getElementById('matCat'));
  ok('点主页分类不会打开任何弹窗（仅信息展示）',
     !d.getElementById('modal').classList.contains('open') &&
     !d.getElementById('picker').classList.contains('open'));
  ok('首页单价即预设字段，选预设后回填 55', field('spoolPrice').value === '55', field('spoolPrice').value);
  ok('详情条含状态标签', /内置/.test(md.textContent));
  ok('单价输入框在详情条内', !!md.querySelector('[data-field="spoolPrice"]'));

  d.getElementById('devSel').value = 'b-p1s';
  change(d.getElementById('devSel'));
  var vd = d.getElementById('devDetail');
  ok('设备详情条常驻显示', !!vd && vd.querySelector('[data-field="power"]'));
  ok('设备详情条含价格/功率/寿命/维护标签',
     /价格/.test(vd.textContent) && /功率/.test(vd.textContent) &&
     /寿命/.test(vd.textContent) && /维护/.test(vd.textContent), vd.textContent.trim());
  ok('设备字段回填 2799/280/6000/0.35',
     field('printerPrice').value === '2799' && field('power').value === '280' &&
     field('lifeHours').value === '6000' && field('maintPerHour').value === '0.35',
     [field('printerPrice').value, field('power').value, field('lifeHours').value, field('maintPerHour').value].join('/'));
  ok('设备卡片标题显示预设名', /拓竹 P1S/.test(d.getElementById('devPick').textContent),
     d.getElementById('devPick').textContent);

  /* 首页直接改单价 -> 立即标记已修改，且「保存 ▾」可写回 */
  field('spoolPrice').value = '56';
  input(field('spoolPrice'));
  ok('首页改单价后材料标题标记「已修改」', /已修改/.test(d.getElementById('matPick').textContent),
     d.getElementById('matPick').textContent);
  ok('首页改单价后材料详情条提示写回', /写回预设/.test(d.getElementById('matDetail').textContent),
     d.getElementById('matDetail').textContent.trim());
  click(d.getElementById('matSave'));
  click(d.querySelector('#matPop [data-act="update"]'));
  var savedMat = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  var recMat = (savedMat.material || []).filter(function (x) { return x.id === 'dj-pla-matte'; })[0];
  ok('首页改的单价能被「保存 ▾」写回', !!recMat && recMat.price === 56, JSON.stringify(recMat));

  /* 设备字段同理：改首页功率 -> 写回 */
  field('power').value = '300';
  input(field('power'));
  ok('首页改功率后设备标题标记「已修改」', /已修改/.test(d.getElementById('devPick').textContent),
     d.getElementById('devPick').textContent);
  ok('改动参数后详情条提示写回', /写回预设/.test(d.getElementById('devDetail').textContent),
     d.getElementById('devDetail').textContent.trim());
  click(d.getElementById('devSave'));
  click(d.querySelector('#devPop [data-act="update"]'));
  var savedDev = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  var recDev = (savedDev.device || []).filter(function (x) { return x.id === 'b-p1s'; })[0];
  ok('首页改的功率能被「保存 ▾」写回', !!recDev && recDev.power === 300, JSON.stringify(recDev));

  /* ===== 12. 分类管理 ===== */
  var tabs2 = d.querySelectorAll('.tab');
  ok('有 3 个 tab', tabs2.length === 3, tabs2.length + ' 个');
  click(tabs2[2]);
  ok('切到分类管理页', d.getElementById('pane-category').classList.contains('active'));
  ok('设备分类已渲染', d.querySelectorAll('#catlist-device .catitem').length >= 3,
     d.querySelectorAll('#catlist-device .catitem').length + ' 个');
  ok('材料分类已渲染', d.querySelectorAll('#catlist-material .catitem').length >= 5,
     d.querySelectorAll('#catlist-material .catitem').length + ' 个');
  ok('分类显示归属预设数', /个预设/.test(d.getElementById('catlist-material').innerHTML));

  /* 新增分类 */
  d.getElementById('catInput-material').value = '树脂专区';
  click(d.querySelector('[data-catadd="material"]'));
  var cs = JSON.parse(w.localStorage.getItem('dpc_cats_v1') || '{}');
  ok('新增分类已保存', (cs.material || []).indexOf('树脂专区') >= 0, JSON.stringify(cs.material));
  ok('空分类暂不占用下拉分组', !/树脂专区/.test(d.querySelector('#matSel').innerHTML));
  ok('新增后输入框已清空', d.getElementById('catInput-material').value === '');

  /* 重命名分类 -> 预设归属同步 */
  var og3 = d.querySelector('#matSel optgroup[label="三慈"]');
  var sc3Count = og3 ? og3.querySelectorAll('option').length : 0;
  ok('重命名前下拉中三慈分组计 8 项', sc3Count === 8, sc3Count + ' 项');
  click(d.querySelector('#catlist-material [data-catrename="material|三慈"]'));
  ok('重命名输入框出现', !!d.getElementById('catRenameInput'));
  d.getElementById('catRenameInput').value = '三慈科技';
  click(d.querySelector('[data-catrenameok="material"]'));
  cs = JSON.parse(w.localStorage.getItem('dpc_cats_v1') || '{}');
  ok('分类重命名已保存', (cs.material || []).indexOf('三慈科技') >= 0, JSON.stringify(cs.material));
  ok('下拉分组已改名', /三慈科技/.test(d.querySelector('#matSel').innerHTML) &&
     !/label="三慈"/.test(d.querySelector('#matSel').innerHTML));
  var ps = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  var moved = (ps.material || []).filter(function (x) { return x.brand === '三慈科技'; });
  ok('该分类下内置预设同步改归属', moved.length === sc3Count, moved.length + ' 个');

  /* 删除分类 -> 预设归入未分类 */
  click(d.querySelector('#catlist-material [data-catdel="material|三慈科技"]'));
  cs = JSON.parse(w.localStorage.getItem('dpc_cats_v1') || '{}');
  ok('分类已删除', (cs.material || []).indexOf('三慈科技') < 0, JSON.stringify(cs.material));
  ok('自动补出「未分类」', (cs.material || []).indexOf('未分类') >= 0);
  ps = JSON.parse(w.localStorage.getItem('dpc_presets_v3') || '{}');
  var unc = (ps.material || []).filter(function (x) { return x.brand === '未分类'; });
  ok('预设归入未分类，未被删除', unc.length === sc3Count, unc.length + ' 个');
  ok('下拉出现「未分类」分组', /未分类/.test(d.querySelector('#matSel').innerHTML));

  /* 表单分类可下拉选择 */
  click(tabs2[1]);
  click(d.querySelector('[data-add="material"]'));
  var brandInput = d.querySelector('#form-material [data-pf="brand"]');
  ok('表单分类字段带 datalist', brandInput.getAttribute('list') === 'dl-material', brandInput.getAttribute('list'));
  ok('datalist 含现有分类', /树脂专区/.test(d.getElementById('dl-material').innerHTML));

  /* 表单里输入新分类名 -> 自动登记 */
  d.querySelector('#form-material [data-pf="name"]').value = '测试新分类耗材';
  brandInput.value = '我的新分类';
  d.querySelector('#form-material [data-pf="price"]').value = '77';
  click(d.querySelector('#form-material [data-save="material"]'));
  cs = JSON.parse(w.localStorage.getItem('dpc_cats_v1') || '{}');
  ok('表单新分类自动登记', (cs.material || []).indexOf('我的新分类') >= 0, JSON.stringify(cs.material));

  /* 分类数据持久化 */
  ok('分类已落盘 dpc_cats_v1', !!w.localStorage.getItem('dpc_cats_v1'));

  /* ===== 13. 两级品牌选择器 ===== */
  click(d.getElementById('matBtn'));
  ok('点选择按钮打开选择器', d.getElementById('picker').classList.contains('open'));
  ok('选择器先显示品牌列表', d.querySelectorAll('#pkBody [data-pkbrand]').length >= 5,
     d.querySelectorAll('#pkBody [data-pkbrand]').length + ' 个品牌');
  ok('品牌行显示型号数', /个型号/.test(d.getElementById('pkBody').innerHTML));
  ok('有「管理 / 新增预设」入口', !!d.querySelector('#pkBody [data-pkmanage]'));
  ok('一级不直接显示型号', d.querySelectorAll('#pkBody [data-pkmodel]').length === 0);

  click(d.querySelector('#pkBody [data-pkbrand="大简 DAJIAN"]'));
  ok('点品牌后展开该品牌型号', d.querySelectorAll('#pkBody [data-pkmodel]').length === 12,
     d.querySelectorAll('#pkBody [data-pkmodel]').length + ' 个');
  ok('标题显示所点品牌名', d.getElementById('pkTitle').textContent === '大简 DAJIAN',
     d.getElementById('pkTitle').textContent);
  ok('进入品牌后出现返回按钮', d.getElementById('pkBack').hidden === false);

  click(d.querySelector('#pkBody [data-pkmodel="dj-pla-matte"]'));
  ok('选型号后自动关闭选择器', !d.getElementById('picker').classList.contains('open'));
  ok('选型号后主页选中该预设', d.getElementById('matSel').value === 'dj-pla-matte',
     d.getElementById('matSel').value);
  ok('选型号后参数已回填（单价 56）', field('spoolPrice').value === '56', field('spoolPrice').value);

  click(d.getElementById('matBtn'));
  click(d.querySelector('#pkBody [data-pkbrand="大简 DAJIAN"]'));
  click(d.getElementById('pkBack'));
  ok('返回后回到品牌列表', d.querySelectorAll('#pkBody [data-pkbrand]').length >= 5 &&
     d.getElementById('pkBack').hidden === true);
  click(d.querySelector('#picker [data-pkclose]'));
  ok('点关闭可收起选择器', !d.getElementById('picker').classList.contains('open'));

  click(d.getElementById('devBtn'));
  ok('设备选择器可打开', d.getElementById('picker').classList.contains('open') &&
     d.getElementById('pkTitle').textContent === '选择设备');
  click(d.querySelector('#pkBody [data-pkmanage]'));
  ok('「管理 / 新增预设」跳转预设管理',
     !d.getElementById('picker').classList.contains('open') &&
     d.getElementById('modal').classList.contains('open') &&
     d.getElementById('pane-device').classList.contains('active'));
  click(d.querySelector('#modal [data-close]'));

  /* 分类管理页每个分类都有显式「重命名」按钮 */
  click(tabs2[2]);
  ok('分类项带显式「重命名」按钮',
     d.querySelectorAll('#catlist-material [data-catrename]').length >= 5 &&
     /重命名/.test(d.getElementById('catlist-material').innerHTML));
  click(d.querySelector('#catlist-material [data-catrename="material|大简 DAJIAN"]'));
  ok('点「重命名」进入改名输入', !!d.getElementById('catRenameInput'));
  click(d.querySelector('[data-catrenamecancel="material"]'));

  /* 14. 弹窗入场动画保留居中 + 预设绑定字段步进可达（修复 2799 无法回调） */
  ok('pkIn 关键帧保留居中位移',
     html.indexOf('@keyframes pkIn{ from{opacity:0; transform:translate(-50%,-50%) scale(.96)} to{opacity:1; transform:translate(-50%,-50%)} }') >= 0);
  ok('.pk-sheet 使用 pkIn 入场（不再用会丢居中的 sheetUp）',
     /\.pk-sheet\{[\s\S]{0,400}?animation:pkIn /.test(html) &&
     !/\.pk-sheet\{[\s\S]{0,400}?animation:sheetUp /.test(html));

  ['spoolPrice', 'printerPrice', 'power', 'lifeHours'].forEach(function (f) {
    var el = field(f);
    ok('字段 ' + f + ' step=any（任意值可精确到达）', !!el && el.getAttribute('step') === 'any');
  });
  ok('维护费 step=0.01（0.28 可精确到达）', field('maintPerHour').getAttribute('step') === '0.01');

  click(d.getElementById('devBtn'));
  click(d.querySelector('#pkBody [data-pkbrand="拓竹 Bambu Lab"]'));
  click(d.querySelector('#pkBody [data-pkmodel="b-p1s"]'));
  ok('选中 P1S 后价格精确回填 2799', field('printerPrice').value === '2799');
  ok('选中 P1S 后维护费精确回填 0.35', field('maintPerHour').value === '0.35');

  /* 15. 打印预览 + 导出兜底 */
  ok('存在打印预览覆盖层', !!d.getElementById('pprev') && !!d.getElementById('ppPage'));
  ok('存在导出兜底面板', !!d.getElementById('exBox') && !!d.getElementById('exText') && !!d.getElementById('exCopy'));

  click(d.getElementById('btnPrint'));
  ok('点「打印」打开预览层', d.getElementById('pprev').classList.contains('open'));
  ok('预览渲染出 A4 报价页',
     /3D 打印成本报价单/.test(d.getElementById('ppPage').innerHTML) &&
     /订单总成本/.test(d.getElementById('ppPage').innerHTML) &&
     /建议售价/.test(d.getElementById('ppPage').innerHTML));
  ok('预览页含当前单件成本数值',
     d.getElementById('ppPage').innerHTML.indexOf(d.getElementById('unitCost').textContent) >= 0);
  ok('打印模式类挂到 body', d.body.classList.contains('pp'));

  click(d.querySelector('#pprev [data-ppclose]'));
  ok('关闭预览层并移除打印模式',
     !d.getElementById('pprev').classList.contains('open') && !d.body.classList.contains('pp'));

  /* 导出：stub 掉浏览器下载 API，验证链路不抛错 */
  w.URL.createObjectURL = function () { return 'blob:test'; };
  w.URL.revokeObjectURL = function () {};
  w.HTMLAnchorElement.prototype.click = function () {};
  click(d.getElementById('btnCsv'));
  ok('点「导出 CSV」不抛错且提示已导出', /已导出 CSV/.test(d.getElementById('toast').textContent));
  ok('下载路径含嵌入式 / WebView 无桥兜底 showExport',
     /isEmbedded\(\) \|\| \(isAndroidWebView\(\) && !bridge\)\) showExport\(/.test(html));

  /* 兜底面板复制按钮（jsdom 无 clipboard，走 execCommand 降级） */
  d.getElementById('exText').value = 'demo,1,2';
  d.getElementById('exBox').classList.add('open');
  click(d.getElementById('exCopy'));
  ok('兜底面板复制按钮可用', /复制/.test(d.getElementById('toast').textContent));
  click(d.querySelector('#exBox [data-exclose]'));
  ok('兜底面板可关闭', !d.getElementById('exBox').classList.contains('open'));

  /* 16. 备份 / 恢复：全量往返 */
  ok('存在「备份全部数据」按钮', !!d.getElementById('btnBackup'));
  ok('存在「恢复备份」文件入口', !!d.getElementById('fileRestore'));
  ok('预设管理内含备份区文案', /备份与恢复/.test(d.getElementById('modal').innerHTML));

  /* 保证三类数据都存在，使往返可验证 */
  if (!w.localStorage.getItem('dpc_presets_v3')) {
    w.localStorage.setItem('dpc_presets_v3', JSON.stringify({
      device: [{ id: 't-dev-1', name: '测试设备', brand: '测试', price: 1234 }], material: []
    }));
  }
  if (!w.localStorage.getItem('dpc_cats_v1')) {
    w.localStorage.setItem('dpc_cats_v1', JSON.stringify({ init: true, device: ['测试'], material: [] }));
  }

  var bkBlob = null;
  w.URL.createObjectURL = function (b) { bkBlob = b; return 'blob:test'; };
  click(d.getElementById('btnBackup'));
  ok('点「备份全部数据」不抛错并给出提示', /已生成备份/.test(d.getElementById('toast').textContent));

  function blobText(b, cb) {
    if (!b) { cb(''); return; }
    if (typeof b.text === 'function') { b.text().then(function (x) { cb(x); }); return; }
    var fr = new w.FileReader();
    fr.onload = function () { cb(String(fr.result)); };
    fr.readAsText(b);
  }

  /* ===== 17. 检查更新（v1.1.0） ===== */
  function fakeRelease(tag) {
    return Promise.resolve({
      ok: true,
      json: function () {
        return Promise.resolve({
          tag_name: tag,
          html_url: 'https://github.com/steveliuyan/3d-print-cost-cn/releases/tag/v' + tag,
          body: '测试更新说明',
          assets: [
            { name: '3d-print-cost-1.1.0.apk', browser_download_url: 'https://github.com/x/app.apk' },
            { name: '3D打印成本计算器-1.1.0-便携版.exe', browser_download_url: 'https://github.com/x/app.exe' },
            { name: 'web.html', browser_download_url: 'https://github.com/x/web.html' }
          ]
        });
      }
    });
  }
  function runUpdateTests(done) {
    /* Android 壳：发现新版本 → 弹窗 →「立即升级」走原生桥 updateApp */
    var updCalls = [];
    var domU = new JSDOM(html, {
      runScripts: 'dangerously',
      url: 'https://appassets.androidplatform.net/assets/index.html',
      pretendToBeVisual: true,
      beforeParse: function (win) {
        win.AndroidBridge = {
          saveText: function () {}, printPage: function () { return true; },
          updateApp: function (u) { updCalls.push(u); return true; }
        };
        win.fetch = function (url) { win.__fetchUrl = url; return fakeRelease('9.9.9'); };
      }
    });
    var wU = domU.window, dU = wU.document;
    ok('更新：footer 显示当前版本号 1.4.0', dU.getElementById('footVer').textContent === '1.4.0',
       dU.getElementById('footVer').textContent);
    dU.getElementById('btnCheckUpd').dispatchEvent(new wU.MouseEvent('click', { bubbles: true }));
    setTimeout(function () {
      ok('更新：请求 GitHub releases/latest',
         /api\.github\.com\/repos\/steveliuyan\/3d-print-cost-cn\/releases\/latest/.test(wU.__fetchUrl || ''),
         wU.__fetchUrl);
      ok('更新：发现新版弹出更新弹窗', dU.getElementById('updBox').classList.contains('open'));
      ok('更新：弹窗展示新版本号', /9\.9\.9/.test(dU.getElementById('updBody').textContent));
      ok('更新：「立即升级」按钮可见', dU.getElementById('updGo').hidden === false);
      dU.getElementById('updGo').dispatchEvent(new wU.MouseEvent('click', { bubbles: true }));
      ok('更新：Android 端升级走原生桥 updateApp', updCalls.length === 1 && /app\.apk$/.test(updCalls[0] || ''),
         JSON.stringify(updCalls));
      ok('更新：点升级后弹窗关闭', !dU.getElementById('updBox').classList.contains('open'));

      /* 普通浏览器（无桥）：升级按钮跳转下载链接 */
      var opened = [];
      var domU2 = new JSDOM(html, {
        runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
        beforeParse: function (win) {
          win.fetch = function () { return fakeRelease('9.9.9'); };
          win.open = function (u) { opened.push(u); return {}; };
        }
      });
      var wU2 = domU2.window, dU2 = wU2.document;
      dU2.getElementById('btnCheckUpd').dispatchEvent(new wU2.MouseEvent('click', { bubbles: true }));
      setTimeout(function () {
        dU2.getElementById('updGo').dispatchEvent(new wU2.MouseEvent('click', { bubbles: true }));
        ok('更新：网页版升级下载 web.html（而非 APK）', opened.length === 1 && /web\.html$/.test(opened[0] || ''),
           JSON.stringify(opened));

        /* Electron 壳（UA 含 Electron）：升级下载 EXE */
        var openedE = [];
        var domU2e = new JSDOM(html, {
          runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
          beforeParse: function (win) {
            win.fetch = function () { return fakeRelease('9.9.9'); };
            win.open = function (u) { openedE.push(u); return {}; };
            Object.defineProperty(win.navigator, 'userAgent', { value: 'Mozilla/5.0 Electron/33.0 Chrome/130', configurable: true });
          }
        });
        var wU2e = domU2e.window, dU2e = wU2e.document;
        dU2e.getElementById('btnCheckUpd').dispatchEvent(new wU2e.MouseEvent('click', { bubbles: true }));
        setTimeout(function () {
          dU2e.getElementById('updGo').dispatchEvent(new wU2e.MouseEvent('click', { bubbles: true }));
          ok('更新：Electron 端升级下载 EXE', openedE.length === 1 && /app\.exe$/.test(openedE[0] || ''),
             JSON.stringify(openedE));

          /* 已是最新版本：手动检查提示最新，不出现升级按钮 */
          var domU3 = new JSDOM(html, {
            runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
            beforeParse: function (win) { win.fetch = function () { return fakeRelease('1.1.0'); }; }
          });
          var wU3 = domU3.window, dU3 = wU3.document;
          dU3.getElementById('btnCheckUpd').dispatchEvent(new wU3.MouseEvent('click', { bubbles: true }));
          setTimeout(function () {
            ok('更新：同版本提示已是最新', /已是最新版本/.test(dU3.getElementById('updBody').textContent));
            ok('更新：已是最新时不显示升级按钮', dU3.getElementById('updGo').hidden === true);

            /* 纯网页（无桥无 Electron UA）启动 3s 内不应自动联网检查 */
            var autoCalls = 0;
            var domU4 = new JSDOM(html, {
              runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
              beforeParse: function (win) { win.fetch = function () { autoCalls++; return fakeRelease('9.9.9'); }; }
            });
            setTimeout(function () {
              ok('更新：纯网页端启动不自动检查（仅壳内自动）', autoCalls === 0, 'calls=' + autoCalls);
              done();
            }, 3400);
          }, 80);
        }, 80);
      }, 80);
    }, 80);
  }

  /* ===== 18. 批量优惠 / 报价历史 / 分享长图（v1.2.0） ===== */
  function runV120Tests(done) {
    var domV = new JSDOM(html, {
      runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
      beforeParse: function (win) {
        win.confirm = function () { return true; };
        /* 画布桩：jsdom 无 canvas，注入 Proxy 2D 上下文与 toDataURL */
        function ctxProxy() {
          return new Proxy({}, {
            get: function (t, k) {
              if (k === 'measureText') return function () { return { width: 10 }; };
              if (k === 'canvas') return {};
              return function () {};
            },
            set: function () { return true; }
          });
        }
        win.HTMLCanvasElement.prototype.getContext = function () { return ctxProxy(); };
        win.HTMLCanvasElement.prototype.toDataURL = function () { return 'data:image/png;base64,QUFBQQ=='; };
        win.URL.createObjectURL = function () { return 'blob:share'; };
        win.URL.revokeObjectURL = function () {};
      }
    });
    var wV = domV.window, dV = wV.document;
    var anchors = 0;
    wV.HTMLAnchorElement.prototype.click = function () { anchors++; };

    /* 批量优惠：字段存在且参与计算（数字滚动为 rAF 动画，需等其结算） */
    ok('v1.2：存在批量优惠字段 bulkDisc', !!dV.querySelector('[data-field="bulkDisc"]'));
    ok('v1.2：footer 版本号为 1.2.0', dV.getElementById('footVer').textContent === '1.4.0');
    ok('v1.2：结果卡带「保存报价 / 报价历史 / 分享长图」三个入口',
       !!dV.getElementById('btnQuoteSave') && !!dV.getElementById('btnQuoteList') && !!dV.getElementById('btnShareImg'));
    var field2 = dV.querySelector('[data-field="qty"]');
    field2.value = '10';
    input(field2);
    var bd = dV.querySelector('[data-field="bulkDisc"]');
    bd.value = '10';
    input(bd);
    setTimeout(function () {
      var revNum = parseFloat(dV.getElementById('totalRevenue').textContent.replace(/[^0-9.]/g, ''));
      var sellNum = parseFloat(dV.getElementById('sellPrice').textContent.replace(/[^0-9.]/g, ''));
      ok('v1.2：批量优惠 10% 后订单收入降为九折', /批量优惠 10%/.test(dV.getElementById('tbody').innerHTML) &&
         Math.abs(revNum / sellNum - 9) < 0.02, 'rev=' + revNum + ' sell=' + sellNum + ' 比=' + (revNum / sellNum).toFixed(3));

      /* 报价历史：保存 -> 列表 -> 载入 -> 删除 */
      click(dV.getElementById('btnQuoteSave'));
      var qs = JSON.parse(wV.localStorage.getItem('dpc_quotes_v1') || '[]');
      ok('v1.2：保存报价写入 dpc_quotes_v1', qs.length === 1 && qs[0].qty === 10 && qs[0].disc === 0.1,
         JSON.stringify(qs[0] || {}).slice(0, 80));
      ok('v1.2：报价快照包含参数字段', !!(qs[0] && qs[0].fields && qs[0].fields.spoolPrice));
      click(dV.getElementById('btnQuoteList'));
      ok('v1.2：历史列表打开并渲染 1 条', dV.getElementById('histBox').classList.contains('open') &&
         dV.querySelectorAll('#histList .hist-item').length === 1);
      ok('v1.2：历史行含设备材料与金额', /件/.test(dV.getElementById('histList').textContent) &&
         /¥/.test(dV.getElementById('histList').textContent));
      dV.querySelector('[data-field="spoolPrice"]').value = '999';
      input(dV.querySelector('[data-field="spoolPrice"]'));
      click(dV.querySelector('#histList [data-qload]'));
      ok('v1.2：载入历史把参数填回（单价恢复快照值 65）',
         dV.querySelector('[data-field="spoolPrice"]').value === '65' &&
         !dV.getElementById('histBox').classList.contains('open'));
      click(dV.getElementById('btnQuoteList'));
      click(dV.querySelector('#histList [data-qdel]'));
      ok('v1.2：删除历史生效', (JSON.parse(wV.localStorage.getItem('dpc_quotes_v1')) || []).length === 0);
      ok('v1.2：清空按钮随列表隐藏', dV.getElementById('histClear').hidden === true);
      runShareTests(done);
    }, 700);
  }

  /* 分享长图：生成 -> 预览 -> Android 桥保存 / 浏览器下载 */
  function runShareTests(done) {
    var bitmapCalls = [];
    var domV2 = new JSDOM(html, {
      runScripts: 'dangerously',
      url: 'https://appassets.androidplatform.net/assets/index.html',
      pretendToBeVisual: true,
      beforeParse: function (win) {
        win.AndroidBridge = {
          saveText: function () { return true; },
          printPage: function () { return true; },
          saveBitmap: function (n, b) { bitmapCalls.push({ n: n, b: b }); return true; },
          updateApp: function () { return true; }
        };
        win.confirm = function () { return true; };
        function ctxProxy() {
          return new Proxy({}, {
            get: function (t, k) {
              if (k === 'measureText') return function () { return { width: 10 }; };
              return function () {};
            },
            set: function () { return true; }
          });
        }
        win.HTMLCanvasElement.prototype.getContext = function () { return ctxProxy(); };
        win.HTMLCanvasElement.prototype.toDataURL = function () { return 'data:image/png;base64,QUFBQQ=='; };
        win.URL.createObjectURL = function () { return 'blob:share'; };
        win.URL.revokeObjectURL = function () {};
      }
    });
    var wV2 = domV2.window, dV2 = wV2.document;
    dV2.getElementById('btnShareImg').dispatchEvent(new wV2.MouseEvent('click', { bubbles: true }));
    ok('v1.2：生成长图后打开预览层', dV2.getElementById('shareBox').classList.contains('open'));
    ok('v1.2：预览 img 为 PNG dataURL', /^data:image\/png;base64,/.test(dV2.getElementById('shareImg').src || ''));
    dV2.getElementById('shareSave').dispatchEvent(new wV2.MouseEvent('click', { bubbles: true }));
    ok('v1.2：Android 端保存走原生桥 saveBitmap（写相册）',
       bitmapCalls.length === 1 && /报价单.*\.png$/.test(bitmapCalls[0].n || ''), JSON.stringify(bitmapCalls));
    dV2.getElementById('btnShareImg').dispatchEvent(new wV2.MouseEvent('click', { bubbles: true }));
    dV2.getElementById('shareSave').dispatchEvent(new wV2.MouseEvent('click', { bubbles: true }));
    ok('v1.2：保存后预览层仍可复用（可连续生成）', dV2.getElementById('shareBox').classList.contains('open'));

    /* 无桥浏览器：保存走 a download */
    var domV3 = new JSDOM(html, {
      runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
      beforeParse: function (win) {
        win.confirm = function () { return true; };
        function ctxProxy() {
          return new Proxy({}, {
            get: function (t, k) {
              if (k === 'measureText') return function () { return { width: 10 }; };
              return function () {};
            },
            set: function () { return true; }
          });
        }
        win.HTMLCanvasElement.prototype.getContext = function () { return ctxProxy(); };
        win.HTMLCanvasElement.prototype.toDataURL = function () { return 'data:image/png;base64,QUFBQQ=='; };
        win.URL.createObjectURL = function (b) { shareBlob = b; return 'blob:share'; };
        win.URL.revokeObjectURL = function () {};
        win.atob = function (s) { return Buffer.from(s, 'base64').toString('binary'); };
        win.HTMLAnchorElement.prototype.click = function () {};
      }
    });
    var wV3 = domV3.window, dV3 = wV3.document, shareBlob = null;
    dV3.getElementById('btnShareImg').dispatchEvent(new wV3.MouseEvent('click', { bubbles: true }));
    dV3.getElementById('shareSave').dispatchEvent(new wV3.MouseEvent('click', { bubbles: true }));
    setTimeout(function () {
      ok('v1.2：无桥环境保存为 PNG Blob 下载', !!shareBlob && shareBlob.type === 'image/png',
         shareBlob && shareBlob.type);
      done();
    }, 60);
  }

  /* ===== 19. STL 导入估算（v1.3.0） ===== */
  function cubeBinaryStl(s) {
    var tris = [
      [[0,0,s],[0,s,s],[s,s,s]], [[0,0,s],[s,s,s],[s,0,s]],
      [[0,0,0],[s,0,0],[s,s,0]], [[0,0,0],[s,s,0],[0,s,0]],
      [[0,s,0],[s,s,0],[s,s,s]], [[0,s,0],[s,s,s],[0,s,s]],
      [[s,0,0],[0,0,0],[0,0,s]], [[s,0,0],[0,0,s],[s,0,s]],
      [[0,0,0],[0,s,0],[0,s,s]], [[0,0,0],[0,s,s],[0,0,s]],
      [[s,s,0],[s,0,0],[s,0,s]], [[s,s,0],[s,0,s],[s,s,s]]
    ];
    var buf = new ArrayBuffer(84 + tris.length * 50);
    var dv = new DataView(buf);
    dv.setUint32(80, tris.length, true);
    tris.forEach(function (t, i) {
      var o = 84 + i * 50 + 12; /* 跳过法线 */
      t.forEach(function (v) { dv.setFloat32(o, v[0], true); dv.setFloat32(o + 4, v[1], true); dv.setFloat32(o + 8, v[2], true); o += 12; });
    });
    return buf;
  }
  function tetraAsciiStl() {
    var f = [
      [[0,0,0],[0,0,10],[0,10,0]], [[0,0,0],[10,0,0],[0,0,10]],
      [[0,0,0],[0,10,0],[10,0,0]], [[10,0,0],[0,10,0],[0,0,10]]
    ];
    var s = 'solid t\n';
    f.forEach(function (t) {
      s += ' facet normal 0 0 0\n  outer loop\n';
      t.forEach(function (v) { s += '   vertex ' + v[0] + ' ' + v[1] + ' ' + v[2] + '\n'; });
      s += '  endloop\n endfacet\n';
    });
    return s + 'endsolid t\n';
  }
  function runStlTests(done) {
    var domS = new JSDOM(html, {
      runScripts: 'dangerously', url: 'http://localhost/', pretendToBeVisual: true,
      beforeParse: function (win) { win.confirm = function () { return true; }; }
    });
    var wS = domS.window, dS = wS.document;
    var bin = new wS.File([cubeBinaryStl(20)], 'cube.stl', { type: '' });
    var inp = dS.getElementById('stlFile');
    try { Object.defineProperty(inp, 'files', { value: [bin], configurable: true }); } catch (e) {}
    inp.dispatchEvent(new wS.Event('change', { bubbles: true }));
    setTimeout(function () {
      var info = dS.getElementById('stlInfo').textContent;
      ok('v1.3：二进制 STL 解析出体积 8.00 cm³', /8\.00/.test(info), info);
      ok('v1.3：显示包围盒 20 × 20 × 20', /20\s*×\s*20\s*×\s*20/.test(info), info);
      ok('v1.3：PLA + 20% 填充估算 3.97 克', /3\.97/.test(info), info);
      dS.getElementById('stlFill').dispatchEvent(new wS.MouseEvent('click', { bubbles: true }));
      ok('v1.3：「填入用量」把 3.97 写进 grams', dS.querySelector('[data-field="grams"]').value === '3.97',
         dS.querySelector('[data-field="grams"]').value);
      /* 换 ABS 密度重算 */
      var sel = dS.getElementById('matDensity');
      sel.value = '1.04';
      sel.dispatchEvent(new wS.Event('change', { bubbles: true }));
      ok('v1.3：切 ABS 后估算变 3.33 克', /3\.33/.test(dS.getElementById('stlInfo').textContent),
         dS.getElementById('stlInfo').textContent);
      /* ASCII STL：四面体 166.67 mm³ → 0.17 cm³（切回 PLA 密度） */
      sel.value = '1.24';
      sel.dispatchEvent(new wS.Event('change', { bubbles: true }));
      var asc = new wS.File([tetraAsciiStl()], 'tetra.stl', { type: '' });
      try { Object.defineProperty(inp, 'files', { value: [asc], configurable: true }); } catch (e) {}
      inp.dispatchEvent(new wS.Event('change', { bubbles: true }));
      setTimeout(function () {
        var info2 = dS.getElementById('stlInfo').textContent;
        ok('v1.3：ASCII STL 解析出 0.17 cm³', /0\.17/.test(info2), info2);

        /* ===== v1.4.0：3MF 导入（Stored ZIP + XML mesh） ===== */
        function zipStore(name, bytes) {
          var n = bytes.length, nameLen = name.length;
          var lfh = 30 + nameLen + n, cdh = 46 + nameLen, total = lfh + cdh + 22;
          var buf = new ArrayBuffer(total), dv = new DataView(buf), u8 = new Uint8Array(buf);
          var o = 0;
          dv.setUint32(o, 0x04034b50, true); dv.setUint16(o + 4, 20, true); dv.setUint16(o + 8, 0, true);
          dv.setUint16(o + 10, 0, true); dv.setUint32(o + 14, 0, true);
          dv.setUint32(o + 18, n, true); dv.setUint32(o + 22, n, true);
          dv.setUint16(o + 26, nameLen, true); dv.setUint16(o + 28, 0, true);
          for (var i = 0; i < nameLen; i++) u8[o + 30 + i] = name.charCodeAt(i);
          u8.set(bytes, o + 30 + nameLen);
          var cdOff = o = lfh;
          dv.setUint32(o, 0x02014b50, true); dv.setUint16(o + 4, 20, true); dv.setUint16(o + 6, 20, true);
          dv.setUint16(o + 8, 0, true); dv.setUint16(o + 10, 0, true);
          dv.setUint32(o + 16, n, true); dv.setUint32(o + 20, n, true);
          dv.setUint32(o + 24, n, true); dv.setUint16(o + 28, nameLen, true);
          dv.setUint32(o + 42, 0, true);
          for (var j = 0; j < nameLen; j++) u8[o + 46 + j] = name.charCodeAt(j);
          o += cdh;
          dv.setUint32(o, 0x06054b50, true); dv.setUint16(o + 8, 1, true); dv.setUint16(o + 10, 1, true);
          dv.setUint32(o + 12, cdh, true); dv.setUint32(o + 16, cdOff, true);
          return buf;
        }
        function cube3mfBytes(s) {
          var V = [[0,0,0],[s,0,0],[s,s,0],[0,s,0],[0,0,s],[s,0,s],[s,s,s],[0,s,s]];
          var T = [[4,7,6],[4,6,5],[0,1,2],[0,2,3],[3,2,6],[3,6,7],[1,0,4],[1,4,5],[0,3,7],[0,7,4],[2,1,5],[2,5,6]];
          var x = '<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model"><mesh><vertices>';
          V.forEach(function (v) { x += '<vertex x="' + v[0] + '" y="' + v[1] + '" z="' + v[2] + '"/>'; });
          x += '</vertices><triangles>';
          T.forEach(function (t) { x += '<triangle v1="' + t[0] + '" v2="' + t[1] + '" v3="' + t[2] + '"/>'; });
          x += '</triangles></mesh></object></resources><build><item objectid="1"/></build></model>';
          var b = new Uint8Array(x.length);
          for (var i = 0; i < x.length; i++) b[i] = x.charCodeAt(i);
          return zipStore('3D/3dmodel.model', b);
        }
        var f3 = new wS.File([cube3mfBytes(20)], 'cube.3mf', { type: '' });
        try { Object.defineProperty(inp, 'files', { value: [f3], configurable: true }); } catch (e) {}
        inp.dispatchEvent(new wS.Event('change', { bubbles: true }));
        setTimeout(function () {
          var info3 = dS.getElementById('stlInfo').textContent;
          ok('v1.4：3MF 解析出 8.00 cm³', /8\.00/.test(info3), info3);
          ok('v1.4：3MF 估算 3.97 克（PLA 20% 填充）', /3\.97/.test(info3), info3);
          done();
        }, 400);
      }, 120);
    }, 120);
  }

  function finish() {
    console.log(out.join('\n'));
    console.log('\n结果: ' + out.filter(function (x) { return x.indexOf('PASS') === 0; }).length + '/' + out.length + ' 通过');
  }

  try { Object.defineProperty(w.location, 'reload', { value: function () { w.__reloaded = true; }, configurable: true }); } catch (e) {}

  blobText(bkBlob, function (txt) {
    var bj = null;
    try { bj = JSON.parse(txt); } catch (e) {}
    ok('备份是合法 JSON 且带 dpc-backup 标识', !!bj && bj.type === 'dpc-backup');
    ok('备份含参数快照', !!(bj && bj.data && bj.data.params && bj.data.params.f));
    ok('备份含预设与分类', !!(bj && bj.data && bj.data.presets && bj.data.cats));
    if (!bj || !bj.data) { finish(); return; }

    /* 清空本机数据，模拟「换机 / 误删」 */
    try {
      w.localStorage.removeItem('dpc_v1');
      w.localStorage.removeItem('dpc_presets_v3');
      w.localStorage.removeItem('dpc_cats_v1');
    } catch (e) {}
    ok('清空后 localStorage 已无参数', !w.localStorage.getItem('dpc_v1'));

    var f = new w.File([txt], 'backup.json', { type: 'application/json' });
    var inp = d.getElementById('fileRestore');
    try { Object.defineProperty(inp, 'files', { value: [f], configurable: true }); } catch (e) {}
    inp.dispatchEvent(new w.Event('change', { bubbles: true }));

    setTimeout(function () {
      ok('恢复后参数写回 localStorage', !!w.localStorage.getItem('dpc_v1'));
      ok('恢复后预设写回 localStorage', !!w.localStorage.getItem('dpc_presets_v3'));
      ok('恢复后分类写回 localStorage', !!w.localStorage.getItem('dpc_cats_v1'));
      ok('参数与备份逐字节一致',
         w.localStorage.getItem('dpc_v1') === JSON.stringify(bj.data.params));
      ok('预设与备份逐字节一致',
         w.localStorage.getItem('dpc_presets_v3') === JSON.stringify(bj.data.presets));
      ok('分类与备份逐字节一致',
         w.localStorage.getItem('dpc_cats_v1') === JSON.stringify(bj.data.cats));
      runUpdateTests(function () { runV120Tests(function () { runStlTests(finish); }); });
    }, 900);
  });
}, 300);
