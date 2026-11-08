# -*- coding: utf-8 -*-
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB, OUT, OUT_CHARTS, OUT_CARDS
# -*- coding: utf-8 -*-
"""国庆好物节活动复盘：数据计算（作品集用）"""
import json
import pymysql
import pandas as pd



def q(sql):
    with pymysql.connect(**DB) as conn:
        return pd.read_sql(sql, conn)

URL = "'https://api-online/bee/template/activity/10001'"

# ---------- 1. 整体漏斗 ----------
overall = q(f"""
SELECT
 (SELECT COUNT(DISTINCT userid) FROM online_activity_resource_detail WHERE click_or_expose='expose' AND target_url={URL}) expose_users,
 (SELECT COUNT(*)              FROM online_activity_resource_detail WHERE click_or_expose='expose' AND target_url={URL}) expose_rows,
 (SELECT COUNT(DISTINCT userid) FROM online_activity_resource_detail WHERE click_or_expose='click'  AND target_url={URL}) click_users,
 (SELECT COUNT(*)              FROM online_activity_resource_detail WHERE click_or_expose='click'  AND target_url={URL}) click_rows,
 (SELECT COUNT(DISTINCT userid) FROM online_activity_join_detail  WHERE aid='10001') join_users,
 (SELECT COUNT(distinct userid) FROM online_activity_reach_detail WHERE aid='10001') reach_users,
 (SELECT COUNT(*)              FROM online_activity_reach_detail WHERE aid='10001') reach_rows
""")
print("OVERALL\n", overall.T)

# 严格嵌套
nested = q(f"""
WITH e AS (SELECT DISTINCT userid FROM online_activity_resource_detail WHERE click_or_expose='expose' AND target_url={URL}),
     c AS (SELECT DISTINCT userid FROM online_activity_resource_detail WHERE click_or_expose='click' AND target_url={URL}),
     j AS (SELECT DISTINCT userid FROM online_activity_join_detail WHERE aid='10001'),
     r AS (SELECT DISTINCT userid FROM online_activity_reach_detail WHERE aid='10001')
SELECT (SELECT COUNT(*) FROM e) lv1,
       (SELECT COUNT(*) FROM e JOIN c USING(userid)) lv2,
       (SELECT COUNT(*) FROM e JOIN c USING(userid) JOIN j USING(userid)) lv3,
       (SELECT COUNT(*) FROM e JOIN c USING(userid) JOIN j USING(userid) JOIN r USING(userid)) lv4
""")
print("NESTED\n", nested)

# ---------- 2. 每日漏斗 ----------
daily = q(f"""
SELECT d.day,
  MAX(CASE WHEN d.src='expose' THEN 1 ELSE 0 END) ignored,
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
) d
GROUP BY d.day ORDER BY d.day
""").drop(columns=["ignored"])
print("DAILY\n", daily.to_string())

# ---------- 3. 资源位 ----------
resource = q(f"""
SELECT res_location,
  COUNT(DISTINCT CASE WHEN click_or_expose='expose' THEN userid END) expose_users,
  COUNT(DISTINCT CASE WHEN click_or_expose='click'  THEN userid END) click_users,
  COUNT(DISTINCT CASE WHEN click_or_expose='click'  THEN userid END)
    / COUNT(DISTINCT CASE WHEN click_or_expose='expose' THEN userid END) ctr
FROM online_activity_resource_detail
WHERE target_url={URL}
GROUP BY res_location ORDER BY expose_users DESC
""")
print("RESOURCE\n", resource.to_string())

# ---------- 4. 时段 ----------
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
) h
GROUP BY h.hour_of_day ORDER BY h.hour_of_day
""")
# 补齐 0-23
hourly = hourly.set_index("hour_of_day").reindex(range(24), fill_value=0).reset_index()
print("HOURLY\n", hourly.to_string())

# ---------- 5. 用户画像（去重取最新） ----------
dim_cols = ["gender", "age_new", "city_line", "platform", "create_period"]
info = q("""
SELECT userid, gender, age_new, city_line, platform, DATE_FORMAT(createday,'%Y') create_period
FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY userid ORDER BY createday DESC) rn
  FROM app_user_info
) t WHERE rn=1
""")
join_u = q("SELECT DISTINCT userid FROM online_activity_join_detail WHERE aid='10001'")
reach_u = q("SELECT DISTINCT userid FROM online_activity_reach_detail WHERE aid='10001'")
info["is_join"] = info.userid.isin(join_u.userid)
info["is_reach"] = info.userid.isin(reach_u.userid)

profiles = {}
for col in dim_cols:
    g = info.groupby(col).agg(total=("userid", "count"),
                              join=("is_join", "sum"),
                              reach=("is_reach", "sum")).reset_index()
    g["join_rate"] = g["join"] / g["total"]
    g["reach_rate"] = g["reach"] / g["total"]
    profiles[col] = g
    print(f"PROFILE {col}\n", g.to_string())

# 画像覆盖率（在 user_info 中的参与用户）
print("join users in info:", info.is_join.sum(), " reach users in info:", info.is_reach.sum())

out = dict(
    overall=overall.iloc[0].to_dict(),
    nested=nested.iloc[0].to_dict(),
    daily=daily.to_dict("records"),
    resource=resource.to_dict("records"),
    hourly=hourly.to_dict("records"),
    profiles={k: v.to_dict("records") for k, v in profiles.items()},
)
with open(str(OUT / "summary.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2, default=float)
print("saved summary.json")
