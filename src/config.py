# -*- coding: utf-8 -*-
"""项目统一配置：数据库连接与输出路径。"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
OUT_CHARTS = OUT / "charts"
OUT_CARDS = OUT / "cards"
for _p in (OUT_CHARTS, OUT_CARDS):
    _p.mkdir(parents=True, exist_ok=True)

# 数据库连接全部走环境变量，仓库内不保存任何密码
DB = dict(
    host=os.getenv("MYSQL_HOST", "localhost"),
    port=int(os.getenv("MYSQL_PORT", "3306")),
    user=os.getenv("MYSQL_USER", "root"),
    password=os.getenv("MYSQL_PASSWORD", ""),
    database=os.getenv("MYSQL_DB", "campaign_analysis"),
    charset="utf8mb4",
)
