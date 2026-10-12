#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_gen_icons.py —— 从 AI 位图母版生成三端全套图标（可复现，单一来源）

v1.8.1 起：品牌图标由「手绘矢量」改为「AI 高清位图母版 → 下采样」。
唯一来源（提交入库，勿手改其它产物）：

  docs/brand/icon-master-rounded.png   圆角方形、四角透明 —— 用于「自带圆角」的目标
  docs/brand/icon-master-bleed.png     全出血方形（四角已补满）—— 用于「由系统遮罩」的目标

谁用哪张母版（关键，别搞反）：

  自带圆角 (rounded 母版)：favicon 内联 / icon-192 / icon-512 / favicon.ico /
                           顶栏 .mark / 打印抬头 / Windows icon.png+ico
  系统遮罩 (bleed 母版)：  apple-touch（iOS 自行切圆角，预切会「双圆角」）/
                           maskable-512 / Android mipmap + 自适应前景

产物：
  根目录      icon-192.png / icon-512.png / maskable-512.png
              apple-touch-icon.png / apple-touch-icon-167.png / favicon.ico / favicon.svg
  desktop     build/icon.png(512) / build/icon.ico(16..256)
  android     res/mipmap-*/ic_launcher.png (+_round) / res/drawable/ic_launcher_foreground.png
              res/values/ic_launcher_background.xml / res/mipmap-anydpi-v26/ic_launcher.xml (+_round)
  docs/brand  icon-master-{rounded,bleed}.png（若缺则从 _icon_ai/final 导入）
  index.html  内联 favicon data-URI + 顶栏 .mark <img> + 打印抬头 BRAND_HTML（自动同步）

用法：python _gen_icons.py
"""
import base64
import io
import os
import re
import shutil
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
BRAND = os.path.join(ROOT, "docs", "brand")
MASTER_ROUND = os.path.join(BRAND, "icon-master-rounded.png")
MASTER_BLEED = os.path.join(BRAND, "icon-master-bleed.png")
SRC_ROUND = os.path.join(ROOT, "_icon_ai", "final", "icon-rounded-1892.png")
SRC_BLEED = os.path.join(ROOT, "_icon_ai", "final", "icon-bleed-1892.png")
MASTER_SIZE = 1024
THEME = "#4f46e5"
ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

# 内联进 index.html 的尺寸（px）：按实际显示尺寸 ×2 取（顶栏 38 / 打印 40）
FAVICON_INLINE = 48
TOPBAR_INLINE = 76
PRINT_INLINE = 128


# ---------------- 母版 ----------------
def ensure_masters():
    """确保 docs/brand 下存在两张 1024 母版（缺则从 _icon_ai/final 的 1892 版导入）。"""
    os.makedirs(BRAND, exist_ok=True)
    for dst, src in ((MASTER_ROUND, SRC_ROUND), (MASTER_BLEED, SRC_BLEED)):
        if not os.path.exists(dst):
            if not os.path.exists(src):
                raise SystemExit("缺少母版来源：" + src)
            im = Image.open(src).convert("RGBA").resize((MASTER_SIZE, MASTER_SIZE), Image.LANCZOS)
            im.save(dst, "PNG")
            print("  导入母版 %s" % os.path.relpath(dst, ROOT))


def load(which):
    return Image.open(MASTER_ROUND if which == "rounded" else MASTER_BLEED).convert("RGBA")


def square(img, size):
    return img.resize((size, size), Image.LANCZOS)


def circular(img, size):
    im = img.resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size * 4 - 1, size * 4 - 1], fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    out = im.copy()
    out.putalpha(m)
    return out


def edge_extend(img, size, frac, inset=0.06):
    """安全区版本：把图标缩到 canvas 的 frac 占比居中，四周用「内缩边」颜色向外拉伸填满。

    用于 maskable / Android 自适应前景 —— 让重要内容落在安全区（80% / 66.7%）之内，
    同时保证整幅无透明（掩码裁到边缘也是干净的渐变底）。
    inset 用于避开图标最外圈的高光/抗锯齿，取更靠内的底色来延伸。
    """
    t = int(round(size * frac))
    off = (size - t) // 2
    k = max(1, int(t * inset))
    tile = img.resize((t, t), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size))
    canvas.paste(tile, (off, off))
    top = tile.crop((0, k, t, k + 1)).resize((t, off), Image.LANCZOS)
    bot = tile.crop((0, t - 1 - k, t, t - k)).resize((t, size - off - t), Image.LANCZOS)
    left = tile.crop((k, 0, k + 1, t)).resize((off, t), Image.LANCZOS)
    right = tile.crop((t - 1 - k, 0, t - k, t)).resize((size - off - t, t), Image.LANCZOS)
    canvas.paste(top, (off, 0))
    canvas.paste(bot, (off, off + t))
    canvas.paste(left, (0, off))
    canvas.paste(right, (off + t, off))
    for (cx, cy, px, py) in ((0, 0, k, k), (size - off, 0, t - 1 - k, k),
                             (0, size - off, k, t - 1 - k), (size - off, size - off, t - 1 - k, t - 1 - k)):
        canvas.paste(tile.crop((px, py, px + 1, py + 1)).resize((off, off), Image.LANCZOS), (cx, cy))
    # 柔化外扩接缝：整幅高斯模糊后把锐利图标贴回中心
    soft = canvas.filter(ImageFilter.GaussianBlur(max(1.2, off * 0.6)))
    soft.paste(tile, (off, off))
    return soft


MASKABLE_FRAC = 0.72   # maskable 安全区 = 直径 80% 圆；内容含对角线，故取 0.72
ADAPTIVE_FRAC = 0.72   # 自适应可见窗口 = 中央 72/108；内容含对角线，故取 0.72


def png_bytes(img, size=None):
    if size:
        img = square(img, size)
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def data_uri(img, size=None):
    return "data:image/png;base64," + base64.b64encode(png_bytes(img, size)).decode("ascii")


def save_png(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")
    print("  %-56s %6d B" % (os.path.relpath(path, ROOT), os.path.getsize(path)))


def save_ico(img, path, size=256):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    square(img, size).save(path, "ICO", sizes=ICO_SIZES)
    print("  %-56s %6d B" % (os.path.relpath(path, ROOT), os.path.getsize(path)))


# ---------------- index.html 同步 ----------------
def _read_html():
    p = os.path.join(ROOT, "index.html")
    with open(p, encoding="utf-8", newline="") as f:
        return p, f.read()


def _write_html(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def sync_favicon_uri():
    """内联 favicon → 圆角母版的 PNG data-URI（单文件离线，浏览器标签页仍可用）。"""
    uri = data_uri(load("rounded"), FAVICON_INLINE)
    p, s = _read_html()
    pat = re.compile(r'<link rel="icon" href="data:[^"]*"[^>]*>')
    new = '<link rel="icon" href="%s">' % uri
    if not pat.search(s):
        print("  [warn] index.html 未找到内联 favicon link，跳过")
        return
    s2 = pat.sub(lambda m: new, s, count=1)
    _write_html(p, s2) if s2 != s else None
    print("  index.html 内联 favicon %s" % ("已更新" if s2 != s else "已是最新"))


def sync_topbar_mark():
    """顶栏 .mark 的内联 svg → 圆角母版 <img>。"""
    uri = data_uri(load("rounded"), TOPBAR_INLINE)
    p, s = _read_html()
    img = ('<img class="mark-img" src="%s" alt="" width="38" height="38" decoding="async">' % uri)
    pat = re.compile(r'(<span class="mark"[^>]*>)[\s\S]*?(</span>)')
    if not pat.search(s):
        print("  [warn] index.html 未找到顶栏 .mark，跳过")
        return
    s2 = pat.sub(lambda m: m.group(1) + img + m.group(2), s, count=1)
    _write_html(p, s2) if s2 != s else None
    print("  index.html 顶栏标识 %s" % ("已更新" if s2 != s else "已是最新"))


def sync_brand_html():
    """打印抬头 JS：var BRAND_SVG=<svg…> → var BRAND_ICON_URI + var BRAND_HTML=<img…>（含引用改名）。"""
    uri = data_uri(load("rounded"), PRINT_INLINE)
    p, s = _read_html()
    blob = ('  var BRAND_ICON_URI = "%s";\n'
            '  var BRAND_HTML = \'<img class="pp-brand-mark" src="\' + BRAND_ICON_URI + \'" alt="" width="40" height="40" decoding="async">\';\n'
            % uri)
    pat = re.compile(r'(?:  var BRAND_ICON_URI\s*=\s*"[^"]*";\n)?'
                     r'  var BRAND_(?:SVG|HTML)\s*=[\s\S]*?(?:"</svg>";|\';)\n')
    if not pat.search(s):
        print("  [warn] index.html 未找到 var BRAND_SVG / BRAND_HTML 定义块，跳过")
        return
    s2 = pat.sub(blob, s, count=1)
    s2 = s2.replace("'<div class=\"pp-brand\">' + BRAND_SVG +", "'<div class=\"pp-brand\">' + BRAND_HTML +")
    s2 = s2.replace("BRAND_SVG: BRAND_SVG, drawBrandMark: drawBrandMark",
                    "BRAND_HTML: BRAND_HTML, BRAND_ICON_URI: BRAND_ICON_URI, drawBrandMark: drawBrandMark")
    s2 = s2.replace("BRAND_HTML: BRAND_HTML, drawBrandMark: drawBrandMark",
                    "BRAND_HTML: BRAND_HTML, BRAND_ICON_URI: BRAND_ICON_URI, drawBrandMark: drawBrandMark")
    _write_html(p, s2) if s2 != s else None
    print("  index.html 打印抬头 BRAND_HTML %s" % ("已更新" if s2 != s else "已是最新"))


def write_favicon_svg():
    """favicon.svg：内嵌 PNG 的 SVG 包装（现代浏览器仍可作 SVG favicon 引用）。"""
    uri = data_uri(load("rounded"), 64)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
           'role="img" aria-label="3D 打印成本计算器">\n'
           '  <title>3D 打印成本计算器 · 应用图标</title>\n'
           '  <image width="64" height="64" href="%s"/>\n'
           '</svg>\n') % uri
    with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(svg)
    print("  favicon.svg")


# ---------------- 主流程 ----------------
def main():
    print("[0/7] 母版")
    ensure_masters()
    rounded, bleed = load("rounded"), load("bleed")

    print("[1/7] 规范源 / 内联同步")
    write_favicon_svg()
    sync_favicon_uri()
    sync_topbar_mark()
    sync_brand_html()

    print("[2/7] Web / PWA（自带圆角用 rounded；maskable 用 bleed）")
    save_png(square(rounded, 192), os.path.join(ROOT, "icon-192.png"))
    save_png(square(rounded, 512), os.path.join(ROOT, "icon-512.png"))
    save_png(edge_extend(bleed, 512, MASKABLE_FRAC), os.path.join(ROOT, "maskable-512.png"))

    print("[3/7] iOS 桌面图标（bleed 全出血；iOS 自行圆角，避免双圆角）")
    save_png(square(bleed, 180), os.path.join(ROOT, "apple-touch-icon.png"))
    save_png(square(bleed, 167), os.path.join(ROOT, "apple-touch-icon-167.png"))

    print("[4/7] favicon.ico")
    save_ico(rounded, os.path.join(ROOT, "favicon.ico"))

    print("[5/7] Windows / Electron")
    save_png(square(rounded, 512), os.path.join(ROOT, "desktop", "build", "icon.png"))
    save_ico(rounded, os.path.join(ROOT, "desktop", "build", "icon.ico"))

    print("[6/7] Android")
    res = os.path.join(ROOT, "android", "app", "src", "main", "res")
    dens = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    for name, px in dens.items():
        save_png(square(bleed, px), os.path.join(res, "mipmap-" + name, "ic_launcher.png"))
        save_png(circular(bleed, px), os.path.join(res, "mipmap-" + name, "ic_launcher_round.png"))
    # 自适应前景：内容缩入安全窗口 + 边缘外扩填满（掩码裁到边缘也是干净渐变）
    old_xml = os.path.join(res, "drawable", "ic_launcher_foreground.xml")
    if os.path.exists(old_xml):
        os.remove(old_xml)
        print("  移除旧矢量前景 drawable/ic_launcher_foreground.xml")
    save_png(edge_extend(bleed, 432, ADAPTIVE_FRAC), os.path.join(res, "drawable", "ic_launcher_foreground.png"))
    with open(os.path.join(res, "values", "ic_launcher_background.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                '  <color name="ic_launcher_background">#4F46E5</color>\n</resources>\n')
    adaptive = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
        '  <background android:drawable="@color/ic_launcher_background"/>\n'
        '  <foreground android:drawable="@drawable/ic_launcher_foreground"/>\n'
        '</adaptive-icon>\n')
    for n in ("ic_launcher", "ic_launcher_round"):
        pr = os.path.join(res, "mipmap-anydpi-v26", n + ".xml")
        os.makedirs(os.path.dirname(pr), exist_ok=True)
        with open(pr, "w", encoding="utf-8", newline="\n") as f:
            f.write(adaptive)
    print("  mipmap-{mdpi..xxxhdpi}/ic_launcher{,_round}.png + 自适应前景 PNG + anydpi-v26")

    print("\n完成。")


if __name__ == "__main__":
    main()
