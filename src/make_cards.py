# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB, OUT, OUT_CHARTS, OUT_CARDS
# -*- coding: utf-8 -*-
"""生成猎聘作品图片卡片 1600x1000"""
import os
from PIL import Image, ImageDraw, ImageFont

IMG = str(OUT_CHARTS)
OUT = str(OUT_CARDS)
os.makedirs(OUT, exist_ok=True)

W, H = 1600, 1000
NAVY = (31, 78, 121)
BLUE = (46, 134, 193)
GRAY = (120, 130, 140)
LIGHT = (240, 246, 252)
DARK = (34, 34, 34)

F_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
F_REG = r"C:\Windows\Fonts\msyh.ttc"

def font(size, bold=False):
    return ImageFont.truetype(F_BOLD if bold else F_REG, size)

def wrap(draw, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=fnt) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines

def base_card(title, takeaway, tag="数据分析作品集 · 电商活动复盘"):
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    # 顶部标签与标题
    d.text((90, 62), tag, font=font(24), fill=GRAY)
    d.text((90, 100), title, font=font(46, True), fill=NAVY)
    d.rectangle([90, 168, 1510, 169], fill=(226, 232, 240))
    # 底部结论条
    d.rectangle([0, 812, W, 1000], fill=LIGHT)
    d.rectangle([60, 846, 68, 966], fill=BLUE)
    tf = font(29)
    lines = wrap(d, takeaway, tf, 1420)
    y = 850
    for ln in lines[:3]:
        d.text((90, y), ln, font=tf, fill=DARK)
        y += 42
    # 页脚
    d.text((90, 970), "袁英豪 · 2027 届 · SQL / Python / Power BI", font=font(20), fill=GRAY)
    return img, d

def paste_chart(img, name, box=(90, 195, 1510, 790)):
    p = os.path.join(IMG, name)
    ch = Image.open(p).convert("RGB")
    bw, bh = box[2] - box[0], box[3] - box[1]
    s = min(bw / ch.width, bh / ch.height)
    ch = ch.resize((int(ch.width * s), int(ch.height * s)), Image.LANCZOS)
    x = box[0] + (bw - ch.width) // 2
    y = box[1] + (bh - ch.height) // 2
    img.paste(ch, (x, y))

def save(img, name):
    img.save(os.path.join(OUT, name), quality=95)

# ---------- 封面 ----------
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
d.rectangle([0, 0, W, 22], fill=NAVY)
d.text((90, 120), "数据分析作品集", font=font(34), fill=BLUE)
d.text((90, 190), "国庆好物节 · 活动效果分析", font=font(64, True), fill=NAVY)
d.text((90, 292), "6 张业务表 · 14 天活动 · 漏斗 + 投放 + 画像 + A/B 实验", font=font(30), fill=DARK)
d.rectangle([90, 370, 1510, 371], fill=(226, 232, 240))

kpis = [("22,572", "曝光用户"), ("8.45%", "曝光→点击"), ("25.64%", "点击→参与"), ("+3.36pp", "A/B 参与率提升")]
x0, y0, tw, th, gap = 90, 430, 330, 190, 33
for i, (v, lab) in enumerate(kpis):
    x = x0 + i * (tw + gap)
    d.rounded_rectangle([x, y0, x + tw, y0 + th], radius=14, fill=LIGHT, outline=(222, 232, 240), width=2)
    d.text((x + 24, y0 + 30), v, font=font(46, True), fill=NAVY)
    d.text((x + 24, y0 + 112), lab, font=font(26), fill=GRAY)

d.text((90, 690), "核心结论", font=font(30, True), fill=NAVY)
concl = "漏斗瓶颈在「点击→参与」；资源位曝光结构与转化效率错配；A/B 验证首屏差异化权益包可显著提升参与率。"
for i, ln in enumerate(wrap(d, concl, font(27), 1400)):
    d.text((90, 740 + i * 40), ln, font=font(27), fill=DARK)

d.rectangle([0, 900, W, 1000], fill=LIGHT)
d.rectangle([60, 918, 68, 982], fill=BLUE)
d.text((90, 922), "袁英豪 · 人工智能专业 2027 届 · 信阳学院", font=font(24), fill=DARK)
d.text((90, 958), "15238229315　|　2928767697@qq.com　|　github.com/danke-ai", font=font(20), fill=GRAY)
save(img, "00_封面.png")

# ---------- 图表卡片 ----------
cards = [
    ("整体漏斗：瓶颈在「点击 → 参与」",
     "曝光 22,572 → 点击 1,907 → 参与 489 → 达标 396；点击→参与仅 25.64%，是最大流失环节。",
     "gq1_funnel.png", "01_整体漏斗.png"),
    ("每日节奏：参与集中在两个大促节点",
     "10-01 与 10-08 贡献主要参与与达标；10-03/05/07/10 曝光 6,500+，点击却只有 170–197。",
     "gq2_daily.png", "02_每日节奏.png"),
    ("资源位：曝光结构与转化效率错配",
     "首页图文占 81.3% 曝光、点击率仅 3.7%；首页弹窗点击率 91.3%，曝光只占 5.6%。",
     "gq3_resource.png", "03_资源位效率.png"),
    ("投放时段：与用户活跃基本对齐",
     "曝光高峰在 7–8 点与 21–23 点；参与峰值 7 点 49 人、21 点 35 人，投放时段与活跃对齐。",
     "gq4_hourly.png", "04_投放时段.png"),
    ("人群：安卓与老用户参与率更高",
     "样本内参与率：安卓 57% vs iOS 13%；新注册 42% vs 老用户 56–57%；15–25 岁最高（50%）。",
     "gq5_profile.png", "05_用户画像.png"),
    ("曝光与参与强正相关",
     "小时曝光与参与 r=0.823；按拟合，2,000 人参与约需 20 万曝光人次（注意口径与外推风险）。",
     "gq7_corr.png", "06_相关性预测.png"),
    ("A/B 实验：差异化权益包显著提升参与",
     "参与率 +3.36pp（p=0.00056），达标率 +3.14pp；券后退款率无显著变化（p=0.7765）。",
     "gq11_ab_forest.png", "07_A_B实验.png"),
]
for title, take, src, out in cards:
    im, _ = base_card(title, take)
    paste_chart(im, src)
    save(im, out)

print("saved to", OUT)
for f in sorted(os.listdir(OUT)):
    print(f)
