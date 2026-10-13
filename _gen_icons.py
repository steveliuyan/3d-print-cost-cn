#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_gen_icons.py —— 从品牌标识生成三端全套图标（可复现）

品牌标识（64×64 空间）：等距立方体（顶/左/右三面），无徽标。
应用图标 = 靛蓝圆角方框底 + 实心白立方体（三面填白）+ 靛蓝细缝（立方体三条内棱）。
标识按包围盒自动居中 + 缩放到指定占比，保证各尺寸构图一致。

产物：
  根目录      icon-192.png / icon-512.png / maskable-512.png / apple-touch-icon.png
              apple-touch-icon-167.png / favicon.svg / favicon.ico
  desktop     build/icon.png (512) / build/icon.ico (16..256)
  android     res/mipmap-*/ic_launcher.png (+_round, 5 档密度)
              res/drawable/ic_launcher_foreground.xml（自适应前景）
              res/values/ic_launcher_background.xml
              res/mipmap-anydpi-v26/ic_launcher.xml (+_round)
  docs/brand  icon-tile.svg（应用图标规范源）/ logo-mark.svg（描边版，供设计/深色底）
  并同步 index.html 三处：内联 favicon data-URI / 顶栏 .mark 标识 / 报价单抬头 BRAND_SVG

用法：python _gen_icons.py
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
INK   = (79, 70, 229, 255)    # #4f46e5
WHITE = (255, 255, 255, 255)
SS    = 4                     # 超采样倍率（抗锯齿）
BORDER = 64                   # 逻辑画布

# —— 64×64 坐标系中的几何（唯一来源：docs/brand/*.svg 亦由本文件生成）——
# v1.8.0 修订：去掉右下角 ¥ 成本徽标，改回纯立方体；立方体以画布中心 (32,32) 居中。
CUBE = [
    [(32.0, 16.4), (45.5, 24.2), (32.0, 32.0), (18.5, 24.2)],  # 顶面
    [(18.5, 24.2), (32.0, 32.0), (32.0, 47.6), (18.5, 39.8)],  # 左面
    [(45.5, 24.2), (32.0, 32.0), (32.0, 47.6), (45.5, 39.8)],  # 右面
]
SEAM_W = 1.9                                   # 内棱线宽（64 空间）
SEAMS = [((18.5, 24.2), (32.0, 32.0)),         # 顶-左 内棱
         ((45.5, 24.2), (32.0, 32.0)),         # 顶-右 内棱
         ((32.0, 32.0), (32.0, 47.6))]         # 左-右 内棱
# 描边版（logo-mark.svg / 打印抬头）使用：外框 + 立方体线宽
FRAME_W = 4.0
CUBE_W_LINE = 3.4


def mark_bbox():
    xs, ys = [], []
    for face in CUBE:
        for (x, y) in face:
            xs.append(x); ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def build_xf(target_frac, canvas):
    """返回 (f, k)：把标识包围盒居中缩放到 canvas 的 target_frac 占比。"""
    x0, y0, x1, y1 = mark_bbox()
    maxd = max(x1 - x0, y1 - y0)
    k = (canvas * target_frac) / maxd
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0

    def f(p):
        return ((p[0] - cx) * k + canvas / 2.0, (p[1] - cy) * k + canvas / 2.0)
    return f, k


def mark_radius():
    """标识上离包围盒中心最远的点（立方体顶点）到中心的距离。"""
    x0, y0, x1, y1 = mark_bbox()
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    r = 0.0
    for face in CUBE:
        for (x, y) in face:
            r = max(r, ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5)
    return r


def build_xf_radial(safe_frac, canvas):
    """径向安全区适配：保证标识最远点落在 canvas*safe_frac 半径内（供圆形/自适应遮罩）。"""
    x0, y0, x1, y1 = mark_bbox()
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    k = (canvas * safe_frac) / mark_radius()

    def f(p):
        return ((p[0] - cx) * k + canvas / 2.0, (p[1] - cy) * k + canvas / 2.0)
    return f, k


# 每种样式的标识占比：(frac, radial)
#   linear = 按包围盒较长边占画布比例；radial = 按最远点占画布半径比例（圆形/自适应安全区）
STYLES = {
    "tile":     (0.61, False),   # 网页/PWA/Windows 圆角方框
    "touch":    (0.55, False),   # iOS 满幅（系统自行圆角）
    "round":    (0.305, True),   # 安卓圆形图标（与 tile 视觉占比一致 ≈61.5%）
    "maskable": (0.40, True),    # PWA maskable（安全圆内）
}


def _seam_polylines():
    """两条折线：V 形（顶面两条内棱）+ 竖直（左右面内棱）。"""
    return [[SEAMS[0][0], (32.0, 32.0), SEAMS[1][0]], [SEAMS[2][0], SEAMS[2][1]]]


def render(size, style):
    frac, radial = STYLES[style]
    W = size * SS
    pxf, k = build_xf_radial(frac, BORDER) if radial else build_xf(frac, BORDER)

    def P(p):
        q = pxf(p)
        return (q[0] * W / BORDER, q[1] * W / BORDER)

    def lw(w):
        return max(1, int(round(w * k * W / BORDER)))

    img = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if style == "tile":
        d.rounded_rectangle([0, 0, W - 1, W - 1], radius=W * 14 / 64, fill=INK)
    elif style == "round":
        d.ellipse([0, 0, W - 1, W - 1], fill=INK)
    else:
        d.rectangle([0, 0, W, W], fill=INK)

    # 三面填白（不加外描边：外轮廓即白/靛蓝硬边，干净）
    for face in CUBE:
        d.polygon([P(p) for p in face], fill=WHITE)
    # 三条内棱：靛蓝细缝（与底色同色，只在面与面之间可见）
    for pl in _seam_polylines():
        d.line([P(p) for p in pl], fill=INK, width=lw(SEAM_W), joint="curve")

    return img.resize((size, size), Image.LANCZOS)


def fmt(v):
    return ("%.3f" % v).rstrip("0").rstrip(".")


def _face_path(pts):
    return "M%sZ" % " ".join("%s %s" % (fmt(p[0]), fmt(p[1])) for p in pts)


def build_svg(target_frac, rounded):
    f, k = build_xf(target_frac, BORDER)

    def c(p):
        q = f(p)
        return "%s %s" % (fmt(q[0]), fmt(q[1]))

    faces = "".join('<path d="%s"/>' % " ".join(c(p) for p in fc) for fc in CUBE)
    seams = "".join("M%s %s %s %s" % (fmt(f(a)[0]), fmt(f(a)[1]), fmt(f(b)[0]), fmt(f(b)[1]))
                    for (a, b) in SEAMS)
    bg = '<rect width="64" height="64" rx="14" fill="#4f46e5"/>' if rounded else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-label="3D 打印成本计算器">\n'
        '  <title>3D 打印成本计算器 · 应用图标</title>\n'
        '  %s\n'
        '  <g fill="#ffffff">%s</g>\n'
        '  <path d="%s" fill="none" stroke="#4f46e5" stroke-width="%s" '
        'stroke-linecap="round" stroke-linejoin="round"/>\n'
        '</svg>\n'
    ) % (bg, faces, seams, fmt(SEAM_W * k))


def build_svg_compact(target_frac):
    """favicon 用的单行内联版（单引号 + %23 编码，去 title/role）。"""
    f, k = build_xf(target_frac, BORDER)

    def c(p):
        q = f(p)
        return "%s %s" % (fmt(q[0]), fmt(q[1]))

    faces = "".join("<path d='M%sZ'/>" % " ".join(c(p) for p in fc) for fc in CUBE)
    seams = "".join("M%s %s %s %s" % (fmt(f(a)[0]), fmt(f(a)[1]), fmt(f(b)[0]), fmt(f(b)[1]))
                    for (a, b) in SEAMS)
    raw = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
        "<rect width='64' height='64' rx='14' fill='#4f46e5'/>"
        "<g fill='#ffffff'>%s</g>"
        "<path d='%s' fill='none' stroke='#4f46e5' stroke-width='%s' "
        "stroke-linecap='round' stroke-linejoin='round'/>"
        "</svg>"
    ) % (faces, seams, fmt(SEAM_W * k))
    # data-URI 安全化：<> 与 # 必须编码（引号统一用单引号，避免与外层 href="…" 冲突）
    return raw.replace("<", "%3C").replace(">", "%3E").replace("#", "%23")


def sync_favicon_uri():
    """把内联 favicon data-URI 同步进 index.html（唯一来源 = 本脚本的几何常量）。"""
    import re
    uri = build_svg_compact(STYLES["tile"][0])
    p = os.path.join(ROOT, "index.html")
    with open(p, encoding="utf-8", newline="") as f:
        s = f.read()
    # 容忍 IDE 预览回注的多余属性（data-page-node-id 等），替换为干净链接
    pat = re.compile(r'<link rel="icon" href="data:image/svg\+xml,[^"]*"[^>]*>')
    new = '<link rel="icon" href="data:image/svg+xml,%s">' % uri
    if not pat.search(s):
        print("  [warn] index.html 未找到内联 favicon link，跳过")
        return False
    s2 = pat.sub(lambda m: new, s, count=1)
    if s2 != s:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(s2)
        print("  index.html 内联 favicon 已更新")
    else:
        print("  index.html 内联 favicon 已是最新")
    return True


def build_brand_svg_js():
    """index.html 中 BRAND_SVG 变量的 JS 字面量（描边版，currentColor；供报价单抬头 / 分享长图 / 空状态）。"""
    lines = []
    for fc in CUBE:
        lines.append('      \'<path d="%s" stroke="currentColor" stroke-width="%s" '
                     'stroke-linejoin="round"/>\' +' % (_face_path(fc), fmt(CUBE_W_LINE)))
    body = "\n".join(lines)
    return (
        '  var BRAND_SVG =\n'
        '    \'<svg viewBox="0 0 64 64" fill="none" aria-hidden="true">\' +\n'
        '      \'<rect x="4" y="4" width="56" height="56" rx="14" stroke="currentColor" '
        'stroke-width="%s"/>\' +\n'
        '%s\n'
        '    "</svg>";'
    ) % (fmt(FRAME_W), body)


def sync_brand_svg():
    """把 index.html 的 BRAND_SVG 变量替换为最新描边版立方体标识（唯一来源 = 本脚本几何）。"""
    import re
    p = os.path.join(ROOT, "index.html")
    with open(p, encoding="utf-8", newline="") as f:
        s = f.read()
    pat = re.compile(r'  var BRAND_SVG =[\s\S]*?"</svg>";')
    new = build_brand_svg_js()
    if not pat.search(s):
        print("  [warn] index.html 未找到 BRAND_SVG 变量，跳过")
        return False
    s2 = pat.sub(lambda m: new, s, count=1)
    if s2 != s:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(s2)
        print("  index.html 报价单抬头 BRAND_SVG 已更新")
    else:
        print("  index.html BRAND_SVG 已是最新")
    return True


def build_mark_svg():
    """描边版品牌标识（docs/brand/logo-mark.svg）：外框 + 立方体三面线框，currentColor 着色。"""
    def cp(p):
        return "%s %s" % (fmt(p[0]), fmt(p[1]))
    faces = "".join(
        '  <path d="M%sZ" stroke="currentColor" stroke-width="%s" stroke-linejoin="round"/>\n'
        % (" ".join(cp(p) for p in fc), fmt(CUBE_W_LINE)) for fc in CUBE)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-label="3D 打印成本计算器" color="#4f46e5" fill="none">\n'
        '  <title>3D 打印成本计算器 · 品牌标识</title>\n'
        '  <rect x="4" y="4" width="56" height="56" rx="14" stroke="currentColor" stroke-width="%s"/>\n'
        '%s'
        '</svg>\n'
    ) % (fmt(FRAME_W), faces)


def build_mark_inner_svg():
    """顶栏用实心白版标识（无外框，viewBox 紧贴包围盒）：三面填白 + 靛蓝内棱缝。"""
    x0, y0, x1, y1 = mark_bbox()
    pad = 2.0
    vb = "%s %s %s %s" % (fmt(x0 - pad), fmt(y0 - pad),
                          fmt((x1 - x0) + 2 * pad), fmt((y1 - y0) + 2 * pad))
    faces = "".join("<path d='M%sZ'/>" % " ".join(
        "%s %s" % (fmt(p[0]), fmt(p[1])) for p in fc) for fc in CUBE)
    seams = "".join("M%s %s %s %s" % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]))
                    for (a, b) in SEAMS)
    return (
        "<svg viewBox='%s' fill='none' aria-hidden='true'>"
        "<g fill='#ffffff'>%s</g>"
        "<path d='%s' fill='none' stroke='#4f46e5' stroke-width='%s' "
        "stroke-linecap='round' stroke-linejoin='round'/>"
        "</svg>"
    ) % (vb, faces, seams, fmt(SEAM_W))


def sync_topbar_mark():
    """把顶栏 .mark 的内联 svg 替换为最新的实心白版标识（唯一来源 = 本脚本几何）。"""
    import re
    svg = build_mark_inner_svg()
    p = os.path.join(ROOT, "index.html")
    with open(p, encoding="utf-8", newline="") as f:
        s = f.read()
    # 容忍 IDE 预览回注属性；非贪婪匹配 span 内第一个 <svg>…</svg>
    pat = re.compile(r'(<span class="mark"[^>]*>)\s*<svg\b[\s\S]*?</svg>(\s*</span>)')
    if not pat.search(s):
        print("  [warn] index.html 未找到顶栏 .mark 内联 svg，跳过")
        return False
    s2 = pat.sub(lambda m: m.group(1) + svg + m.group(2), s, count=1)
    if s2 != s:
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(s2)
        print("  index.html 顶栏标识已更新")
    else:
        print("  index.html 顶栏标识已是最新")
    return True


def android_vector(safe_frac=0.205, canvas=108):
    """自适应图标前景层（108dp 画布）。
    v1.8.2 修订：safe_frac 0.31 → 0.205。启动器只显示中央 72dp 可视区，
    旧值使立方体占可视区 93%（几乎顶满、显大）；新值 ≈61.5%，与网页/PWA tile 图标比例一致。"""
    f, k = build_xf_radial(safe_frac, canvas)

    def c(p):
        q = f(p)
        return "%s,%s" % (fmt(q[0]), fmt(q[1]))

    paths = []
    for fc in CUBE:
        d = "M" + "L".join(c(p) for p in fc) + "Z"
        paths.append('  <path android:fillColor="#FFFFFF" android:pathData="%s"/>' % d)
    segs = []
    for (a, b) in SEAMS:
        segs.append("M%sL%s" % (c(a), c(b)))
    paths.append('  <path android:fillColor="#00000000" android:strokeColor="#4F46E5" '
                 'android:strokeWidth="%s" android:strokeLineCap="round" '
                 'android:strokeLineJoin="round" android:pathData="%s"/>' % (fmt(SEAM_W * k), "".join(segs)))
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<!-- 由 _gen_icons.py 生成 · 自适应图标前景层 -->\n'
        '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    android:width="108dp" android:height="108dp"\n'
        '    android:viewportWidth="108" android:viewportHeight="108">\n'
        + "\n".join(paths) + "\n</vector>\n"
    )


def save_png(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, "PNG")
    print("  %-56s %6d B" % (os.path.relpath(path, ROOT), os.path.getsize(path)))


ICO_SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def make_preview():
    """生成品牌资产对照图 docs/brand/icon-preview.png（尺寸行 + 样式行）。"""
    sizes = [16, 24, 32, 48, 64, 128, 256]
    pad, gap, cell = 28, 18, 256
    row1w = pad * 2 + len(sizes) * cell + (len(sizes) - 1) * gap
    W = max(row1w, 1100)
    H = pad * 3 + cell * 2 + 40
    sheet = Image.new("RGBA", (W, H), (244, 245, 248, 255))
    d = ImageDraw.Draw(sheet)
    for i, s in enumerate(sizes):
        im = render(s, "tile")
        x = pad + i * (cell + gap) + (cell - im.width) // 2
        y = pad + (cell - im.height) // 2
        d.rectangle([x - 8, y - 8, x + im.width + 8, y + im.height + 8], outline=(214, 218, 226, 255))
        sheet.alpha_composite(im, (x, y))
    y2 = pad * 2 + cell + 40
    for i, style in enumerate(["tile", "maskable", "touch", "round"]):
        im = render(256, style)
        sheet.alpha_composite(im, (pad + i * (cell + gap - 40), y2))
    out = os.path.join(ROOT, "docs", "brand", "icon-preview.png")
    sheet.convert("RGB").save(out)
    print("  %-56s %6d B" % ("docs/brand/icon-preview.png", os.path.getsize(out)))


def main():
    print("[1/7] 规范源 SVG")
    svg = build_svg(STYLES["tile"][0], rounded=True)
    for name in ("docs/brand/icon-tile.svg", "favicon.svg"):
        with open(os.path.join(ROOT, *name.split("/")), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
    print("  docs/brand/icon-tile.svg + favicon.svg")
    with open(os.path.join(ROOT, "docs", "brand", "logo-mark.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_mark_svg())
    print("  docs/brand/logo-mark.svg")
    sync_favicon_uri()
    sync_topbar_mark()
    sync_brand_svg()

    print("[2/7] Web / PWA")
    save_png(render(192, "tile"), os.path.join(ROOT, "icon-192.png"))
    save_png(render(512, "tile"), os.path.join(ROOT, "icon-512.png"))
    save_png(render(512, "maskable"), os.path.join(ROOT, "maskable-512.png"))

    print("[3/7] iOS 桌面图标（满幅、无透明，iOS 自行圆角）")
    save_png(render(180, "touch"), os.path.join(ROOT, "apple-touch-icon.png"))
    save_png(render(167, "touch"), os.path.join(ROOT, "apple-touch-icon-167.png"))

    print("[4/7] favicon.ico")
    p = os.path.join(ROOT, "favicon.ico")
    render(256, "tile").save(p, "ICO", sizes=ICO_SIZES)
    print("  %-56s %6d B" % ("favicon.ico", os.path.getsize(p)))

    print("[5/7] Windows / Electron")
    save_png(render(512, "tile"), os.path.join(ROOT, "desktop", "build", "icon.png"))
    p = os.path.join(ROOT, "desktop", "build", "icon.ico")
    render(256, "tile").save(p, "ICO", sizes=ICO_SIZES)
    print("  %-56s %6d B" % (os.path.relpath(p, ROOT), os.path.getsize(p)))

    print("[6/7] Android")
    res = os.path.join(ROOT, "android", "app", "src", "main", "res")
    dens = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    for name, px in dens.items():
        save_png(render(px, "tile"),  os.path.join(res, "mipmap-" + name, "ic_launcher.png"))
        save_png(render(px, "round"), os.path.join(res, "mipmap-" + name, "ic_launcher_round.png"))
    fg = android_vector()
    with open(os.path.join(res, "drawable", "ic_launcher_foreground.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(fg)
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
    print("  mipmap-{mdpi..xxxhdpi}/ic_launcher{,_round}.png + 自适应前景 + anydpi-v26")

    print("[7/7] 品牌资产对照图")
    make_preview()
    print("\n完成。")


if __name__ == "__main__":
    main()
