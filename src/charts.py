# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB, OUT, OUT_CHARTS, OUT_CARDS
# -*- coding: utf-8 -*-
"""生成国庆好物节作品集图表 -> portfolio/img/gq_*.png"""
import os
import pymysql
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT = str(OUT_CHARTS)
URL = "'https://api-online/bee/template/activity/10001'"

def q(sql):
    with pymysql.connect(**DB) as conn:
        return pd.read_sql(sql, conn)

EXP, CLK, JOIN, RCH, GRAY, RED = "#1f4e79", "#2e86c1", "#f39c12", "#27ae60", "#95a5a6", "#c0392b"

def style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e8edf3", linewidth=0.8)
    ax.set_axisbelow(True)

# ---------- 1 漏斗 ----------
labels = ["曝光", "点击", "参与", "达标"]
vals = [22572, 1907, 489, 396]
conv = [None, 1907/22572, 489/1907, 396/489]
fig, ax = plt.subplots(figsize=(9, 4.6), dpi=170)
y = np.arange(len(vals))[::-1]
bars = ax.barh(y, vals, color=[EXP, CLK, JOIN, RCH], height=0.58)
for i, (v, b) in enumerate(zip(vals, bars)):
    ax.text(v + 350, b.get_y() + b.get_height()/2, f"{v:,}", va="center",
            fontsize=13, fontweight="bold", color="#1a1a1a")
    if conv[i] is not None:
        ax.text(v + 2600, b.get_y() + b.get_height()/2, f"→ {conv[i]:.2%}",
                va="center", fontsize=11, color="#666")
ax.set_yticks(y)
ax.set_yticklabels(labels, fontsize=13)
ax.set_xlim(0, 30500)
ax.set_xlabel("去重用户数", fontsize=11)
ax.xaxis.set_major_formatter(FuncFormatter(lambda x, p: f"{int(x/1000)}k" if x else "0"))
ax.set_title("活动四层转化漏斗（用户级去重口径）", fontsize=14, fontweight="bold", color=EXP, loc="left")
style(ax)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq1_funnel.png"), facecolor="white")
plt.close()

# ---------- 2 每日趋势 ----------
daily = q(f"""
SELECT d.day,
  COUNT(DISTINCT CASE WHEN d.src='expose' THEN d.userid END) expose_users,
  COUNT(DISTINCT CASE WHEN d.src='click'  THEN d.userid END) click_users,
  COUNT(DISTINCT CASE WHEN d.src='join'   THEN d.userid END) join_users,
  COUNT(DISTINCT CASE WHEN d.src='reach'  THEN d.userid END) reach_users
FROM (
  SELECT activeday day,'expose' src,userid FROM online_activity_resource_detail WHERE click_or_expose='expose' AND target_url={URL}
  UNION ALL
  SELECT activeday,'click',userid FROM online_activity_resource_detail WHERE click_or_expose='click' AND target_url={URL}
  UNION ALL
  SELECT join_day,'join',userid FROM online_activity_join_detail WHERE aid='10001'
  UNION ALL
  SELECT reach_day,'reach',userid FROM online_activity_reach_detail WHERE aid='10001'
) d GROUP BY d.day ORDER BY d.day
""")
x = np.arange(len(daily))
fig, axes = plt.subplots(2, 1, figsize=(10, 5.6), dpi=170, sharex=True,
                         gridspec_kw={"height_ratios": [1, 1]})
ax = axes[0]
ax.bar(x, daily.expose_users, color=EXP, width=0.62, label="曝光用户")
ax.set_ylabel("曝光用户", fontsize=10)
style(ax)
ax2 = ax.twinx()
ax2.plot(x, daily.click_users, color=RED, marker="o", ms=3, lw=1.8, label="点击用户")
ax2.set_ylabel("点击用户", fontsize=10, color=RED)
ax2.tick_params(axis="y", colors=RED)
ax2.spines["top"].set_visible(False)
ax.set_title("每日曝光与点击", fontsize=11.5, fontweight="bold", color=EXP, loc="left")

ax = axes[1]
ax.bar(x, daily.join_users, color=JOIN, width=0.62, label="参与用户")
ax.set_ylabel("参与用户", fontsize=10)
style(ax)
ax2 = ax.twinx()
ax2.plot(x, daily.reach_users, color=RCH, marker="o", ms=3, lw=1.8, label="达标用户")
ax2.set_ylabel("达标用户", fontsize=10, color=RCH)
ax2.tick_params(axis="y", colors=RCH)
ax2.spines["top"].set_visible(False)
ax.set_title("每日参与与达标", fontsize=11.5, fontweight="bold", color=EXP, loc="left")
ax.set_xticks(x)
ax.set_xticklabels([d[5:] for d in daily.day], fontsize=9)
ax.set_xlabel("日期（2080 年）", fontsize=10)

for a in axes:
    for i in [3, 10]:  # 10-01, 10-08
        a.axvline(i, color=GRAY, ls="--", lw=0.9, alpha=0.8)
box = dict(facecolor="white", alpha=0.85, edgecolor="none", pad=1.5)
axes[0].text(3.4, 0.94, "10-01 国庆当天\n点击 672", transform=axes[0].get_xaxis_transform(),
             fontsize=8.5, color="#555", va="top", bbox=box)
axes[0].text(10.4, 0.94, "10-08 二次高峰\n点击 552", transform=axes[0].get_xaxis_transform(),
             fontsize=8.5, color="#555", va="top", bbox=box)
plt.tight_layout(pad=1.2)
plt.savefig(os.path.join(OUT, "gq2_daily.png"), facecolor="white")
plt.close()

# ---------- 3 资源位 ----------
res = q(f"""
SELECT res_location,
  COUNT(DISTINCT CASE WHEN click_or_expose='expose' THEN userid END) expose_users,
  COUNT(DISTINCT CASE WHEN click_or_expose='click'  THEN userid END) click_users
FROM online_activity_resource_detail WHERE target_url={URL}
GROUP BY res_location ORDER BY expose_users ASC
""")
res["ctr"] = res.click_users / res.expose_users
short = {"首页-通栏单帧推广位/首页—首页图文": "首页图文",
         "发现-热门活动": "发现-热门活动",
         "首页-首页广告弹窗/首页—首页弹窗": "首页弹窗",
         "首页-开机大屏": "开机大屏"}
res["name"] = res.res_location.map(short)
fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), dpi=170)
y = np.arange(len(res))
axes[0].barh(y, res.expose_users, color=EXP, height=0.55)
for i, v in enumerate(res.expose_users):
    axes[0].text(v + 250, i, f"{v:,}", va="center", fontsize=10)
axes[0].set_yticks(y); axes[0].set_yticklabels(res.name, fontsize=11)
axes[0].set_xlim(0, 21500)
axes[0].set_title("各资源位曝光用户", fontsize=12, fontweight="bold", color=EXP, loc="left")
style(axes[0])

colors = [RED if v > 0.3 else CLK for v in res.ctr]
axes[1].barh(y, res.ctr * 100, color=colors, height=0.55)
for i, v in enumerate(res.ctr):
    axes[1].text(v * 100 + 1.5, i, f"{v:.1%}", va="center", fontsize=10, fontweight="bold")
axes[1].set_yticks(y); axes[1].set_yticklabels(res.name, fontsize=11)
axes[1].set_xlim(0, 108)
axes[1].set_xlabel("点击率（点击用户 / 曝光用户）", fontsize=10)
axes[1].set_title("各资源位点击率", fontsize=12, fontweight="bold", color=EXP, loc="left")
style(axes[1])
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq3_resource.png"), facecolor="white")
plt.close()

# ---------- 4 时段 ----------
hourly = q(f"""
SELECT h.hour_of_day,
  COUNT(DISTINCT CASE WHEN h.src='expose' THEN h.userid END) expose_users,
  COUNT(DISTINCT CASE WHEN h.src='click'  THEN h.userid END) click_users,
  COUNT(DISTINCT CASE WHEN h.src='join'   THEN h.userid END) join_users
FROM (
  SELECT HOUR(event_time) hour_of_day,'expose' src,userid FROM online_activity_resource_detail WHERE click_or_expose='expose' AND target_url={URL}
  UNION ALL
  SELECT HOUR(event_time),'click',userid FROM online_activity_resource_detail WHERE click_or_expose='click' AND target_url={URL}
  UNION ALL
  SELECT HOUR(join_time),'join',userid FROM online_activity_join_detail WHERE aid='10001'
) h GROUP BY h.hour_of_day ORDER BY h.hour_of_day
""").set_index("hour_of_day").reindex(range(24), fill_value=0).reset_index()
hourly["ctr"] = hourly.click_users / hourly.expose_users.replace(0, np.nan)
fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.6), dpi=170)
ax = axes[0]
ax.bar(hourly.hour_of_day, hourly.expose_users, color="#c9d8ea", width=0.72, label="曝光用户")
ax.set_xlabel("小时", fontsize=10); ax.set_ylabel("曝光用户", fontsize=10, color=EXP)
ax.set_xticks(range(0, 24, 2))
style(ax)
ax2 = ax.twinx()
ax2.plot(hourly.hour_of_day, hourly.join_users, color=JOIN, marker="o", ms=3, lw=1.8, label="参与用户")
ax2.set_ylabel("参与用户", fontsize=10, color=JOIN)
ax2.tick_params(axis="y", colors=JOIN); ax2.spines["top"].set_visible(False)
ax.set_title("曝光与参与的小时分布", fontsize=12, fontweight="bold", color=EXP, loc="left")

ax = axes[1]
ax.plot(hourly.hour_of_day, hourly.ctr * 100, color=RED, marker="o", ms=3.5, lw=1.9)
ax.fill_between(hourly.hour_of_day, hourly.ctr * 100, color=RED, alpha=0.10)
ax.set_xticks(range(0, 24, 2))
ax.set_xlabel("小时", fontsize=10); ax.set_ylabel("点击率 (%)", fontsize=10)
ax.set_title("小时点击率", fontsize=12, fontweight="bold", color=EXP, loc="left")
style(ax)
peak = hourly.loc[hourly.ctr.idxmax()]
ax.annotate(f"0 点 {peak.ctr:.1%}\n曝光量小，参考意义有限",
            xy=(peak.hour_of_day, peak.ctr*100),
            xytext=(peak.hour_of_day + 2.2, peak.ctr*100 - 1.2), fontsize=8.5, color="#555",
            va="top", arrowprops=dict(arrowstyle="->", color="#999", lw=0.8))
fig.subplots_adjust(left=0.09, right=0.93, top=0.86, bottom=0.19, wspace=0.40)
plt.savefig(os.path.join(OUT, "gq4_hourly.png"), facecolor="white")
plt.close()

# ---------- 5 画像 ----------
info = q("""
SELECT userid, gender, age_new, city_line, platform, DATE_FORMAT(createday,'%Y') create_period
FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY userid ORDER BY createday DESC) rn
      FROM app_user_info) t WHERE rn=1
""")
ju = q("SELECT DISTINCT userid FROM online_activity_join_detail WHERE aid='10001'")
info["is_join"] = info.userid.isin(ju.userid)

def rate_tab(col, order=None):
    g = info.groupby(col).agg(total=("userid", "count"), join=("is_join", "sum")).reset_index()
    g["rate"] = g["join"] / g["total"]
    g = g[g.total >= 50]
    if order:
        g["o"] = g[col].map({v: i for i, v in enumerate(order)})
        g = g.sort_values("o")
    return g

fig, axes = plt.subplots(1, 3, figsize=(12, 3.5), dpi=170)
panels = [
    ("platform", rate_tab("platform"), "平台"),
    ("age_new", rate_tab("age_new"), "年龄"),
    ("create_period", rate_tab("create_period"), "注册年份"),
]
for ax, (col, g, title) in zip(axes, panels):
    if col == "create_period":
        xs = np.arange(len(g))
        ax.plot(xs, g.rate * 100, color=EXP, marker="o", ms=4, lw=1.8)
        ax.set_xticks(xs); ax.set_xticklabels(g[col], fontsize=9)
    else:
        xs = np.arange(len(g))
        bars = ax.bar(xs, g.rate * 100, color=[EXP if i == 0 else CLK for i in range(len(g))], width=0.55)
        ax.set_xticks(xs); ax.set_xticklabels(g[col], fontsize=9)
        for i, v in enumerate(g.rate):
            ax.text(i, v * 100 + 1.2, f"{v:.0%}", ha="center", fontsize=9, fontweight="bold")
    ax.set_title(f"{title}：样本内参与率", fontsize=11.5, fontweight="bold", color=EXP, loc="left")
    ax.set_ylabel("参与率 (%)", fontsize=9)
    ax.set_ylim(0, 72)
    style(ax)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq5_profile.png"), facecolor="white")
plt.close()

# ---------- 6 A/B ----------
metrics = ["活动参与率", "到达标转化率"]
control = [25.64, 20.79]
treat = [29.00, 23.93]
pvals = ["p = 0.00056", "p = 0.00055"]
fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=170)
x = np.arange(len(metrics)); w = 0.32
b1 = ax.bar(x - w/2, control, w, color="#a9c4dd", label="对照组（原权益展示）")
b2 = ax.bar(x + w/2, treat, w, color=EXP, label="实验组（差异化权益包）")
for i in range(len(metrics)):
    ax.text(x[i] - w/2, control[i] + 0.7, f"{control[i]:.2f}%", ha="center", fontsize=10)
    ax.text(x[i] + w/2, treat[i] + 0.7, f"{treat[i]:.2f}%", ha="center", fontsize=10, fontweight="bold")
    ax.text(x[i], max(control[i], treat[i]) + 3.2, f"+{treat[i]-control[i]:.2f}pp\n{pvals[i]}",
            ha="center", fontsize=9.5, color=RED, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(metrics, fontsize=11)
ax.set_ylabel("转化率 (%)", fontsize=10)
ax.set_ylim(0, 40)
ax.set_title("A/B 实验结果：实验组两项转化指标均显著提升", fontsize=12, fontweight="bold", color=EXP, loc="left")
style(ax)
ax.legend(fontsize=9, frameon=False, loc="upper right")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq6_ab.png"), facecolor="white")
plt.close()

print("charts saved to", OUT)
