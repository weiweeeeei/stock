"""
族群分數回填（一次性，0 次 API 呼叫）

從資料庫裡已回填的歷史價格＋法人，逐日重算族群評分並寫入 daily_sector_score，
讓「族群輪動」立即有歷史可比。

關鍵：每一天都用 as_of=該日 重算，只看當天（含）以前的資料，
      不偷看未來，確保歷史分數與往後 live 執行的口徑一致、輪動才有意義。

用法：python replay_scores.py [天數，預設 20]
"""

import sys
import logging
from database import init_db, get_conn, save_sector_scores
from signals import score_stock, score_sectors_from_stocks
from data.stock_universe import get_all_stocks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)


def _trading_dates(limit: int) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT date FROM daily_price ORDER BY date DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return sorted(r["date"] for r in rows)  # 升冪（舊→新）


def _day_data(d: str):
    conn = get_conn()
    prices = conn.execute(
        "SELECT code,name,close,change_pct FROM daily_price WHERE date=?", (d,)).fetchall()
    insts = conn.execute(
        "SELECT code,name,foreign_net,trust_net,dealer_net,total_net FROM daily_institutional WHERE date=?",
        (d,)).fetchall()
    conn.close()
    price_by = {r["code"]: r for r in prices}
    inst_by  = {r["code"]: r for r in insts}
    inst_list = [{"code": r["code"], "name": r["name"], "foreign_net": r["foreign_net"],
                  "trust_net": r["trust_net"], "dealer_net": r["dealer_net"],
                  "total_net": r["total_net"]} for r in insts]
    return price_by, inst_by, inst_list


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    init_db()
    dates = _trading_dates(n)
    universe = get_all_stocks()
    log.info(f"重算 {len(dates)} 個交易日的族群分數（as_of 逐日）...")

    for d in dates:
        price_by, inst_by, inst_list = _day_data(d)
        stock_signals = []
        for code, info in universe.items():
            p = price_by.get(code)
            if not p:
                continue
            i = inst_by.get(code, {})
            pct = p["change_pct"]
            sig = score_stock(code, {
                "name": info["name"],
                "close": p["close"],
                "change_pct": f"{pct:+.2f}%" if pct is not None else "",
                "institutional": {
                    "foreign_net": (i["foreign_net"] if i else 0),
                    "trust_net":   (i["trust_net"]   if i else 0),
                    "dealer_net":  (i["dealer_net"]  if i else 0),
                },
            }, as_of=d)
            sig["change_pct"] = f"{pct:+.2f}%" if pct is not None else ""
            stock_signals.append(sig)

        sectors = score_sectors_from_stocks(stock_signals, inst_list)
        save_sector_scores(d.replace("-", ""), sectors)
        green = sum(1 for s in sectors if s["signal"] == "🟢")
        log.info(f"  {d}: {len(stock_signals)} 檔 → {len(sectors)} 族群（🟢{green}）")

    log.info("✅ 族群分數回填完成，族群輪動已有歷史可比")


if __name__ == "__main__":
    main()
