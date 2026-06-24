"""
台股數據抓取（FinMind 版本）

改用 FinMind API（https://finmindtrade.com）取代直連 TWSE/TPEx，
解決 GitHub Actions 從美國 IP 連 TWSE 不穩定 / 部分端點被擋的問題。

需要 FINMIND_TOKEN 環境變數（免費帳號每小時 600 次額度）。

免費版不能一次抓全市場，所以只抓 STOCK_UNIVERSE 內的 137 檔精選股；
大盤層級的彙總（外資/投信/自營合計、融資融券）改用 *Total* dataset 抓。
"""

import os
import sys
import time
import logging
import requests
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent / "data"))
from stock_universe import STOCK_UNIVERSE, get_all_stocks  # noqa: E402

log = logging.getLogger(__name__)

FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "")
FINMIND_API   = "https://api.finmindtrade.com/api/v4/data"
MAX_WORKERS   = 8  # 並行請求數，避免被 FinMind 限速


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
                msg = j.get("msg", "unknown")
                log.warning(f"FinMind 回傳錯誤 ({dataset}/{params.get('data_id','')}): {msg}")
                return []
            return j.get("data", []) or []
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                log.warning(f"FinMind 連線失敗 ({dataset}/{params.get('data_id','')}): {e}")
    return []


def _to_finmind_date(date_str: str) -> str:
    """20260611 → 2026-06-11"""
    return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"


def _window_start(fd: str, days: int = 14) -> str:
    """回推 N 個日曆天，給區間查詢用（確保涵蓋至少一個前一交易日）。"""
    from datetime import datetime
    d = datetime.strptime(fd, "%Y-%m-%d").date() - timedelta(days=days)
    return d.strftime("%Y-%m-%d")


def _calc_change(rows: list, fd: str) -> tuple:
    """
    從 FinMind 價格序列（同一檔、多日）算「今收 / 漲跌 / 漲跌%」。
    自己用『今收 − 昨收』計算，不信任 FinMind 偶爾出錯的 spread 欄位。
    回傳 (today_row, change, change_pct)；無資料回 (None, 0, 0)。
    """
    rows = [r for r in rows if r.get("date", "") <= fd and r.get("close") is not None]
    rows.sort(key=lambda r: r["date"])
    if not rows:
        return None, 0.0, 0.0
    today = rows[-1]
    t_close = float(today.get("close") or 0)
    if len(rows) >= 2:
        prev_close = float(rows[-2].get("close") or 0)
    else:
        # 只有一天資料 → 退而求其次用 spread 還原昨收
        prev_close = t_close - float(today.get("spread") or 0)
    change = t_close - prev_close
    chg_pct = (change / prev_close * 100) if prev_close else 0.0
    return today, change, chg_pct


def last_trading_day() -> str:
    """
    取得最近一個有資料的交易日。用 TAIEX 做探測。
    """
    d = date.today()
    for _ in range(10):
        if d.weekday() >= 5:
            d -= timedelta(days=1)
            continue
        fd = d.strftime("%Y-%m-%d")
        if _get("TaiwanStockPrice", data_id="TAIEX", start_date=fd, end_date=fd):
            return d.strftime("%Y%m%d")
        d -= timedelta(days=1)
    return date.today().strftime("%Y%m%d")


def fetch_taiex(date_str: str) -> dict:
    fd = _to_finmind_date(date_str)
    data = _get("TaiwanStockPrice", data_id="TAIEX",
                start_date=_window_start(fd), end_date=fd)
    today, change, chg_pct = _calc_change(data, fd)
    if not today:
        return {}
    return {
        "close":      str(today.get("close", "")),
        "open":       str(today.get("open", "")),
        "high":       str(today.get("max", "")),
        "low":        str(today.get("min", "")),
        "volume":     str(today.get("Trading_Volume", "")),
        "change":     f"{change:+.2f}",
        "change_pct": f"{chg_pct:+.2f}%",
    }


def _price_row(today: dict, name: str, change: float, chg_pct: float) -> dict:
    return {
        "code":       today.get("stock_id", ""),
        "name":       name,
        "close":      str(today.get("close", "")),
        "change":     f"{change:+.2f}",
        "change_pct": f"{chg_pct:+.2f}%",
        "volume":     str(today.get("Trading_Volume", "")),
        "open":       str(today.get("open", "")),
        "high":       str(today.get("max", "")),
        "low":        str(today.get("min", "")),
    }


def _fetch_price_one(code: str, name: str, fd: str) -> dict | None:
    # 抓一小段區間，自己用今收−昨收算漲跌（不信任 FinMind 偶爾出錯的 spread）
    data = _get("TaiwanStockPrice", data_id=code,
                start_date=_window_start(fd), end_date=fd)
    today, change, chg_pct = _calc_change(data, fd)
    if not today:
        return None
    return _price_row(today, name, change, chg_pct)


def fetch_stocks_in_universe(date_str: str) -> list[dict]:
    """抓 STOCK_UNIVERSE 裡所有股票的當日價格（並行）。"""
    fd = _to_finmind_date(date_str)
    universe = get_all_stocks()  # {code: {name, sector, ...}}
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {
            ex.submit(_fetch_price_one, code, info["name"], fd): code
            for code, info in universe.items()
        }
        for fut in as_completed(futures):
            row = fut.result()
            if row:
                results.append(row)
    return results


def _fetch_inst_one(code: str, name: str, fd: str) -> dict | None:
    rows = _get("TaiwanStockInstitutionalInvestorsBuySell",
                data_id=code, start_date=fd, end_date=fd)
    if not rows:
        return None
    foreign = trust = dealer = 0
    for r in rows:
        cat = (r.get("name") or "").lower()
        buy = int(r.get("buy") or 0)
        sell = int(r.get("sell") or 0)
        net = buy - sell
        if "foreign" in cat:
            foreign += net
        elif "trust" in cat or "investment" in cat:
            trust += net
        elif "dealer" in cat:
            dealer += net
    return {
        "code":        code,
        "name":        name,
        "foreign_net": foreign,
        "trust_net":   trust,
        "dealer_net":  dealer,
        "total_net":   foreign + trust + dealer,
    }


def fetch_institutional_in_universe(date_str: str) -> list[dict]:
    """抓 STOCK_UNIVERSE 裡所有股票的三大法人買賣超（並行）。"""
    fd = _to_finmind_date(date_str)
    universe = get_all_stocks()
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {
            ex.submit(_fetch_inst_one, code, info["name"], fd): code
            for code, info in universe.items()
        }
        for fut in as_completed(futures):
            row = fut.result()
            if row:
                results.append(row)
    results.sort(key=lambda x: x["total_net"], reverse=True)
    return results


def fetch_institutional_total(date_str: str) -> dict:
    """全市場三大法人合計（不分股票）。FinMind: TaiwanStockTotalInstitutionalInvestors"""
    fd = _to_finmind_date(date_str)
    rows = _get("TaiwanStockTotalInstitutionalInvestors", start_date=fd, end_date=fd)
    foreign = trust = dealer = 0
    for r in rows:
        cat = (r.get("name") or "").lower()
        buy  = int(r.get("buy")  or 0)
        sell = int(r.get("sell") or 0)
        net = buy - sell
        if "foreign" in cat:
            foreign += net
        elif "trust" in cat or "investment" in cat:
            trust += net
        elif "dealer" in cat:
            dealer += net
    return {
        "foreign_total_net":   foreign,
        "trust_total_net":     trust,
        "dealer_total_net":    dealer,
        "grand_total_net":     foreign + trust + dealer,
        # FinMind 已是元，直接轉億：
        "foreign_net_billion": round(foreign / 1e8, 1),
        "trust_net_billion":   round(trust   / 1e8, 1),
        "dealer_net_billion":  round(dealer  / 1e8, 1),
    }


def fetch_margin(date_str: str) -> dict:
    """全市場融資融券彙總。FinMind: TaiwanStockTotalMarginPurchaseShortSale"""
    fd = _to_finmind_date(date_str)
    rows = _get("TaiwanStockTotalMarginPurchaseShortSale", start_date=fd, end_date=fd)
    if not rows:
        return {}
    # 該 dataset 每天通常 2 列：MarginPurchase / ShortSale
    margin_today = margin_prev = short_today = short_prev = 0
    for r in rows:
        nm = (r.get("name") or "").lower()
        today_bal = int(r.get("TodayBalance") or 0)
        yes_bal   = int(r.get("YesBalance") or 0)
        if "margin" in nm:
            margin_today += today_bal
            margin_prev  += yes_bal
        elif "short" in nm:
            short_today += today_bal
            short_prev  += yes_bal
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
    log.info("  [1/5] 加權指數...")
    taiex = fetch_taiex(date_str)
    result["taiex"] = taiex
    if not taiex:
        result["errors"].append("加權指數抓取失敗")

    # ── 2. 個股收盤（STOCK_UNIVERSE 內，137 檔，並行）──
    log.info(f"  [2/5] 個股收盤（{len(get_all_stocks())} 檔並行）...")
    stocks = fetch_stocks_in_universe(date_str)
    result["stocks_twse"] = stocks
    result["stocks_tpex"] = []  # FinMind 已合併
    log.info(f"       取得 {len(stocks)} 檔個股")

    # ── 3. 個股三大法人 ──
    log.info(f"  [3/5] 個股三大法人（{len(get_all_stocks())} 檔並行）...")
    inst = fetch_institutional_in_universe(date_str)
    result["institutional_twse"] = inst
    log.info(f"       取得 {len(inst)} 筆三大法人")

    # 衍生 Top20
    result["foreign_top20"] = sorted(inst, key=lambda x: x["foreign_net"], reverse=True)[:20]
    result["trust_top20"]   = sorted(inst, key=lambda x: x["trust_net"],   reverse=True)[:20]
    def _vol(s):
        try:    return int(s.get("volume") or 0)
        except: return 0
    result["volume_top20"]  = sorted(stocks, key=_vol, reverse=True)[:20]

    # ── 4. 三大法人彙總（從 137 檔 STOCK_UNIVERSE 加總，與個股顯示一致） ──
    log.info("  [4/5] 三大法人彙總（STOCK_UNIVERSE 範圍）...")
    total_f = sum(s["foreign_net"] for s in inst)
    total_t = sum(s["trust_net"]   for s in inst)
    total_d = sum(s["dealer_net"]  for s in inst)
    # FinMind 個股法人單位是「股數」，估算金額：股數 × 平均股價（粗估 60 元）
    result["institutional_summary"] = {
        "foreign_total_net":   total_f,
        "trust_total_net":     total_t,
        "dealer_total_net":    total_d,
        "grand_total_net":     total_f + total_t + total_d,
        "foreign_net_billion": round(total_f * 60 / 1e8, 1),
        "trust_net_billion":   round(total_t * 60 / 1e8, 1),
        "dealer_net_billion":  round(total_d * 60 / 1e8, 1),
    }

    # ── 5. 融資融券（單 call） ──
    log.info("  [5/5] 融資融券...")
    result["margin"] = fetch_margin(date_str)

    # FinMind 沒有現成類股指數，留空
    result["sector_twse"] = []
    result["sector_tpex"] = []

    log.info(f"✅ 數據抓取完成，共 {len(stocks)} 檔個股")
    return result


def build_context_for_claude(market_data: dict, stock_universe: dict) -> str:
    """為與舊版相容保留，目前未實際使用。"""
    date_str = market_data["date"]
    taiex    = market_data.get("taiex", {})
    inst_sum = market_data.get("institutional_summary", {})
    return (
        f"=== 台股 {date_str} ===\n"
        f"加權指數：{taiex.get('close','-')} ({taiex.get('change_pct','-')})\n"
        f"外資：{inst_sum.get('foreign_net_billion','-')} 億 / "
        f"投信：{inst_sum.get('trust_net_billion','-')} 億 / "
        f"自營：{inst_sum.get('dealer_net_billion','-')} 億"
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    date_str = sys.argv[1] if len(sys.argv) > 1 else last_trading_day()
    data = fetch_all_market_data(date_str)
    print(f"\n=== 摘要 ===")
    print(f"日期：{data['date']}")
    print(f"加權指數：{data.get('taiex', {}).get('close')} ({data.get('taiex', {}).get('change_pct')})")
    print(f"個股檔數：{len(data.get('stocks_twse', []))}")
    print(f"三大法人筆數：{len(data.get('institutional_twse', []))}")
    print(f"外資合計：{data.get('institutional_summary', {}).get('foreign_net_billion')} 億")
    print(f"融資餘額：{data.get('margin', {}).get('margin_balance')}")
