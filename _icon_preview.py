#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""_icon_preview.py —— 生成「应用图标已接入」的自包含预览页 + 资产对照图。

产物：
  _icon_ai/final/apply-preview.html   在上下文里看效果（顶栏 / 打印抬头 / 各尺寸 / 掩码安全区）
  docs/brand/icon-preview.png         资产对照图（尺寸行 + 平台行）
所有位图以内联 data-URI 嵌入，预览页单文件可离线打开。
"""
import base64
import io
import os
from PIL import Image, ImageDraw
import _gen_icons as G

ROOT = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(ROOT, "docs", "brand", "icon-master-rounded.png")
B = os.path.join(ROOT, "docs", "brand", "icon-master-bleed.png")
OUT_HTML = os.path.join(ROOT, "_icon_ai", "final", "apply-preview.html")
OUT_PNG = os.path.join(ROOT, "docs", "brand", "icon-preview.png")


def rd(p):
    return Image.open(p).convert("RGBA")


def uri(img, size=None):
    if size:
        img = img.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def square(img, s):
    return img.resize((s, s), Image.LANCZOS)


def circle(img, s):
    im = img.resize((s, s), Image.LANCZOS)
    m = Image.new("L", (s * 4, s * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, s * 4 - 1, s * 4 - 1], fill=255)
    im.putalpha(m.resize((s, s), Image.LANCZOS))
    return im


def sheet():
    rounded, bleed = rd(R), rd(B)
    pad, gap, cell = 24, 16, 200
    sizes = [512, 256, 128, 96, 64, 48, 32, 16]
    W = pad * 2 + len(sizes) * cell + (len(sizes) - 1) * gap
    H = pad * 3 + cell * 2 + 30
    sh = Image.new("RGBA", (W, H), (244, 245, 248, 255))
    d = ImageDraw.Draw(sh)
    for i, s in enumerate(sizes):
        im = square(rounded, min(s, cell - 20))
        x = pad + i * (cell + gap) + (cell - im.width) // 2
        y = pad + (cell - im.height) // 2
        d.rectangle([x - 6, y - 6, x + im.width + 6, y + im.height + 6], outline=(214, 218, 226, 255))
        sh.alpha_composite(im, (x, y))
    y2 = pad * 2 + cell + 30
    row = [("maskable (safe)", G.edge_extend(bleed, 180, G.MASKABLE_FRAC)), ("android round", circle(bleed, 180)),
           ("apple-touch", square(bleed, 180)), ("favicon (rounded)", square(rounded, 180))]
    for i, (_, im) in enumerate(row):
        x = pad + i * (cell + gap) + (cell - im.width) // 2
        sh.alpha_composite(im, (x, y2))
    sh.convert("RGB").save(OUT_PNG)
    print("  docs/brand/icon-preview.png  %d B" % os.path.getsize(OUT_PNG))


def safe_zone_check(bleed):
    """自适应前景（已缩入安全区）叠加 72/108 安全圆，确认内容不越线。"""
    base = G.edge_extend(bleed, 432, G.ADAPTIVE_FRAC)
    d = ImageDraw.Draw(base, "RGBA")
    r = int(432 * 72 / 108 / 2)
    c = 216
    d.ellipse([c - r, c - r, c + r, c + r], outline=(255, 60, 60, 235), width=6)
    return uri(base, 216)


def main():
    rounded, bleed = rd(R), rd(B)
    sheet()
    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>应用图标接入预览</title>
<style>
  :root{--ink:#14161a;--t2:#5c6472;--line:#e7e9ee;--accent:#4f46e5;--bg:#f5f6f8}
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 -apple-system,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif}
  .wrap{max-width:940px;margin:0 auto;padding:28px 20px 60px}
  h1{font-size:19px;margin:0 0 4px;letter-spacing:-.02em}
  .sub{color:var(--t2);margin:0 0 22px}
  h2{font-size:14px;margin:26px 0 10px;color:#2b2f38}
  .card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px}
  /* 顶栏模拟 */
  .topbar{display:flex;align-items:center;gap:12px}
  .mark{width:38px;height:38px;border-radius:11px;flex:none;display:grid;place-items:center;box-shadow:0 10px 26px -12px rgba(79,70,229,.55)}
  .mark img{width:38px;height:38px;display:block;border-radius:11px}
  .tb-title b{display:block;font-size:14.5px;font-weight:700;letter-spacing:-.015em}
  .tb-title span{display:block;font-size:11px;color:var(--t2)}
  /* 打印抬头 */
  .pp-brand{display:flex;align-items:center;gap:10px}
  .pp-brand img{width:40px;height:40px;flex:none;display:block;border-radius:11px}
  .pp-brand .bn b{display:block;font-size:14.5px;font-weight:700;color:#14161c}
  .pp-brand .bn span{display:block;font-size:10.5px;color:#6b7280}
  .pp-rule{height:2px;background:var(--accent);margin-top:12px;border-radius:2px}
  /* 尺寸行 */
  .sizes{display:flex;align-items:flex-end;gap:22px;flex-wrap:wrap}
  .sizes figure{margin:0;text-align:center}
  .sizes img{display:block;box-shadow:0 1px 3px rgba(0,0,0,.12);border-radius:22%}
  .sizes figcaption{margin-top:6px;font-size:10.5px;color:var(--t2)}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
  .chk{background:conic-gradient(#e9ecf1 0 25%,#fff 0 50%,#e9ecf1 0 75%,#fff 0) 0 0/18px 18px;border-radius:12px;padding:14px;text-align:center}
  .chk img{border-radius:8px}
  .note{font-size:12px;color:var(--t2);margin-top:8px}
  code{background:#eef0f5;padding:1px 5px;border-radius:5px;font-size:12px}
</style></head><body><div class="wrap">
  <h1>应用图标 · 接入预览</h1>
  <p class="sub">母版：<code>docs/brand/icon-master-rounded.png</code> / <code>icon-master-bleed.png</code>（单一来源）。圆角母版用于自带圆角处，全出血母版用于由系统遮罩处。</p>

  <h2>① 顶栏 .mark（原 38px 靛蓝底 + 白立方体 → 改为位图母版 <code>&lt;img&gt;</code>）</h2>
  <div class="card"><div class="topbar">
    <span class="mark"><img src="__TOPBAR__" alt="" width="38" height="38"></span>
    <div class="tb-title"><b>3D 打印成本计算器</b><span>离线单文件报价工具</span></div>
  </div></div>

  <h2>② 打印抬头 / 分享长图（BRAND_HTML → 位图 <code>&lt;img&gt;</code>；canvas 优先画位图，未就绪回退矢量）</h2>
  <div class="card"><div class="pp-brand">
    <img src="__PRINT__" alt="" width="40" height="40">
    <div class="bn"><b>3D 打印成本计算器</b><span>报价单 · 2026-10-12</span></div>
  </div><div class="pp-rule"></div></div>

  <h2>③ 启动图标各尺寸（自带圆角母版）</h2>
  <div class="card"><div class="sizes" id="sz"></div></div>

  <h2>④ 平台形态 &amp; Android 掩码安全区自检</h2>
  <div class="grid2">
    <div class="card"><div class="chk"><img src="__ROUND__" width="112" height="112" style="border-radius:50%"></div>
      <div class="note">Android <code>ic_launcher_round</code>（圆形裁切自全出血母版）</div></div>
    <div class="card"><div class="chk"><img src="__SAFE__" width="112" height="112"></div>
      <div class="note">自适应前景自检：红线 = 72/108 安全圆。内容若越线，圆形遮罩会切到边缘。</div></div>
  </div>
  <div class="grid2" style="margin-top:16px">
    <div class="card"><div class="chk"><img src="__MASK__" width="112" height="112" style="border-radius:50%"></div>
      <div class="note">maskable-512（Chrome 圆形遮罩）</div></div>
    <div class="card"><div class="chk"><img src="__APPLE__" width="112" height="112" style="border-radius:24%"></div>
      <div class="note">apple-touch（iOS 自行 squircle，故用全出血母版避免双圆角）</div></div>
  </div>
</div>
<script>
var R="__RUR__",B="__BLEED__";
var sizes=[512,256,192,180,128,96,64,48,32,16],el=document.getElementById('sz');
sizes.forEach(function(s){if(s>192&&s!==512)return;if(s===512)return;var f=document.createElement('figure');
 f.innerHTML='<img src="'+R+'" width="'+Math.min(s,128)+'" height="'+Math.min(s,128)+'"><figcaption>'+s+'px</figcaption>';el.appendChild(f);});
</script>
</body></html>"""
    html = (html.replace("__TOPBAR__", uri(rounded, 96))
                .replace("__PRINT__", uri(rounded, 192))
                .replace("__ROUND__", uri(circle(bleed, 224), 112))
                .replace("__SAFE__", safe_zone_check(bleed))
                .replace("__MASK__", uri(G.edge_extend(bleed, 224, G.MASKABLE_FRAC), 112))
                .replace("__APPLE__", uri(square(bleed, 224), 112))
                .replace("__RUR__", uri(rounded, 128))
                .replace("__BLEED__", uri(bleed, 128)))
    os.makedirs(os.path.dirname(OUT_HTML), exist_ok=True)
    with open(OUT_HTML, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("  _icon_ai/final/apply-preview.html  %d B" % os.path.getsize(OUT_HTML))


if __name__ == "__main__":
    main()
