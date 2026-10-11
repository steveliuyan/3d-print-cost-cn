# -*- coding: utf-8 -*-
"""生成应用图标：靛蓝圆角底 + 白色立方体（与应用内品牌图形一致）。"""
import os
from PIL import Image, ImageDraw

S = 1024                      # 超采样画布
BRAND = (79, 70, 229, 255)    # #4F46E5
WHITE = (255, 255, 255, 255)

img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, S - 1, S - 1], radius=224, fill=BRAND)

# 24x24 设计坐标 → 画布坐标：scale 30，居中原点 152
def P(x, y):
    return (152 + x * 30, 152 + y * 30)

W = 51  # 1.7 * 30

# 立方体外轮廓
d.line([P(12, 3), P(4, 7.5), P(4, 16.5), P(12, 21), P(20, 16.5), P(20, 7.5), P(12, 3)],
       fill=WHITE, width=W, joint='curve')
# 顶面 V 形
d.line([P(4, 7.5), P(12, 12), P(20, 7.5)], fill=WHITE, width=W, joint='curve')
# 中缝
d.line([P(12, 12), P(12, 21)], fill=WHITE, width=W, joint='curve')

base = img.resize((256, 256), Image.LANCZOS)

out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'desktop', 'build')
os.makedirs(out_dir, exist_ok=True)

ico = os.path.join(out_dir, 'icon.ico')
base.save(ico, format='ICO',
          sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

png = os.path.join(out_dir, 'icon.png')
img.resize((512, 512), Image.LANCZOS).save(png, format='PNG')

print('ico :', ico, os.path.getsize(ico), 'bytes')
print('png :', png, os.path.getsize(png), 'bytes')
