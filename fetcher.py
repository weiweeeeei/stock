"""
台股官方數據抓取模組
Taiwan Stock Official Data Fetcher

數據來源（全部官方，免費，無需 token）：
  - TWSE 台灣證券交易所 (上市股票)
  - TPEx 櫃買中心 (上櫃股票)

重要：這些 API 只在台灣時間 14:00 後有當日數據
      盤中數據請用 yfinance 或付費 API
"""

import requests
import time
import json
import logging
from datetime import date, timedelta
from typing import Optional

log = logging.getLogger(__name__)

# ── 共用設定 ────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.twse.com.tw/",
}

TWSE = "https://www.twse.com.tw"
TPEX = "https://www.tpex.org.tw"

def _get(url: str, params: dict = None, retries: int = 3) -> Optional[dict]:
    """帶重試的 GET，回傳 JSON dict 或 None"""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
            # TWSE 回傳 {"stat": "OK", ...} 或 {"stat": "No data."}
            if isinstance(data, dict) and data.get("stat") == "No data.":
                log.warning(f"TWSE 無資料: {url}")
                return None
            return data
        except requests.exceptions.HTTPError as e:
            log.error(f"HTTP 錯誤 (嘗試 {attempt+1}): {e}")
        except requests.exceptions.ConnectionError as e:
            log.error(f"連線失敗 (嘗試 {attempt+1}): {e}")
        except requests.exceptions.Timeout:
            log.error(f"逾時 (嘗試 {attempt+1})")
        except json.JSONDecodeError as e:
            log.error(f"JSON 解析失敗: {e}")
            return None
        if attempt < retries - 1:
            time.sleep(2 ** attempt)  # 指數退避
    return None


def last_trading_day() -> str:
    """取得最近交易日（跳過週末，節假日需另外處理）"""
    d = date.today()
    # 若今天是週六(5)往前1天，週日(6)往前2天
    if d.weekday() == 5:
        d -= timedelta(days=1)
    elif d.weekday() == 6:
        d -= timedelta(days=2)
    return d.strftime("%Y%m%d")  # TWSE 格式：20250607


# ── TWSE 上市 API ────────────────────────────────────────────────────────────

def fetch_taiex(date_str: str) -> dict:
    """
    加權指數當日資訊
    回傳: {close, open, high, low, volume, change, change_pct}
    """
    data = _get(f"{TWSE}/exchangeReport/MI_INDEX", params={
        "response": "json",
        "date": date_str,
        "type": "IND",
    })
    if not data:
        return {}

    # 找加權指數那列（"發行量加權股價指數"）
    fields = data.get("fields9", [])
    rows   = data.get("data9", [])
    target = None
    for row in rows:
        if "加權" in row[0]:
            target = row
            break
    if not target or not fields:
        return {}

    def clean(val: str) -> str:
        return val.replace(",", "").strip()

    result = {}
    for i, field in enumerate(fields):
        if i < len(target):
            result[field] = clean(target[i])

    # 標準化欄位名
    return {
        "name":       result.get("指數名稱", "加權指數"),
        "close":      result.get("收盤指數", ""),
        "change":     result.get("漲跌點數", ""),
        "change_pct": result.get("漲跌百分比", ""),
        "open":       result.get("開盤指數", ""),
        "high":       result.get("最高指數", ""),
        "low":        result.get("最低指數", ""),
    }


def fetch_sector_index(date_str: str) -> list[dict]:
    """
    各類股指數漲跌
    回傳: [{sector, close, change, change_pct}, ...]
    """
    data = _get(f"{TWSE}/exchangeReport/MI_INDEX", params={
        "response": "json",
        "date": date_str,
        "type": "IND",
    })
    if not data:
        return []

    # MI_INDEX 有多個 data 區塊，data8 是各類指數
    fields = data.get("fields8", [])
    rows   = data.get("data8", [])

    results = []
    for row in rows:
        item = {}
        for i, f in enumerate(fields):
            if i < len(row):
                item[f] = row[i].replace(",", "").strip()
        if item:
            results.append({
                "sector":     item.get("指數名稱", ""),
                "close":      item.get("收盤指數", ""),
                "change":     item.get("漲跌點數", ""),
                "change_pct": item.get("漲跌百分比", ""),
                "open":       item.get("開盤指數", ""),
            })

    return results


def fetch_all_stocks_close(date_str: str) -> list[dict]:
    """
    全部上市股票當日收盤資料
    回傳: [{code, name, close, change, change_pct, volume, ...}, ...]
    """
    data = _get(f"{TWSE}/exchangeReport/STOCK_DAY_ALL", params={
        "response": "json",
        "date": date_str,
    })
    if not data:
        return []

    fields = data.get("fields", [])
    rows   = data.get("data", [])

    results = []
    for row in rows:
        item = {}
        for i, f in enumerate(fields):
            if i < len(row):
                item[f] = row[i].replace(",", "").strip()

        # 計算漲跌%（TWSE 有時不直接給，用收盤-昨收計算）
        try:
            close  = float(item.get("收盤價", 0) or 0)
            change = float(item.get("漲跌價差", 0) or 0)
            prev   = close - change
            pct    = (change / prev * 100) if prev != 0 else 0
        except:
            pct = 0

        results.append({
            "code":       item.get("證券代號", ""),
            "name":       item.get("證券名稱", ""),
            "close":      item.get("收盤價", ""),
            "change":     item.get("漲跌價差", ""),
            "change_pct": f"{pct:+.2f}%",
            "volume":     item.get("成交股數", ""),
            "turnover":   item.get("成交金額", ""),
            "open":       item.get("開盤價", ""),
            "high":       item.get("最高價", ""),
            "low":        item.get("最低價", ""),
        })

    return results


def fetch_institutional_all(date_str: str) -> list[dict]:
    """
    三大法人每日買賣超明細（全部股票）
    回傳: [{code, name, foreign_net, trust_net, dealer_net, total_net}, ...]
    """
    data = _get(f"{TWSE}/fund/T86", params={
        "response": "json",
        "date": date_str,
        "selectType": "ALL",
    })
    if not data:
        return []

    fields = data.get("fields", [])
    rows   = data.get("data", [])

    results = []
    for row in rows:
        item = {}
        for i, f in enumerate(fields):
            if i < len(row):
                item[f] = row[i].replace(",", "").strip()

        def to_int(val: str) -> int:
            try:
                return int(val.replace("+", "").replace(",", "") or 0)
            except:
                return 0

        # 外資=外資自行+外資自行帳，投信，自營商
        foreign = to_int(item.get("外陸資買賣超股數(不含外資自營商)", "0"))
        trust   = to_int(item.get("投信買賣超股數", "0"))
        dealer  = to_int(item.get("自營商買賣超股數(合計)", "0"))
        total   = foreign + trust + dealer

        results.append({
            "code":        item.get("證券代號", ""),
            "name":        item.get("證券名稱", ""),
            "foreign_net": foreign,   # 股數（正=買超，負=賣超）
            "trust_net":   trust,
            "dealer_net":  dealer,
            "total_net":   total,
        })

    # 依三大法人合計買超排序
    results.sort(key=lambda x: x["total_net"], reverse=True)
    return results


def fetch_foreign_top20(date_str: str) -> list[dict]:
    """外資買超前 20 名"""
    data = _get(f"{TWSE}/fund/MI_QFIIS_sort_20", params={
        "response": "json",
        "date": date_str,
        "selectType": "Q",
    })
    if not data:
        return []
    fields = data.get("fields", [])
    rows   = data.get("data", [])
    results = []
    for row in rows:
        item = {f: (row[i].replace(",","").strip() if i < len(row) else "")
                for i, f in enumerate(fields)}
        results.append({
            "code":        item.get("證券代號",""),
            "name":        item.get("證券名稱",""),
            "foreign_buy": item.get("買進股數",""),
            "foreign_sell":item.get("賣出股數",""),
            "foreign_net": item.get("買賣超股數",""),
        })
    return results


def fetch_trust_top20(date_str: str) -> list[dict]:
    """投信買超前 20 名"""
    data = _get(f"{TWSE}/fund/MI_SITC_sort_20", params={
        "response": "json",
        "date": date_str,
        "selectType": "Q",
    })
    if not data:
        return []
    fields = data.get("fields", [])
    rows   = data.get("data", [])
    results = []
    for row in rows:
        item = {f: (row[i].replace(",","").strip() if i < len(row) else "")
                for i, f in enumerate(fields)}
        results.append({
            "code":       item.get("證券代號",""),
            "name":       item.get("證券名稱",""),
            "trust_buy":  item.get("買進股數",""),
            "trust_sell": item.get("賣出股數",""),
            "trust_net":  item.get("買賣超股數",""),
        })
    return results


def fetch_volume_top20(date_str: str) -> list[dict]:
    """成交量排行前 20 名"""
    data = _get(f"{TWSE}/exchangeReport/MI_INDEX20", params={
        "response": "json",
        "date": date_str,
        "type": "V",
    })
    if not data:
        return []
    fields = data.get("fields", [])
    rows   = data.get("data", [])
    results = []
    for row in rows:
        item = {f: (row[i].replace(",","").strip() if i < len(row) else "")
                for i, f in enumerate(fields)}
        results.append({
            "code":    item.get("證券代號",""),
            "name":    item.get("證券名稱",""),
            "volume":  item.get("成交股數",""),
            "close":   item.get("收盤價",""),
            "change":  item.get("漲跌",""),
        })
    return results


def fetch_margin(date_str: str) -> dict:
    """融資融券彙總（市場面情緒指標）"""
    data = _get(f"{TWSE}/exchangeReport/MI_MARGN", params={
        "response": "json",
        "date": date_str,
        "selectType": "MS",
    })
    if not data:
        return {}
    # 取合計列
    fields = data.get("fields", [])
    rows   = data.get("data", [])
    for row in rows:
        item = {f: (row[i].replace(",","").strip() if i < len(row) else "")
                for i, f in enumerate(fields)}
        if "合計" in item.get("股票名稱","") or "合計" in item.get("證券名稱",""):
            return {
                "margin_balance":    item.get("融資餘額",""),   # 融資餘額（張）
                "short_balance":     item.get("融券餘額",""),   # 融券餘額（張）
                "margin_change":     item.get("融資增減",""),
                "short_change":      item.get("融券增減",""),
            }
    return {}


# ── TPEx 上櫃 API ─────────────────────────────────────────────────────────────

def fetch_tpex_stocks(date_str: str) -> list[dict]:
    """
    上櫃股票當日收盤行情
    date_str 格式：民國年/月/日，如 114/06/07
    """
    # TPEx 用民國年
    d = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
    roc_date = f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"

    data = _get(
        f"{TPEX}/web/stock/aftertrading/otc_quotes_no1430/stk_wn1430_result.php",
        params={"l": "zh-tw", "o": "json", "d": roc_date, "se": "EW"},
    )
    if not data:
        return []

    aaData = data.get("aaData", [])
    results = []
    for row in aaData:
        if len(row) < 8:
            continue
        try:
            close  = float(str(row[2]).replace(",","") or 0)
            change = float(str(row[3]).replace(",","") or 0)
            prev   = close - change
            pct    = (change / prev * 100) if prev != 0 else 0
        except:
            pct = 0

        results.append({
            "code":       str(row[0]).strip(),
            "name":       str(row[1]).strip(),
            "close":      str(row[2]).strip(),
            "change":     str(row[3]).strip(),
            "change_pct": f"{pct:+.2f}%",
            "volume":     str(row[7]).replace(",","").strip(),
            "market":     "OTC",
        })
    return results


def fetch_tpex_institutional(date_str: str) -> list[dict]:
    """上櫃三大法人買賣超"""
    d = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
    roc_date = f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"

    data = _get(
        f"{TPEX}/web/stock/3insti/daily_trade/3itrade_hedge_result.php",
        params={"l": "zh-tw", "o": "json", "se": "EW", "d": roc_date},
    )
    if not data:
        return []

    aaData = data.get("aaData", [])
    results = []
    for row in aaData:
        if len(row) < 10:
            continue
        def ti(val):
            try: return int(str(val).replace(",","").replace("+","") or 0)
            except: return 0

        results.append({
            "code":        str(row[0]).strip(),
            "name":        str(row[1]).strip(),
            "foreign_net": ti(row[4]),
            "trust_net":   ti(row[7]),
            "dealer_net":  ti(row[10]) if len(row) > 10 else 0,
        })
    return results


def fetch_tpex_sector_index(date_str: str) -> list[dict]:
    """上櫃類股指數"""
    d = date(int(date_str[:4]), int(date_str[4:6]), int(date_str[6:]))
    roc_date = f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"

    data = _get(
        f"{TPEX}/web/stock/iNdex_info/inx/tpex_inx_result.php",
        params={"l": "zh-tw", "o": "json", "d": roc_date},
    )
    if not data:
        return []

    aaData = data.get("aaData", [])
    results = []
    for row in aaData:
        if len(row) < 3:
            continue
        try:
            change_pct = float(str(row[2]).replace("%","").replace("+","") or 0)
        except:
            change_pct = 0
        results.append({
            "sector":     str(row[0]).strip(),
            "close":      str(row[1]).strip(),
            "change_pct": f"{change_pct:+.2f}%",
            "market":     "OTC",
        })
    return results


# ── 整合函數（analyzer.py 呼叫這個）────────────────────────────────────────────

def fetch_all_market_data(date_str: str = None) -> dict:
    """
    一次抓取所有需要的市場數據
    date_str: YYYYMMDD，預設最近交易日
    回傳完整市場數據 dict
    """
    if not date_str:
        date_str = last_trading_day()

    log.info(f"開始抓取 {date_str} 市場數據...")
    result = {"date": date_str, "errors": []}

    # ── 1. 加權指數 ──────────────────────────────────
    log.info("  [1/8] 加權指數...")
    taiex = fetch_taiex(date_str)
    result["taiex"] = taiex
    if not taiex:
        result["errors"].append("加權指數抓取失敗")

    # ── 2. 各類股指數（上市）────────────────────────────
    log.info("  [2/8] 類股指數（上市）...")
    time.sleep(0.5)
    sector_twse = fetch_sector_index(date_str)
    result["sector_twse"] = sector_twse
    log.info(f"       取得 {len(sector_twse)} 個產業指數")

    # ── 3. 類股指數（上櫃）────────────────────────────
    log.info("  [3/8] 類股指數（上櫃）...")
    time.sleep(0.5)
    sector_tpex = fetch_tpex_sector_index(date_str)
    result["sector_tpex"] = sector_tpex
    log.info(f"       取得 {len(sector_tpex)} 個上櫃產業指數")

    # ── 4. 全部上市個股收盤 ──────────────────────────────
    log.info("  [4/8] 全部上市個股收盤...")
    time.sleep(0.5)
    stocks_twse = fetch_all_stocks_close(date_str)
    result["stocks_twse"] = stocks_twse
    log.info(f"       取得 {len(stocks_twse)} 檔上市股票")

    # ── 5. 全部上櫃個股收盤 ──────────────────────────────
    log.info("  [5/8] 全部上櫃個股收盤...")
    time.sleep(0.5)
    stocks_tpex = fetch_tpex_stocks(date_str)
    result["stocks_tpex"] = stocks_tpex
    log.info(f"       取得 {len(stocks_tpex)} 檔上櫃股票")

    # ── 6. 三大法人明細（上市）──────────────────────────
    log.info("  [6/8] 三大法人（上市）...")
    time.sleep(0.5)
    inst_twse = fetch_institutional_all(date_str)
    result["institutional_twse"] = inst_twse
    log.info(f"       取得 {len(inst_twse)} 筆法人買賣超")

    # ── 7. 三大法人彙總（上市外資/投信 Top20）────────────
    log.info("  [7/8] 外資/投信 Top20...")
    time.sleep(0.5)
    result["foreign_top20"] = fetch_foreign_top20(date_str)
    time.sleep(0.3)
    result["trust_top20"] = fetch_trust_top20(date_str)
    time.sleep(0.3)
    result["volume_top20"] = fetch_volume_top20(date_str)

    # ── 8. 融資融券（情緒指標）──────────────────────────
    log.info("  [8/8] 融資融券...")
    time.sleep(0.5)
    result["margin"] = fetch_margin(date_str)

    # ── 計算三大法人彙總 ─────────────────────────────────
    total_foreign = sum(s["foreign_net"] for s in inst_twse)
    total_trust   = sum(s["trust_net"]   for s in inst_twse)
    total_dealer  = sum(s["dealer_net"]  for s in inst_twse)
    result["institutional_summary"] = {
        "foreign_total_net": total_foreign,   # 股數
        "trust_total_net":   total_trust,
        "dealer_total_net":  total_dealer,
        "grand_total_net":   total_foreign + total_trust + total_dealer,
        # 轉換成億元（以均價60元估算）
        "foreign_net_billion": round(total_foreign * 60 / 1e8, 1),
        "trust_net_billion":   round(total_trust   * 60 / 1e8, 1),
        "dealer_net_billion":  round(total_dealer  * 60 / 1e8, 1),
    }

    log.info(f"✅ 數據抓取完成，共 {len(stocks_twse)+len(stocks_tpex)} 檔個股")
    return result


def build_context_for_claude(market_data: dict, stock_universe: dict) -> str:
    """
    將原始市場數據整理成給 Claude 的分析 context
    只傳入與分類資料庫匹配的重點數據，避免 token 過多
    """
    date_str = market_data["date"]
    taiex    = market_data.get("taiex", {})
    inst_sum = market_data.get("institutional_summary", {})
    sectors  = market_data.get("sector_twse", [])
    all_stocks_price = {
        s["code"]: s for s in
        market_data.get("stocks_twse", []) + market_data.get("stocks_tpex", [])
    }

    # ── 加權指數 ──────────────────────────────────────────
    taiex_txt = (
        f"加權指數：{taiex.get('close','-')} "
        f"漲跌：{taiex.get('change','-')} ({taiex.get('change_pct','-')})"
        if taiex else "加權指數：資料抓取失敗"
    )

    # ── 三大法人（億元）───────────────────────────────────
    def fmt_b(val):
        return f"{val:+.1f}" if val else "0"

    inst_txt = (
        f"外資：{fmt_b(inst_sum.get('foreign_net_billion'))} 億\n"
        f"投信：{fmt_b(inst_sum.get('trust_net_billion'))} 億\n"
        f"自營：{fmt_b(inst_sum.get('dealer_net_billion'))} 億\n"
        f"合計：{fmt_b(inst_sum.get('foreign_net_billion',0)+inst_sum.get('trust_net_billion',0)+inst_sum.get('dealer_net_billion',0))} 億"
    )

    # ── 上市類股指數（前10名漲、前5名跌）─────────────────────
    sorted_sectors = sorted(
        [s for s in sectors if s.get("change_pct") and s["change_pct"] != ""],
        key=lambda x: float(x.get("change_pct", "0").replace("%","")),
        reverse=True
    )
    sector_txt = "【漲幅前10】\n"
    for s in sorted_sectors[:10]:
        sector_txt += f"  {s['sector']}: {s['change_pct']}\n"
    sector_txt += "【跌幅前5】\n"
    for s in sorted_sectors[-5:]:
        sector_txt += f"  {s['sector']}: {s['change_pct']}\n"

    # ── 資料庫中個股的當日表現 ────────────────────────────────
    stock_txt = ""
    for code, info in stock_universe.items():
        price_data = all_stocks_price.get(code, {})
        if price_data:
            stock_txt += (
                f"  {code} {info['name']}({info['sector']}/{info['chain']}): "
                f"收{price_data['close']} {price_data['change_pct']}\n"
            )

    # ── 外資買超 Top10 ──────────────────────────────────────
    foreign_top = market_data.get("foreign_top20", [])[:10]
    foreign_txt = "\n".join(
        f"  {s['code']} {s['name']}: 淨買 {s['foreign_net']} 股"
        for s in foreign_top
    )

    # ── 投信買超 Top10 ──────────────────────────────────────
    trust_top = market_data.get("trust_top20", [])[:10]
    trust_txt = "\n".join(
        f"  {s['code']} {s['name']}: 淨買 {s['trust_net']} 股"
        for s in trust_top
    )

    # ── 融資融券 ────────────────────────────────────────────
    margin = market_data.get("margin", {})
    margin_txt = (
        f"融資餘額：{margin.get('margin_balance','-')} 張 (增減{margin.get('margin_change','-')})\n"
        f"融券餘額：{margin.get('short_balance','-')} 張 (增減{margin.get('short_change','-')})"
        if margin else "融資融券：無資料"
    )

    return f"""
=== 台股官方數據 {date_str} ===
（數據來源：台灣證券交易所 + 櫃買中心，官方正確數據）

【大盤指數】
{taiex_txt}

【三大法人買賣超（估算億元）】
{inst_txt}

【各類股指數漲跌（上市）】
{sector_txt}

【外資買超前10】
{foreign_txt}

【投信買超前10】
{trust_txt}

【融資融券（市場槓桿情緒）】
{margin_txt}

【資料庫個股當日表現】
（以下為資料庫中有對應數據的個股）
{stock_txt}
""".strip()


# ── 測試用 ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    date_str = sys.argv[1] if len(sys.argv) > 1 else last_trading_day()
    print(f"\n抓取日期：{date_str}")
    print("=" * 50)

    data = fetch_all_market_data(date_str)

    print(f"\n✅ 抓取結果摘要：")
    print(f"  加權指數：{data['taiex'].get('close','N/A')} ({data['taiex'].get('change_pct','N/A')})")
    print(f"  類股指數（上市）：{len(data['sector_twse'])} 個")
    print(f"  類股指數（上櫃）：{len(data['sector_tpex'])} 個")
    print(f"  上市個股：{len(data['stocks_twse'])} 檔")
    print(f"  上櫃個股：{len(data['stocks_tpex'])} 檔")
    print(f"  三大法人：{len(data['institutional_twse'])} 筆")

    inst = data["institutional_summary"]
    print(f"\n三大法人彙總（估算）：")
    print(f"  外資：{inst['foreign_net_billion']:+.1f} 億")
    print(f"  投信：{inst['trust_net_billion']:+.1f} 億")
    print(f"  自營：{inst['dealer_net_billion']:+.1f} 億")

    if data["errors"]:
        print(f"\n⚠️  錯誤：{data['errors']}")
