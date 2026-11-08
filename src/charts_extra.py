# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB, OUT, OUT_CHARTS, OUT_CARDS
# -*- coding: utf-8 -*-
"""国庆好物节独立作品集：补充图表 gq7~gq10"""
import os
import pymysql
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
OUT = str(OUT_CHARTS)

URL = "'https://api-online/bee/template/activity/10001'"
EXP, CLK, JOIN, RCH, GRAY, RED = "#1f4e79", "#2e86c1", "#f39c12", "#27ae60", "#95a5a6", "#c0392b"

def q(sql):
    with pymysql.connect(**DB) as conn:
        return pd.read_sql(sql, conn)

def style(ax):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e8edf3", linewidth=0.8)
    ax.set_axisbelow(True)

# ---------- 7 曝光-参与相关性 ----------
hourly = q(f"""
SELECT h.hour_of_day,
  COUNT(DISTINCT CASE WHEN h.src='expose' THEN h.userid END) expose_users,
  COUNT(DISTINCT CASE WHEN h.src='join'   THEN h.userid END) join_users
FROM (
  SELECT HOUR(event_time) hour_of_day,'expose' src,userid FROM online_activity_resource_detail WHERE click_or_expose='expose' AND target_url={URL}
  UNION ALL
  SELECT HOUR(join_time),'join',userid FROM online_activity_join_detail WHERE aid='10001'
) h GROUP BY h.hour_of_day ORDER BY h.hour_of_day
""")
slope, intercept = np.polyfit(hourly.expose_users, hourly.join_users, 1)
corr = hourly.expose_users.corr(hourly.join_users)
fig, ax = plt.subplots(figsize=(7.6, 4.2), dpi=170)
ax.scatter(hourly.expose_users, hourly.join_users, s=46, color=EXP, alpha=0.8, edgecolor="white", linewidth=0.8, zorder=3)
xs = np.linspace(hourly.expose_users.min(), hourly.expose_users.max(), 100)
ax.plot(xs, slope * xs + intercept, color=RED, lw=1.8, label=f"线性拟合  y = {slope:.4f}x {intercept:+.1f}")
ax.set_xlabel("小时曝光用户数", fontsize=10)
ax.set_ylabel("小时参与用户数", fontsize=10)
ax.set_title(f"曝光量与参与量的正相关（r = {corr:.3f}）", fontsize=13, fontweight="bold", color=EXP, loc="left")
style(ax)
ax.legend(fontsize=9, frameon=False, loc="upper left")
ax.text(0.98, 0.08, "按拟合：2,000 人参与 ≈ 20 万曝光", transform=ax.transAxes,
        ha="right", fontsize=10, color=RED, fontweight="bold")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq7_corr.png"), facecolor="white")
plt.close()

# ---------- 8 活动前后活跃分布 ----------
ju = q("SELECT DISTINCT userid FROM online_activity_join_detail WHERE aid='10001'")
act = q(f"""
SELECT userid,
  SUM(CASE WHEN activeday BETWEEN '2080-09-14' AND '2080-09-27' THEN CAST(activenum AS DECIMAL(10,2)) ELSE 0 END)/14 pre,
  SUM(CASE WHEN activeday BETWEEN '2080-09-28' AND '2080-10-11' THEN CAST(activenum AS DECIMAL(10,2)) ELSE 0 END)/14 dur
FROM app_user_active WHERE userid IN (SELECT userid FROM online_activity_join_detail WHERE aid='10001')
GROUP BY userid
""")
bins = [0, 2, 4, 8, 15, 999]
labels = ["[0,2]", "(2,4]", "(4,8]", "(8,15]", ">15"]
act["pre_bin"] = pd.cut(act.pre, bins=bins, labels=labels, include_lowest=True, right=True)
act["dur_bin"] = pd.cut(act.dur, bins=bins, labels=labels, include_lowest=True, right=True)
pre = act.pre_bin.value_counts().reindex(labels) / len(act) * 100
dur = act.dur_bin.value_counts().reindex(labels) / len(act) * 100
fig, ax = plt.subplots(figsize=(7.8, 4.0), dpi=170)
x = np.arange(len(labels)); w = 0.36
b1 = ax.bar(x - w/2, pre, w, color="#a9c4dd", label="活动前 14 天")
b2 = ax.bar(x + w/2, dur, w, color=EXP, label="活动中 14 天")
for i in range(len(labels)):
    ax.text(x[i]-w/2, pre.iloc[i]+1.2, f"{pre.iloc[i]:.1f}%", ha="center", fontsize=9)
    ax.text(x[i]+w/2, dur.iloc[i]+1.2, f"{dur.iloc[i]:.1f}%", ha="center", fontsize=9, fontweight="bold")
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_xlabel("人均日活跃次数区间", fontsize=10)
ax.set_ylabel("用户占比 (%)", fontsize=10)
ax.set_ylim(0, 80)
ax.set_title(f"参与用户：活动前后日活跃频次分布（均值 {act.pre.mean():.2f} → {act.dur.mean():.2f}）", fontsize=12.5, fontweight="bold", color=EXP, loc="left")
style(ax)
ax.legend(fontsize=9, frameon=False, loc="upper right")
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq8_activity.png"), facecolor="white")
plt.close()
print("mean pre/dur:", round(act.pre.mean(), 3), round(act.dur.mean(), 3), "n:", len(act))

# ---------- 9 参与但未达标画像 ----------
un = q(f"""
SELECT u.gender, u.age_new, u.city_line
FROM (SELECT DISTINCT userid FROM online_activity_join_detail WHERE aid='10001') j
JOIN (SELECT userid, gender, age_new, city_line FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY userid ORDER BY createday DESC) rn FROM app_user_info) t WHERE rn=1) u
  ON j.userid = u.userid
WHERE j.userid NOT IN (SELECT userid FROM online_activity_reach_detail WHERE aid='10001')
""")
fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.5), dpi=170)
for ax, col, title in zip(axes, ["gender", "age_new"], ["性别", "年龄"]):
    if col == "age_new":
        order = ["[0,14]", "[15,25]", "[26,35]", "[36,50]", "[51,70]", ">70"]
        g = un[col].value_counts().reindex(order).dropna()
    else:
        g = un[col].value_counts().sort_index()
    xs = np.arange(len(g))
    ax.bar(xs, g.values, color=CLK, width=0.55)
    for i, v in enumerate(g.values):
        ax.text(i, v + 0.8, f"{v} ({v/len(un):.0%})", ha="center", fontsize=9)
    ax.set_xticks(xs); ax.set_xticklabels(g.index, fontsize=9.5)
    ax.set_title(f"参与未达标用户：{title}分布（n={len(un)}）", fontsize=11.5, fontweight="bold", color=EXP, loc="left")
    ax.set_ylabel("用户数", fontsize=9)
    ax.set_ylim(0, max(g.values) * 1.28)
    style(ax)
plt.tight_layout(pad=1.2)
plt.savefig(os.path.join(OUT, "gq9_unreached.png"), facecolor="white")
plt.close()

# ---------- 10 达标用户参与日期分布 ----------
rd = q("""
SELECT j.join_day day, COUNT(DISTINCT j.userid) users
FROM online_activity_join_detail j
WHERE j.aid='10001' AND j.userid IN (SELECT userid FROM online_activity_reach_detail WHERE aid='10001')
GROUP BY j.join_day ORDER BY j.join_day
""")
fig, ax = plt.subplots(figsize=(9.2, 3.8), dpi=170)
colors = [RED if d == "2080-10-01" else EXP for d in rd.day]
ax.bar(np.arange(len(rd)), rd.users, color=colors, width=0.62)
for i, v in enumerate(rd.users):
    ax.text(i, v + 2, str(v), ha="center", fontsize=8.5)
ax.set_xticks(np.arange(len(rd)))
ax.set_xticklabels([d[5:] for d in rd.day], fontsize=9)
ax.set_xlabel("参与日期（2080 年）", fontsize=10)
ax.set_ylabel("达标用户数", fontsize=10)
ax.set_title("达标用户的参与日期分布：10-01 一天贡献 192 人（占 48.5%）", fontsize=12.5, fontweight="bold", color=EXP, loc="left")
style(ax)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq10_reachday.png"), facecolor="white")
plt.close()
print(rd.to_string())

# ---------- 11 A/B 效应量森林图 ----------
metrics = ["活动参与率\n（主指标）", "活动页到达标转化率\n（辅助指标）", "券后退款/取消率\n（护栏指标）"]
diff = [3.36, 3.14, 0.31]
lo = [1.45, 1.36, -1.83]
hi = [5.26, 4.92, 2.45]
pvals = ["p = 0.00056", "p = 0.00055", "p = 0.7765"]
colors = [EXP, CLK, GRAY]
fig, ax = plt.subplots(figsize=(8.2, 3.8), dpi=170)
y = np.arange(len(metrics))[::-1]
for i, (m, d, l, h, pv, c) in enumerate(zip(metrics, diff, lo, hi, pvals, colors)):
    ax.plot([l, h], [y[i], y[i]], color=c, lw=2.6, solid_capstyle="round")
    ax.scatter([d], [y[i]], s=90, color=c, zorder=3, edgecolor="white", linewidth=1.2)
    ax.text(h + 0.18, y[i], f"{d:+.2f}pp  {pv}", va="center", fontsize=9.5, color=c, fontweight="bold")
ax.axvline(0, color="#888", ls="--", lw=1.1)
ax.set_yticks(y); ax.set_yticklabels(metrics, fontsize=10)
ax.set_xlim(-3.2, 9.6)
ax.set_xlabel("实验组 − 对照组（百分点，95% 置信区间）", fontsize=10)
ax.set_title("三项指标的效应量与 95% 置信区间", fontsize=13, fontweight="bold", color=EXP, loc="left")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="x", color="#e8edf3", linewidth=0.8); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(os.path.join(OUT, "gq11_ab_forest.png"), facecolor="white")
plt.close()
print("done")
