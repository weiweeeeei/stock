"""
台股數據抓取（FinMind 版本）

改用 FinMind API（https://finmindtrade.com）取代直連 TWSE/TPEx，
解決 GitHub Actions 從美國 IP 連 TWSE 不穩定 / 部分端點被擋的問題。

需要 FINMIND_TOKEN 環境變數（免費帳號每天 600 次額度）。
"""

import os
import time
import logging
import requests
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

log = logging.getLogger(__name__)

FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "")
FINMIND_API   = "https://api.finmindtrade.com/api/v4/data"


def _get(dataset: str, **params) -> list:
    """呼叫 FinMind，回傳 data list（失敗回空 list）。"""
    params["dataset"] = dataset
    if FINMIND_TOKEN:
        params["token"] = FINMIND_TOKEN
    for attempt in range(3):
        try:
            r = requests.get(FINMIND_API, params=params, timeout=30)
            r.raise_for_status()
            j = r.json()
            if j.get("status") != 200:
                log.warning(f"FinMind 回傳錯誤 ({dataset}): {j.get('msg')}")
                return []
            return j.get("data", []) or []
        except Exception as e:
            log.warning(f"FinMind 連線失敗 ({dataset}, 嘗試 {attempt+1}): {e}")
            if attempt < 2:
                time.sleep(2 ** attempt)
    return []


def _to_finmind_date(date_str: str) -> str:
    """20260611 → 2026-06-11"""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"


def last_trading_day() -> str:
    """
    取得最近一個有完整資料的交易日。
    用 TAIEX 當作探測——FinMind 有 TAIEX 那一天通常就有完整資料。
    自動處理：週末、台股假日、盤中尚未收盤、資料延遲。
    """
    d = date.today()
    for _ in range(10):
        if d.weekday() >= 5:  # 週六/週日跳過
            d -= timedelta(days=1)
            continue
        fd = d.strftime("%Y-%m-%d")
        if _get("TaiwanStockPrice", data_id="TAIEX", start_date=fd, end_date=fd):
            return d.strftime("%Y%m%d")
        d -= timedelta(days=1)
    return date.today().strftime("%Y%m%d")


def fetch_taiex(date_str: str) -> dict:
    """加權指數當日資訊。"""
    fd = _to_finmind_date(date_str)
    data = _get("TaiwanStockPrice", data_id="TAIEX", start_date=fd, end_date=fd)
    if not data:
        return {}
    t = data[0]
    close  = float(t.get("close") or 0)
    spread = float(t.get("spread") or 0)
    prev   = close - spread
    chg_pct = (spread / prev * 100) if prev else 0.0
    return {
        "close":      str(t.get("close", "")),
        "open":       str(t.get("open", "")),
        "high":       str(t.get("max", "")),
        "low":        str(t.get("min", "")),
        "volume":     str(t.get("Trading_Volume", "")),
        "change":     f"{spread:+.2f}",
        "change_pct": f"{chg_pct:+.2f}%",
    }


def _price_row(p: dict) -> dict:
    close  = float(p.get("close") or 0)
    spread = float(p.get("spread") or 0)
    prev   = close - spread
    chg_pct = (spread / prev * 100) if prev else 0.0
    return {
        "code":       p.get("stock_id", ""),
        "name":       "",  # 由 STOCK_UNIVERSE 對應，這裡留空
        "close":      str(p.get("close", "")),
        "change":     f"{spread:+.2f}",
        "change_pct": f"{chg_pct:+.2f}%",
        "volume":     str(p.get("Trading_Volume", "")),
        "open":       str(p.get("open", "")),
        "high":       str(p.get("max", "")),
        "low":        str(p.get("min", "")),
    }


def fetch_all_stocks_close(date_str: str) -> list[dict]:
    """全部個股當日收盤（TWSE + TPEx 已合併）。"""
    fd = _to_finmind_date(date_str)
    data = _get("TaiwanStockPrice", start_date=fd, end_date=fd)
    return [_price_row(p) for p in data if p.get("stock_id") and p.get("stock_id") != "TAIEX"]


def fetch_institutional_all(date_str: str) -> list[dict]:
    """
    三大法人每日買賣超明細。
    FinMind 用 (stock_id, name) 多列表達，name 為投資人類別。
    回傳格式維持與舊版相同：每檔股票一筆 dict。
    """
    fd = _to_finmind_date(date_str)
    rows = _get("TaiwanStockInstitutionalInvestorsBuySell", start_date=fd, end_date=fd)
    if not rows:
        return []
    agg = defaultdict(lambda: {"foreign_net": 0, "trust_net": 0, "dealer_net": 0})
    for r in rows:
        code = r.get("stock_id", "")
        if not code:
            continue
        cat = (r.get("name") or "").lower()
        buy = int(r.get("buy") or 0)
        sell = int(r.get("sell") or 0)
        net = buy - sell
        if "foreign" in cat:
            agg[code]["foreign_net"] += net
        elif "trust" in cat or "investment" in cat:
            agg[code]["trust_net"] += net
        elif "dealer" in cat:
            agg[code]["dealer_net"] += net
    out = []
    for code, vals in agg.items():
        total = vals["foreign_net"] + vals["trust_net"] + vals["dealer_net"]
        out.append({
            "code":        code,
            "name":        "",
            "foreign_net": vals["foreign_net"],
            "trust_net":   vals["trust_net"],
            "dealer_net":  vals["dealer_net"],
            "total_net":   total,
        })
    out.sort(key=lambda x: x["total_net"], reverse=True)
    return out


def fetch_margin(date_str: str) -> dict:
    """全市場融資融券彙總。"""
    fd = _to_finmind_date(date_str)
    rows = _get("TaiwanStockMarginPurchaseShortSale", start_date=fd, end_date=fd)
    if not rows:
        return {}
    margin_today = sum(int(r.get("MarginPurchaseTodayBalance") or 0) for r in rows)
    margin_prev  = sum(int(r.get("MarginPurchaseYesterdayBalance") or 0) for r in rows)
    short_today  = sum(int(r.get("ShortSaleTodayBalance") or 0) for r in rows)
    short_prev   = sum(int(r.get("ShortSaleYesterdayBalance") or 0) for r in rows)
    return {
        "margin_balance": margin_today,
        "margin_change":  margin_today - margin_prev,
        "short_balance":  short_today,
        "short_change":   short_today - short_prev,
    }


def fetch_all_market_data(date_str: str = None) -> dict:
    """
    一次抓取所有需要的市場數據。
    回傳格式與舊版 TWSE 直連版相同，下游 signals/database/reporter 不用改。
    """
    if not date_str:
        date_str = last_trading_day()

    log.info(f"開始抓取 {date_str} 市場數據（FinMind）...")
    result = {"date": date_str, "errors": []}

    # ── 1. 加權指數 ──
    log.info("  [1/4] 加權指數...")
    taiex = fetch_taiex(date_str)
    result["taiex"] = taiex
    if not taiex:
        result["errors"].append("加權指數抓取失敗")

    # ── 2. 全部個股收盤（TWSE+TPEx 已合併）──
    log.info("  [2/4] 個股收盤（含上市櫃）...")
    stocks = fetch_all_stocks_close(date_str)
    result["stocks_twse"] = stocks
    result["stocks_tpex"] = []  # FinMind 已合併，全放 stocks_twse
    log.info(f"       取得 {len(stocks)} 檔個股")

    # ── 3. 三大法人 ──
    log.info("  [3/4] 三大法人...")
    inst = fetch_institutional_all(date_str)
    result["institutional_twse"] = inst
    log.info(f"       取得 {len(inst)} 筆三大法人")

    # 從三大法人衍生 Top20
    result["foreign_top20"] = sorted(inst, key=lambda x: x["foreign_net"], reverse=True)[:20]
    result["trust_top20"]   = sorted(inst, key=lambda x: x["trust_net"],   reverse=True)[:20]

    # 從股價衍生 成交量 Top20
    def _vol(s):
        try:
            return int(s.get("volume") or 0)
        except (ValueError, TypeError):
            return 0
    result["volume_top20"] = sorted(stocks, key=_vol, reverse=True)[:20]

    # ── 4. 融資融券 ──
    log.info("  [4/4] 融資融券...")
    result["margin"] = fetch_margin(date_str)

    # FinMind 沒有現成的類股指數資料，先給空 list（signals.score_sectors 會自行處理）
    result["sector_twse"] = []
    result["sector_tpex"] = []

    # ── 三大法人彙總（億元）──
    total_foreign = sum(s["foreign_net"] for s in inst)
    total_trust   = sum(s["trust_net"]   for s in inst)
    total_dealer  = sum(s["dealer_net"]  for s in inst)
    result["institutional_summary"] = {
        "foreign_total_net":   total_foreign,
        "trust_total_net":     total_trust,
        "dealer_total_net":    total_dealer,
        "grand_total_net":     total_foreign + total_trust + total_dealer,
        "foreign_net_billion": round(total_foreign * 60 / 1e8, 1),
        "trust_net_billion":   round(total_trust   * 60 / 1e8, 1),
        "dealer_net_billion":  round(total_dealer  * 60 / 1e8, 1),
    }

    log.info(f"✅ 數據抓取完成，共 {len(stocks)} 檔個股")
    return result


def build_context_for_claude(market_data: dict, stock_universe: dict) -> str:
    """
    將原始市場數據整理成給 AI 的分析 context。
    （為與舊版相容保留，但目前 analyzer.py 沒有實際用到）
    """
    date_str = market_data["date"]
    taiex    = market_data.get("taiex", {})
    inst_sum = market_data.get("institutional_summary", {})
    all_stocks_price = {s["code"]: s for s in market_data.get("stocks_twse", [])}

    taiex_txt = (
        f"加權指數：{taiex.get('close','-')} "
        f"漲跌：{taiex.get('change','-')} ({taiex.get('change_pct','-')})"
        if taiex else "加權指數：資料抓取失敗"
    )

    def fmt_b(val):
        return f"{val:+.1f}" if val else "0"

    inst_txt = (
        f"外資：{fmt_b(inst_sum.get('foreign_net_billion'))} 億\n"
        f"投信：{fmt_b(inst_sum.get('trust_net_billion'))} 億\n"
        f"自營：{fmt_b(inst_sum.get('dealer_net_billion'))} 億"
    )

    stock_txt = ""
    for code, info in stock_universe.items():
        p = all_stocks_price.get(code, {})
        if p:
            stock_txt += f"  {code} {info['name']}: 收{p['close']} {p['change_pct']}\n"

    return f"""
=== 台股數據 {date_str}（FinMind）===

【大盤指數】
{taiex_txt}

【三大法人買賣超（估算億元）】
{inst_txt}

【資料庫個股當日表現】
{stock_txt}
""".strip()


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    date_str = sys.argv[1] if len(sys.argv) > 1 else last_trading_day()
    data = fetch_all_market_data(date_str)
    print(f"\n=== 摘要 ===")
    print(f"日期：{data['date']}")
    print(f"加權指數：{data.get('taiex', {}).get('close')}")
    print(f"個股檔數：{len(data.get('stocks_twse', []))}")
    print(f"三大法人筆數：{len(data.get('institutional_twse', []))}")
    print(f"融資餘額：{data.get('margin', {}).get('margin_balance')}")
