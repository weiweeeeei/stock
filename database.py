"""
數據庫層 - SQLite 存儲每日數據，供趨勢分析用
每次執行後數據累積，計算連續法人買賣超、技術指標等
"""

import sqlite3
import json
from pathlib import Path
from datetime import date, timedelta
from typing import Optional

DB_PATH = Path(__file__).parent / "db" / "twstock.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建立資料表（若不存在）"""
    conn = get_conn()
    conn.executescript("""
        -- 每日個股收盤
        CREATE TABLE IF NOT EXISTS daily_price (
            date        TEXT NOT NULL,
            code        TEXT NOT NULL,
            name        TEXT,
            close       REAL,
            change      REAL,
            change_pct  REAL,
            volume      INTEGER,
            open        REAL,
            high        REAL,
            low         REAL,
            PRIMARY KEY (date, code)
        );

        -- 每日三大法人
        CREATE TABLE IF NOT EXISTS daily_institutional (
            date        TEXT NOT NULL,
            code        TEXT NOT NULL,
            name        TEXT,
            foreign_net INTEGER DEFAULT 0,
            trust_net   INTEGER DEFAULT 0,
            dealer_net  INTEGER DEFAULT 0,
            total_net   INTEGER DEFAULT 0,
            PRIMARY KEY (date, code)
        );

        -- 每日產業指數
        CREATE TABLE IF NOT EXISTS daily_sector (
            date        TEXT NOT NULL,
            sector      TEXT NOT NULL,
            market      TEXT DEFAULT 'TWSE',
            close       REAL,
            change_pct  REAL,
            PRIMARY KEY (date, sector, market)
        );

        -- 每月營收
        CREATE TABLE IF NOT EXISTS monthly_revenue (
            year_month  TEXT NOT NULL,
            code        TEXT NOT NULL,
            name        TEXT,
            revenue     INTEGER,
            yoy_pct     REAL,
            mom_pct     REAL,
            PRIMARY KEY (year_month, code)
        );

        -- 大盤每日紀錄
        CREATE TABLE IF NOT EXISTS daily_market (
            date        TEXT PRIMARY KEY,
            taiex_close REAL,
            taiex_change REAL,
            taiex_change_pct REAL,
            foreign_net_b REAL,
            trust_net_b   REAL,
            dealer_net_b  REAL,
            margin_balance INTEGER,
            short_balance  INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_price_code ON daily_price(code, date);
        CREATE INDEX IF NOT EXISTS idx_inst_code  ON daily_institutional(code, date);
    """)
    conn.commit()
    conn.close()


def save_market_data(market_data: dict):
    """儲存當日所有市場數據"""
    conn = get_conn()
    date_str = market_data["date"]
    # 轉換日期格式 YYYYMMDD → YYYY-MM-DD
    d = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"

    # 大盤
    taiex = market_data.get("taiex", {})
    inst  = market_data.get("institutional_summary", {})
    margin = market_data.get("margin", {})

    def safe_float(v):
        try:
            return float(str(v).replace(",","").replace("%","").replace("+",""))
        except:
            return None

    conn.execute("""
        INSERT OR REPLACE INTO daily_market
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        d,
        safe_float(taiex.get("close")),
        safe_float(taiex.get("change")),
        safe_float(taiex.get("change_pct")),
        inst.get("foreign_net_billion"),
        inst.get("trust_net_billion"),
        inst.get("dealer_net_billion"),
        safe_float(str(margin.get("margin_balance","")).replace(",","")),
        safe_float(str(margin.get("short_balance","")).replace(",","")),
    ))

    # 個股價格
    for s in market_data.get("stocks_twse", []) + market_data.get("stocks_tpex", []):
        conn.execute("""
            INSERT OR REPLACE INTO daily_price
            (date,code,name,close,change,change_pct,volume,open,high,low)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            d, s.get("code",""), s.get("name",""),
            safe_float(s.get("close")),
            safe_float(s.get("change")),
            safe_float(s.get("change_pct","0%").replace("%","")),
            safe_float(str(s.get("volume","0")).replace(",","")),
            safe_float(s.get("open")),
            safe_float(s.get("high")),
            safe_float(s.get("low")),
        ))

    # 三大法人
    for s in market_data.get("institutional_twse", []):
        conn.execute("""
            INSERT OR REPLACE INTO daily_institutional
            (date,code,name,foreign_net,trust_net,dealer_net,total_net)
            VALUES (?,?,?,?,?,?,?)
        """, (
            d, s.get("code",""), s.get("name",""),
            s.get("foreign_net",0), s.get("trust_net",0),
            s.get("dealer_net",0), s.get("total_net",0),
        ))

    # 產業指數
    for s in market_data.get("sector_twse", []):
        conn.execute("""
            INSERT OR REPLACE INTO daily_sector
            (date,sector,market,close,change_pct)
            VALUES (?,?,?,?,?)
        """, (
            d, s.get("sector",""), "TWSE",
            safe_float(s.get("close")),
            safe_float(s.get("change_pct","0%").replace("%","")),
        ))

    conn.commit()
    conn.close()


# ── 趨勢計算函數 ──────────────────────────────────────────────────────────────

def get_institutional_trend(code: str, days: int = 10) -> dict:
    """
    取得個股最近 N 日法人買賣超趨勢
    回傳：{
      consecutive_foreign_buy: 連續外資買超天數,
      total_foreign_5d: 近5日外資合計,
      total_foreign_10d: 近10日外資合計,
      trust_5d: 近5日投信合計,
      trend: "持續買超/持續賣超/混合"
    }
    """
    conn = get_conn()
    rows = conn.execute("""
        SELECT date, foreign_net, trust_net, dealer_net, total_net
        FROM daily_institutional
        WHERE code = ?
        ORDER BY date DESC
        LIMIT ?
    """, (code, days)).fetchall()
    conn.close()

    if not rows:
        return {"consecutive_foreign_buy": 0, "total_foreign_5d": 0,
                "total_foreign_10d": 0, "trust_5d": 0, "trend": "無資料"}

    # 連續外資買超天數
    consecutive = 0
    for r in rows:
        if r["foreign_net"] > 0:
            consecutive += 1
        else:
            break

    foreign_vals = [r["foreign_net"] for r in rows]
    trust_vals   = [r["trust_net"]   for r in rows]

    total_f5  = sum(foreign_vals[:5])
    total_f10 = sum(foreign_vals[:10])
    total_t5  = sum(trust_vals[:5])

    buy_days  = sum(1 for v in foreign_vals[:5] if v > 0)
    sell_days = sum(1 for v in foreign_vals[:5] if v < 0)

    if buy_days >= 4:
        trend = "持續買超"
    elif sell_days >= 4:
        trend = "持續賣超"
    else:
        trend = "多空混合"

    return {
        "consecutive_foreign_buy": consecutive,
        "total_foreign_5d":  total_f5,
        "total_foreign_10d": total_f10,
        "trust_5d":          total_t5,
        "trend":             trend,
        "days_available":    len(rows),
    }


def get_price_history(code: str, days: int = 60) -> list[dict]:
    """取得個股歷史價格（供技術指標計算用）"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT date, close, volume, high, low, open
        FROM daily_price
        WHERE code = ? AND close IS NOT NULL
        ORDER BY date ASC
        LIMIT ?
    """, (code, days)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_sector_trend(sector: str, days: int = 5) -> dict:
    """取得產業指數近 N 日趨勢"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT date, change_pct
        FROM daily_sector
        WHERE sector = ?
        ORDER BY date DESC
        LIMIT ?
    """, (sector, days)).fetchall()
    conn.close()

    if not rows:
        return {"avg_pct": 0, "up_days": 0, "trend": "無資料"}

    vals = [r["change_pct"] for r in rows if r["change_pct"] is not None]
    up   = sum(1 for v in vals if v > 0)
    return {
        "avg_pct":  round(sum(vals)/len(vals), 2) if vals else 0,
        "up_days":  up,
        "trend":    "強勢" if up >= 3 else ("弱勢" if up <= 1 else "震盪"),
        "days":     len(vals),
    }


def get_market_trend(days: int = 5) -> dict:
    """大盤近 N 日趨勢"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT date, taiex_close, taiex_change_pct,
               foreign_net_b, trust_net_b, margin_balance
        FROM daily_market
        ORDER BY date DESC
        LIMIT ?
    """, (days,)).fetchall()
    conn.close()

    if not rows:
        return {}

    up_days     = sum(1 for r in rows if (r["taiex_change_pct"] or 0) > 0)
    foreign_5d  = sum((r["foreign_net_b"] or 0) for r in rows)
    trust_5d    = sum((r["trust_net_b"]   or 0) for r in rows)

    return {
        "taiex_latest":  rows[0]["taiex_close"],
        "up_days_5d":    up_days,
        "foreign_5d_b":  round(foreign_5d, 1),
        "trust_5d_b":    round(trust_5d, 1),
        "market_bias":   "偏多" if up_days >= 3 and foreign_5d > 0 else
                         "偏空" if up_days <= 1 else "震盪",
        "days_available": len(rows),
    }
