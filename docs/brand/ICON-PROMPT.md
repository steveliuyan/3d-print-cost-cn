# 3D 打印成本计算器 · App 图标生成提示词

> 用途：把本文件里的提示词整段复制给其它图像 AI（Midjourney / DALL·E / 即梦 / 可灵 / 豆包 / Stable Diffusion 等）生成应用图标。
> 版本：2026-10-13

---

## 1. 软件是什么（给 AI 的上下文）

**一句话**：一个给 3D 打印**报价**用的**成本计算器** —— 算清一件 3D 打印品的**真实成本**，给出建议售价。

**它具体做什么**：
- 输入：材料用量与单价、设备折旧、电费、人工与后处理、失败率（摊销）、佣金/加价等。
- 输出：**单件成本、建议售价、利润**，并支持多品项**订单报价**、导出与打印报价单。
- 用户：3D 打印服务商、手作／工作室、把打印当生意的创客。

**本质**：`3D 打印（一个被制造出来的实体物件）` × `成本 / 价格（钱）`。

**品牌基调**：简洁、现代、精确、可信赖；主色**靛蓝 #4f46e5**，辅色紫罗兰 #7c3aed。

---

## 2. 图标设计规范（AI 必须满足）

1. **正方形 1:1，满幅**（背景铺满整个画布，不要自带圆角 —— 圆角由系统加）。
2. **单一主体**：画面里只有**一个**视觉主体，位于正中、视觉居中、留白充足。不要多物件堆叠。
3. **主体 = 一个 3D 打印出来的物件**，把「成本 / 钱」融进这个主体内部（例如在物件表面出现 ¥ 或价签元素），而不是在旁边加一个徽章。
4. **风格**：扁平矢量插画（flat vector），可用**实心填充 + 柔和渐变**，不要写实照片、不要 3D 渲染高光、不要复杂纹理。
5. **高对比、粗形状**：缩到 **16px 仍能认出主体**。避免细线、细节、微小文字。
6. **配色 ≤ 3 色**：靛蓝 / 紫罗兰系 + 白（或浅底）。深底或浅底都可以。
7. **不要任何文字、字母、水印**（¥ 符号除外，且要简单）。

---

## 3. 可直接粘贴的提示词

### ▶ 英文主提示词（推荐，图像模型对英文更稳）

```
Design a modern app icon for a "3D printing cost calculator" — a tool that calculates the true cost and selling price of 3D-printed parts. Concept: a SINGLE centered isometric 3D cube (a 3D-printed object) with a simple yen/price motif (¥) integrated into its front face. Flat vector illustration style, solid fills with soft gradients, indigo (#4f46e5) and violet palette with white accents on a clean light background. Bold simple geometric shapes, strong contrast, generous negative space, crisp clean edges, optically centered, one single subject only, readable at 16 pixels. Square 1:1, full-bleed background, no text, no letters, no watermark, no photorealism, no 3D render glare, minimal.
```

### ▶ 中文备用提示词

```
为一款「3D 打印成本计算器」设计应用图标。这是一个计算 3D 打印件真实成本与建议售价的工具。
画面主体：正中央一个等距视角的 3D 立方体（代表一个 3D 打印出来的物件），在其正面融入一个简洁的人民币/价格符号「¥」。
风格：扁平矢量插画，实心填充 + 柔和渐变，靛蓝 #4f46e5 与紫罗兰配色，白色点缀，干净浅色背景。
要求：粗壮简洁的几何形状，对比强烈，留白充足，边缘清晰，视觉居中，画面只有一个主体，缩到 16px 仍清晰可辨。
正方形 1:1，背景满幅，不要文字、不要字母、不要水印、不要写实照片、不要 3D 渲染高光、极简。
```

### ▶ 反向提示词 / Negative prompt

```
text, letters, words, numbers, watermark, logo text, photorealism, realistic photo,
3D render glare, heavy shadows, busy details, clutter, multiple objects, stickers,
thin lines, tiny details, gradients with many colors, drop shadows, mockup, frame,
hand, human, background scenery
```

### ▶ Midjourney 参数建议（如用 MJ）

```
--ar 1:1 --style raw --v 6 --no text,letters,watermark,photorealism
```

---

## 4. 换风格？把下面这句加到提示词末尾

- **浅底简约**：`on a soft light lavender background, minimal, airy.`
- **深底高级**：`on a deep indigo night background, premium, subtle glow.`
- **更「3D 打印」**：`the cube surface shows horizontal 3D-printing layer lines.`
- **更「成本」**：`a bold price tag shape containing the ¥ symbol, single subject.`
- **更金融**：`a single coin/medallion with an embossed ¥ and a subtle cube, premium fintech style.`

---

## 5. 验收标准（生成后自己核对）

- [ ] 缩到 **32px / 16px** 还认得出主体？
- [ ] 画面**只有一个**主体，没有多余小元素？
- [ ] 没有夹带文字 / 水印 / 乱码字母？
- [ ] 配色是否靛蓝系、≤3 色？
- [ ] 1:1、背景满幅（没有自带白边或圆角框）？
- [ ] 主体视觉居中、留白均匀？

> 生成后用系统工具箱（或让我）把选定图切成一整套：Web favicon、PWA 192/512、iOS 180/167、Android 5 档 + 自适应、Windows ico/png。

---

## 6. 附：本项目当前图标（供参考/对比）

- 主色 `#4f46e5`；已有矢量候选在 `docs/brand/concepts/`（c1–c6）。
- 生成器 `_gen_icons.py` 负责把一张方形图标切成三端全套产物。
