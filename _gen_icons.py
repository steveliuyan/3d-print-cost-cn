#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_gen_icons.py —— 从品牌标识生成三端全套图标（可复现）

品牌标识（64×64 空间）：等距立方体 + 右下角成本徽标圆（内含 ¥）。
应用图标 = 靛蓝圆角方框底（框本身即「圆角方框」）+ 白色立方体 + 白色徽标圆（靛蓝 ¥）。
标识按包围盒自动居中 + 缩放到指定占比，保证各尺寸构图一致。

产物：
  根目录      icon-192.png / icon-512.png / maskable-512.png / apple-touch-icon.png
              apple-touch-icon-167.png / favicon.svg / favicon.ico
  desktop     build/icon.png (512) / build/icon.ico (16..256)
  android     res/mipmap-*/ic_launcher.png (+_round, 5 档密度)
              res/drawable/ic_launcher_foreground.xml（自适应前景）
              res/values/ic_launcher_background.xml
              res/mipmap-anydpi-v26/ic_launcher.xml (+_round)
  docs/brand  icon-tile.svg（应用图标规范源）

用法：python _gen_icons.py
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.abspath(__file__))
INK   = (79, 70, 229, 255)    # #4f46e5
WHITE = (255, 255, 255, 255)
SS    = 4                     # 超采样倍率（抗锯齿）
BORDER = 64                   # 逻辑画布

# —— 64×64 坐标系中的几何（唯一来源：docs/brand/logo-mark.svg 亦由本文件生成）——
# v1.8.0 修订：徽标整体按包围盒居中（bbox 中心 = 画布中心 32,32），
# 并收小 ¥ 徽标（r 11.5→9）、内收至离外框描边留白 ≥4，消除「右下角压边 / 比例失衡」。
CUBE = [
    [(26.25, 10.2), (39.75, 18.0), (26.25, 25.8), (12.75, 18.0)],  # 顶面
    [(12.75, 18.0), (26.25, 25.8), (26.25, 41.4), (12.75, 33.6)],  # 左面
    [(39.75, 18.0), (26.25, 25.8), (26.25, 41.4), (39.75, 33.6)],  # 右面
]
CUBE_W = 3.0
BADGE = (42.25, 44.8, 9.0)                     # cx, cy, r（内收 + 收小）
YEN_W = 2.4
YEN = [
    ((38.62, 39.36), (42.25, 44.97)),
    ((45.88, 39.36), (42.25, 44.97)),
    ((42.25, 44.97), (42.25, 50.25)),
    ((39.61, 45.96), (44.89, 45.96)),
    ((39.61, 48.07), (44.89, 48.07)),
]
# 描边版（logo-mark.svg / 打印抬头）使用：外框 + 立方体线宽 + ¥ 圆变换参数
FRAME_W = 4.0
CUBE_W_LINE = 3.4
YEN_XF = (34.33, 36.72, 0.66)                  # translate(tx ty) scale(s)
YEN_W_LINE = 3.6                               # 变换后视觉线宽 ≈ 3.6*0.66 = 2.376
YEN_PATH = "M6.5 4 12 12.5M17.5 4 12 12.5M12 12.5V20.5M8 14h8M8 17.2h8"


def mark_bbox():
    xs, ys = [], []
    for face in CUBE:
        for (x, y) in face:
            xs.append(x); ys.append(y)
    bx, by, br = BADGE
    xs += [bx - br, bx + br]; ys += [by - br, by + br]
    for (a, b) in YEN:
        xs += [a[0], b[0]]; ys += [a[1], b[1]]
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
    """标识上离包围盒中心最远的点（含徽标外缘）到中心的距离。"""
    x0, y0, x1, y1 = mark_bbox()
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    r = 0.0
    for face in CUBE:
        for (x, y) in face:
            r = max(r, ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5)
    bx, by, br = BADGE
    r = max(r, ((bx - cx) ** 2 + (by - cy) ** 2) ** 0.5 + br)
    for (a, b) in YEN:
        for p in (a, b):
            r = max(r, ((p[0] - cx) ** 2 + (p[1] - cy) ** 2) ** 0.5)
    return r


def build_xf_radial(safe_frac, canvas):
    """径向安全区适配：保证标识最远点落在 canvas*safe_frac 半径内（供圆形/自适应遮罩）。"""
    x0, y0, x1, y1 = mark_bbox()
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    k = (canvas * safe_frac) / mark_radius()

    def f(p):
        return ((p[0] - cx) * k + canvas / 2.0, (p[1] - cy) * k + canvas / 2.0)
    return f, k


STYLES = {"tile": 0.80, "maskable": 0.56, "touch": 0.68, "round": 0.72}


def render(size, style):
    W = size * SS
    pxf, k = build_xf(STYLES[style], BORDER)          # 64 空间变换
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

    for face in CUBE:
        pts = [P(p) for p in face] + [P(face[0])]
        d.line(pts, fill=WHITE, width=lw(CUBE_W), joint="curve")
    bx, by, br = BADGE
    c = P((bx, by)); rp = br * k * W / BORDER
    d.ellipse([c[0] - rp, c[1] - rp, c[0] + rp, c[1] + rp], fill=WHITE)
    for (a, b) in YEN:
        d.line([P(a), P(b)], fill=INK, width=lw(YEN_W))

    return img.resize((size, size), Image.LANCZOS)


def fmt(v):
    return ("%.3f" % v).rstrip("0").rstrip(".")


def build_svg(target_frac, rounded):
    f, k = build_xf(target_frac, BORDER)
    def c(p):
        q = f(p)
        return "%s %s" % (fmt(q[0]), fmt(q[1]))
    sw = fmt(CUBE_W * k)
    face = "".join('<path d="M%sZ"/>' % " ".join(c(p) for p in fc) for fc in CUBE)
    bx, by, br = BADGE
    bc = f((bx, by))
    segs = []
    for (a, b) in YEN:
        pa, pb = f(a), f(b)
        segs.append("M%s %s %s %s" % (fmt(pa[0]), fmt(pa[1]), fmt(pb[0]), fmt(pb[1])))
    yen_path = "".join(segs)
    yen_sw = fmt(YEN_W * k)
    bg = '<rect width="64" height="64" rx="14" fill="#4f46e5"/>' if rounded else ""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-label="3D 打印成本计算器">\n'
        '  <title>3D 打印成本计算器 · 应用图标</title>\n'
        '  %s\n'
        '  <g fill="none" stroke="#ffffff" stroke-width="%s" stroke-linejoin="round">%s</g>\n'
        '  <circle cx="%s" cy="%s" r="%s" fill="#ffffff"/>\n'
        '  <path d="%s" fill="none" stroke="#4f46e5" stroke-width="%s" stroke-linecap="round"/>\n'
        '</svg>\n'
    ) % (bg, sw, face, fmt(bc[0]), fmt(bc[1]), fmt(br * k), yen_path, yen_sw)


def build_svg_compact(target_frac):
    """favicon 用的单行内联版（单引号 + %23 编码，去 title/role）。"""
    f, k = build_xf(target_frac, BORDER)

    def c(p):
        q = f(p)
        return "%s %s" % (fmt(q[0]), fmt(q[1]))
    face = "".join("<path d='M%sZ'/>" % " ".join(c(p) for p in fc) for fc in CUBE)
    bx, by, br = BADGE
    bc = f((bx, by))
    segs = []
    for (a, b) in YEN:
        pa, pb = f(a), f(b)
        segs.append("M%s %s %s %s" % (fmt(pa[0]), fmt(pa[1]), fmt(pb[0]), fmt(pb[1])))
    raw = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>"
        "<rect width='64' height='64' rx='14' fill='#4f46e5'/>"
        "<g fill='none' stroke='#ffffff' stroke-width='%s' stroke-linejoin='round'>%s</g>"
        "<circle cx='%s' cy='%s' r='%s' fill='#ffffff'/>"
        "<path d='%s' fill='none' stroke='#4f46e5' stroke-width='%s' stroke-linecap='round'/>"
        "</svg>"
    ) % (fmt(CUBE_W * k), face, fmt(bc[0]), fmt(bc[1]), fmt(br * k), "".join(segs), fmt(YEN_W * k))
    # data-URI 安全化：<> 与 # 必须编码（引号统一用单引号，避免与外层 href="…" 冲突）
    return raw.replace("<", "%3C").replace(">", "%3E").replace("#", "%23")


def sync_favicon_uri():
    """把内联 favicon data-URI 同步进 index.html（唯一来源 = 本脚本的几何常量）。"""
    import re
    uri = build_svg_compact(STYLES["tile"])
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


def build_mark_svg():
    """描边版品牌标识（docs/brand/logo-mark.svg）：外框 + 立方体 + ¥ 徽标，currentColor 着色。"""
    def cp(p):
        return "%s %s" % (fmt(p[0]), fmt(p[1]))
    faces = "".join(
        '  <path d="M%sZ" stroke="currentColor" stroke-width="%s" stroke-linejoin="round"/>\n'
        % (" ".join(cp(p) for p in fc), fmt(CUBE_W_LINE)) for fc in CUBE)
    bx, by, br = BADGE
    tx, ty, s = YEN_XF
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64" '
        'role="img" aria-label="3D 打印成本计算器" color="#4f46e5" fill="none">\n'
        '  <title>3D 打印成本计算器 · 品牌标识</title>\n'
        '  <rect x="4" y="4" width="56" height="56" rx="14" stroke="currentColor" stroke-width="%s"/>\n'
        '%s'
        '  <circle cx="%s" cy="%s" r="%s" fill="currentColor"/>\n'
        '  <g transform="translate(%s %s) scale(%s)" stroke="#ffffff" stroke-width="%s" stroke-linecap="round" fill="none">\n'
        '    <path d="%s"/>\n'
        '  </g>\n'
        '</svg>\n'
    ) % (fmt(FRAME_W), faces, fmt(bx), fmt(by), fmt(br),
         fmt(tx), fmt(ty), fmt(s), fmt(YEN_W_LINE), YEN_PATH)


def build_mark_inner_svg():
    """顶栏用实心白版标识（无外框，viewBox 紧贴包围盒）：白立方体 + 白徽标圆 + 靛蓝 ¥。"""
    x0, y0, x1, y1 = mark_bbox()
    pad = 2.0
    vb = "%s %s %s %s" % (fmt(x0 - pad), fmt(y0 - pad),
                          fmt((x1 - x0) + 2 * pad), fmt((y1 - y0) + 2 * pad))
    faces = "".join("<path d='M%sZ'/>" % " ".join(
        "%s %s" % (fmt(p[0]), fmt(p[1])) for p in fc) for fc in CUBE)
    bx, by, br = BADGE
    tx, ty, s = YEN_XF
    return (
        "<svg viewBox='%s' fill='none' aria-hidden='true'>"
        "<g stroke='#ffffff' stroke-width='%s' stroke-linejoin='round'>%s</g>"
        "<circle cx='%s' cy='%s' r='%s' fill='#ffffff'/>"
        "<g transform='translate(%s %s) scale(%s)' stroke='#4f46e5' stroke-width='%s' stroke-linecap='round' fill='none'>"
        "<path d='%s'/></g>"
        "</svg>"
    ) % (vb, fmt(CUBE_W), faces, fmt(bx), fmt(by), fmt(br),
         fmt(tx), fmt(ty), fmt(s), fmt(YEN_W_LINE), YEN_PATH)


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


def android_vector(safe_frac=0.3055, canvas=108):
    f, k = build_xf_radial(safe_frac, canvas)
    def c(p):
        q = f(p)
        return "%s,%s" % (fmt(q[0]), fmt(q[1]))
    sw = fmt(CUBE_W * k)
    paths = []
    for fc in CUBE:
        d = "M" + "L".join(c(p) for p in fc) + "Z"
        paths.append('  <path android:fillColor="#00000000" android:strokeColor="#FFFFFF" '
                     'android:strokeWidth="%s" android:strokeLineJoin="round" '
                     'android:strokeLineCap="round" android:pathData="%s"/>' % (sw, d))
    bx, by, br = BADGE
    bc = f((bx, by))
    paths.append('  <path android:fillColor="#FFFFFF" android:pathData="M%s a%s,%s 0 1,0 %s,0 '
                 'a%s,%s 0 1,0 -%s,0Z"/>'
                 % (c((bx - br, by)), fmt(br * k), fmt(br * k), fmt(2 * br * k),
                    fmt(br * k), fmt(br * k), fmt(2 * br * k)))
    segs = []
    for (a, b) in YEN:
        pa, pb = f(a), f(b)
        segs.append("M%sL%s" % (c(a), c(b)))
    paths.append('  <path android:fillColor="#00000000" android:strokeColor="#4F46E5" '
                 'android:strokeWidth="%s" android:strokeLineCap="round" '
                 'android:pathData="%s"/>' % (fmt(YEN_W * k), "".join(segs)))
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
    print("[1/6] 规范源 SVG")
    svg = build_svg(STYLES["tile"], rounded=True)
    for name in ("docs/brand/icon-tile.svg", "favicon.svg"):
        with open(os.path.join(ROOT, *name.split("/")), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg)
    print("  docs/brand/icon-tile.svg + favicon.svg")
    with open(os.path.join(ROOT, "docs", "brand", "logo-mark.svg"), "w", encoding="utf-8", newline="\n") as f:
        f.write(build_mark_svg())
    print("  docs/brand/logo-mark.svg")
    sync_favicon_uri()
    sync_topbar_mark()

    print("[2/6] Web / PWA")
    save_png(render(192, "tile"), os.path.join(ROOT, "icon-192.png"))
    save_png(render(512, "tile"), os.path.join(ROOT, "icon-512.png"))
    save_png(render(512, "maskable"), os.path.join(ROOT, "maskable-512.png"))

    print("[3/6] iOS 桌面图标（满幅、无透明，iOS 自行圆角）")
    save_png(render(180, "touch"), os.path.join(ROOT, "apple-touch-icon.png"))
    save_png(render(167, "touch"), os.path.join(ROOT, "apple-touch-icon-167.png"))

    print("[4/6] favicon.ico")
    p = os.path.join(ROOT, "favicon.ico")
    render(256, "tile").save(p, "ICO", sizes=ICO_SIZES)
    print("  %-56s %6d B" % ("favicon.ico", os.path.getsize(p)))

    print("[5/6] Windows / Electron")
    save_png(render(512, "tile"), os.path.join(ROOT, "desktop", "build", "icon.png"))
    p = os.path.join(ROOT, "desktop", "build", "icon.ico")
    render(256, "tile").save(p, "ICO", sizes=ICO_SIZES)
    print("  %-56s %6d B" % (os.path.relpath(p, ROOT), os.path.getsize(p)))

    print("[6/6] Android")
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
