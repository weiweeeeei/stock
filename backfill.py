"""
歷史資料回填腳本（一次性）

cache bug 修正前，SQLite 從未跨天累積，導致族群輪動、技術指標長期無資料。
本腳本把過去 N 個交易日的真實股價＋三大法人灌進資料庫，讓系統「補課」。

效率：每檔股票各抓「一次」區間（價格 1 次、法人 1 次），
      218 檔 × 2 ≈ 436 次呼叫，落在 FinMind 免費額度（600/小時）內。

只灌「原始資料」（daily_price / daily_institutional / daily_market），
不回算歷史族群分數——族群輪動由往後的正常執行自然累積，確保前後用同一套公式比較。

用法：python backfill.py [天數，預設 90]
"""

import sys
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

from fetcher import _get, MAX_WORKERS
from database import init_db, get_conn
from data.stock_universe import get_all_stocks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def _change_pct(close, prev_close):
    if not prev_close:
        return 0.0
    return (close - prev_close) / prev_close * 100


def _fetch_price_window(code, start, end):
    """回傳 {date: {close, change_pct, volume, open, high, low}}，change 自己用今收−昨收算。"""
    rows = _get("TaiwanStockPrice", data_id=code, start_date=start, end_date=end)
    rows = [r for r in rows if r.get("close") is not None]
    rows.sort(key=lambda r: r["date"])
    out = {}
    for i, r in enumerate(rows):
        close = float(r.get("close") or 0)
        prev = float(rows[i-1].get("close") or 0) if i > 0 else close - float(r.get("spread") or 0)
        out[r["date"]] = {
            "close": close, "change": close - prev, "change_pct": _change_pct(close, prev),
            "volume": int(r.get("Trading_Volume") or 0),
            "open": float(r.get("open") or 0), "high": float(r.get("max") or 0), "low": float(r.get("min") or 0),
        }
    return code, out


def _fetch_inst_window(code, start, end):
    """回傳 {date: {foreign_net, trust_net, dealer_net, total_net}}。"""
    rows = _get("TaiwanStockInstitutionalInvestorsBuySell", data_id=code, start_date=start, end_date=end)
    agg = defaultdict(lambda: {"foreign_net": 0, "trust_net": 0, "dealer_net": 0})
    for r in rows:
        cat = (r.get("name") or "").lower()
        net = int(r.get("buy") or 0) - int(r.get("sell") or 0)
        if "foreign" in cat:
            agg[r["date"]]["foreign_net"] += net
        elif "trust" in cat or "investment" in cat:
            agg[r["date"]]["trust_net"] += net
        elif "dealer" in cat:
            agg[r["date"]]["dealer_net"] += net
    for d in agg:
        v = agg[d]
        v["total_net"] = v["foreign_net"] + v["trust_net"] + v["dealer_net"]
    return code, dict(agg)


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    end = date.today()
    start = end - timedelta(days=days)
    s, e = start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
    log.info(f"回填區間 {s} ~ {e}（約 {days} 日曆天）")

    init_db()
    universe = get_all_stocks()
    names = {c: i["name"] for c, i in universe.items()}

    # ── 1. 並行抓所有個股的價格區間 ──
    log.info(f"[1/3] 抓 {len(universe)} 檔價格區間...")
    prices = {}  # code -> {date: {...}}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(_fetch_price_window, c, s, e) for c in universe]
        for f in as_completed(futs):
            code, data = f.result()
            if data:
                prices[code] = data
    log.info(f"      取得 {len(prices)} 檔")

    # ── 2. 並行抓所有個股的三大法人區間 ──
    log.info(f"[2/3] 抓 {len(universe)} 檔三大法人區間...")
    insts = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = [ex.submit(_fetch_inst_window, c, s, e) for c in universe]
        for f in as_completed(futs):
            code, data = f.result()
            if data:
                insts[code] = data
    log.info(f"      取得 {len(insts)} 檔")

    # ── 3. 寫入 DB ──
    log.info("[3/3] 寫入資料庫...")
    conn = get_conn()
    n_price = n_inst = 0
    market_agg = defaultdict(lambda: {"f": 0, "t": 0, "d": 0})  # date -> 法人合計（股數）

    for code, days_data in prices.items():
        for d, p in days_data.items():
            conn.execute("""INSERT OR REPLACE INTO daily_price
                (date,code,name,close,change,change_pct,volume,open,high,low)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (d, code, names.get(code, ""), p["close"], p["change"], p["change_pct"],
                 p["volume"], p["open"], p["high"], p["low"]))
            n_price += 1

    for code, days_data in insts.items():
        for d, v in days_data.items():
            conn.execute("""INSERT OR REPLACE INTO daily_institutional
                (date,code,name,foreign_net,trust_net,dealer_net,total_net)
                VALUES (?,?,?,?,?,?,?)""",
                (d, code, names.get(code, ""), v["foreign_net"], v["trust_net"],
                 v["dealer_net"], v["total_net"]))
            n_inst += 1
            market_agg[d]["f"] += v["foreign_net"]
            market_agg[d]["t"] += v["trust_net"]
            market_agg[d]["d"] += v["dealer_net"]

    # 大盤每日：TAIEX + 三大法人合計（與 live institutional_summary 同定義：股數×60/1e8）
    code_taiex, taiex_days = _fetch_price_window("TAIEX", s, e)
    for d, m in market_agg.items():
        tx = taiex_days.get(d, {})
        conn.execute("""INSERT OR REPLACE INTO daily_market
            (date,taiex_close,taiex_change,taiex_change_pct,foreign_net_b,trust_net_b,dealer_net_b,margin_balance,short_balance)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (d, tx.get("close"), tx.get("change"), tx.get("change_pct"),
             round(m["f"] * 60 / 1e8, 1), round(m["t"] * 60 / 1e8, 1), round(m["d"] * 60 / 1e8, 1),
             None, None))

    conn.commit()
    # 統計
    dates = conn.execute("SELECT COUNT(DISTINCT date) AS n FROM daily_price").fetchone()["n"]
    conn.close()
    log.info(f"✅ 回填完成：{n_price} 筆價格、{n_inst} 筆法人，涵蓋 {dates} 個交易日")


if __name__ == "__main__":
    main()
