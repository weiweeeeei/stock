"""
訊號引擎 - 整合所有維度，輸出最終燈號
設計原則：笨蛋也看得懂，一個燈號 + 一句話

燈號定義：
  🟢 強力做多  score >= 70，多維度訊號對齊
  🟡 觀察等待  score 40~69，訊號分歧或不足
  🔴 暫時迴避  score < 40，空頭訊號為主
"""

from database import get_institutional_trend, get_market_trend
from technicals import calc_technicals


# ── 個股綜合評分 ──────────────────────────────────────────────────────────────

def score_stock(code: str, today_data: dict) -> dict:
    """
    整合四個維度計算個股綜合評分
    today_data: 當日收盤 + 法人數據

    評分維度：
      技術面  30分  (均線/KD/MACD/量能)
      法人面  30分  (當日+連續買超)
      趨勢面  20分  (N日累積方向)
      大盤面  20分  (市場環境)
    """

    result = {
        "code":  code,
        "name":  today_data.get("name", ""),
        "close": today_data.get("close", 0),
        "change_pct": today_data.get("change_pct", ""),
    }

    scores = {}
    reasons = []

    # ── 1. 技術面 (30分) ──────────────────────────────────────────────────────
    tech = calc_technicals(code)
    tech_score = tech["score"]  # 0~100
    scores["tech"] = round(tech_score * 0.30)
    result["tech"] = tech

    for sig in tech["signals"]:
        reasons.append(sig)

    # ── 2. 法人面 (30分) ──────────────────────────────────────────────────────
    inst_today = today_data.get("institutional", {})
    foreign_today = inst_today.get("foreign_net", 0)
    trust_today   = inst_today.get("trust_net", 0)
    total_today   = foreign_today + trust_today

    trend = get_institutional_trend(code, days=10)
    consec_f = trend.get("consecutive_foreign_buy", 0)
    f5d      = trend.get("total_foreign_5d", 0)
    t5d      = trend.get("trust_5d", 0)

    inst_score = 50  # base
    if foreign_today > 0:
        inst_score += 15
        reasons.append(f"✅ 外資今日買超 {foreign_today//1000:.0f}千股")
    elif foreign_today < 0:
        inst_score -= 15
        reasons.append(f"🔴 外資今日賣超 {abs(foreign_today)//1000:.0f}千股")

    if trust_today > 0:
        inst_score += 10
        reasons.append(f"✅ 投信今日買超 {trust_today//1000:.0f}千股")

    if consec_f >= 5:
        inst_score += 20
        reasons.append(f"✅ 外資連續 {consec_f} 日買超（強力追蹤）")
    elif consec_f >= 3:
        inst_score += 10
        reasons.append(f"✅ 外資連續 {consec_f} 日買超")
    elif trend.get("trend") == "持續賣超":
        inst_score -= 15
        reasons.append("🔴 外資近5日持續賣超")

    if f5d > 0 and t5d > 0:
        inst_score += 10
        reasons.append("✅ 外資+投信近5日同步買超")

    scores["inst"] = round(min(100, max(0, inst_score)) * 0.30)

    # ── 3. 趨勢面 (20分) ──────────────────────────────────────────────────────
    trend_score = 50
    if trend.get("total_foreign_10d", 0) > 0:
        trend_score += 20
    elif trend.get("total_foreign_10d", 0) < 0:
        trend_score -= 20

    if trend.get("days_available", 0) < 3:
        trend_score = 50
        reasons.append("🟡 歷史數據累積中（建議觀察3日後）")

    scores["trend"] = round(min(100, max(0, trend_score)) * 0.20)

    # ── 4. 大盤面 (20分) ──────────────────────────────────────────────────────
    mkt = get_market_trend(days=5)
    mkt_bias = mkt.get("market_bias", "震盪")
    if mkt_bias == "偏多":
        mkt_score = 70
        reasons.append("✅ 大盤近5日偏多，順勢做多")
    elif mkt_bias == "偏空":
        mkt_score = 30
        reasons.append("🔴 大盤近5日偏空，謹慎操作")
    else:
        mkt_score = 50

    scores["market"] = round(mkt_score * 0.20)

    # ── 最終評分 ──────────────────────────────────────────────────────────────
    total_score = sum(scores.values())
    result["score"]        = total_score
    result["score_detail"] = scores
    result["reasons"]      = reasons[:5]  # 最多5條理由（報告用）

    # 動態門檻：歷史資料不足時放寬綠燈門檻，避免「永遠 0 綠燈」。
    # 技術面或趨勢面任一被強制中性 → 用較鬆的門檻；資料齊全才恢復 70 / 40。
    hist_thin = (
        tech.get("summary", "").startswith("歷史數據不足")
        or trend.get("days_available", 0) < 5
    )
    green_th, yellow_th = (50, 30) if hist_thin else (70, 40)

    if total_score >= green_th:
        result["signal"]       = "🟢"
        result["signal_label"] = "強力做多"
        result["signal_color"] = "#39d98a"
        result["one_line"]     = _gen_one_line("做多", reasons, tech, trend)
    elif total_score >= yellow_th:
        result["signal"]       = "🟡"
        result["signal_label"] = "觀察等待"
        result["signal_color"] = "#e8c84a"
        result["one_line"]     = _gen_one_line("觀察", reasons, tech, trend)
    else:
        result["signal"]       = "🔴"
        result["signal_label"] = "暫時迴避"
        result["signal_color"] = "#ff4d6d"
        result["one_line"]     = _gen_one_line("迴避", reasons, tech, trend)

    return result


def _gen_one_line(action: str, reasons: list, tech: dict, trend: dict) -> str:
    """生成一句話理由"""
    key_reasons = [r for r in reasons if "✅" in r]
    neg_reasons = [r for r in reasons if "🔴" in r]

    consec = trend.get("consecutive_foreign_buy", 0)
    tech_sum = tech.get("summary", "")

    if action == "做多":
        if consec >= 5:
            return f"外資連買{consec}日，{tech_sum.replace('技術面','').strip()}"
        elif key_reasons:
            clean = key_reasons[0].replace("✅","").strip()
            return f"{clean}，{tech_sum.replace('技術面強勢，','').split('，')[0]}"
        return tech_sum
    elif action == "觀察":
        return f"訊號分歧，等待方向確認後再進場"
    else:
        if neg_reasons:
            clean = neg_reasons[0].replace("🔴","").strip()
            return f"{clean}，宜觀望"
        return "多空訊號偏空，暫時迴避"


# ── 市場整體燈號 ──────────────────────────────────────────────────────────────

def score_market(market_data: dict) -> dict:
    """
    整體市場燈號
    決定今日是否適合積極操作
    """
    mkt = get_market_trend(days=5)
    inst = market_data.get("institutional_summary", {})
    taiex = market_data.get("taiex", {})

    score = 50
    signals = []

    # 外資5日方向
    f5 = mkt.get("foreign_5d_b", 0)
    if f5 > 50:
        score += 15
        signals.append(f"外資近5日買超 {f5:+.1f}億")
    elif f5 < -50:
        score -= 15
        signals.append(f"外資近5日賣超 {f5:+.1f}億")

    # 今日法人
    today_f = inst.get("foreign_net_billion", 0) or 0
    if today_f > 30:
        score += 10
        signals.append(f"今日外資大買 {today_f:+.1f}億")
    elif today_f < -30:
        score -= 10
        signals.append(f"今日外資大賣 {today_f:+.1f}億")

    # 大盤漲跌
    try:
        chg = float(str(taiex.get("change_pct","0")).replace("%","").replace("+",""))
        if chg > 1:
            score += 10
        elif chg < -1:
            score -= 10
    except:
        pass

    # 5日上漲天數
    up5 = mkt.get("up_days_5d", 0)
    if up5 >= 4:
        score += 10
        signals.append("大盤近5日上漲4天")
    elif up5 <= 1:
        score -= 10
        signals.append("大盤近5日僅上漲1天")

    score = max(0, min(100, score))

    if score >= 65:
        label, color, advice = "市場偏多", "#39d98a", "可積極布局強勢股"
    elif score >= 40:
        label, color, advice = "市場震盪", "#e8c84a", "精選個股，控制倉位"
    else:
        label, color, advice = "市場偏空", "#ff4d6d", "輕倉觀望，等待訊號"

    return {
        "score":   score,
        "label":   label,
        "color":   color,
        "advice":  advice,
        "signals": signals,
        "foreign_5d_b": mkt.get("foreign_5d_b", 0),
        "up_days_5d":   mkt.get("up_days_5d", 0),
    }


# ── 產業燈號 ──────────────────────────────────────────────────────────────────

def score_sectors(sector_data: list[dict], inst_data: list[dict]) -> list[dict]:
    """
    給每個產業打燈號
    結合：今日漲跌% + 近期趨勢 + 法人資金流入估算
    """
    # 整理法人數據：哪些產業收到法人買超
    from data.stock_universe import STOCK_UNIVERSE
    sector_inst = {}  # sector -> total institutional net
    code_to_sector = {}
    for sec, info in STOCK_UNIVERSE.items():
        for code in info["stocks"]:
            code_to_sector[code] = sec

    for row in inst_data:
        sec = code_to_sector.get(row.get("code",""), "")
        if sec:
            if sec not in sector_inst:
                sector_inst[sec] = 0
            sector_inst[sec] += row.get("total_net", 0)

    results = []
    for s in sector_data:
        sector_name = s.get("sector","")
        try:
            pct = float(str(s.get("change_pct","0")).replace("%",""))
        except:
            pct = 0

        from database import get_sector_trend
        trend = get_sector_trend(sector_name, days=5)
        inst_flow = sector_inst.get(sector_name, 0)

        score = 50
        if pct > 1.5:    score += 20
        elif pct > 0.5:  score += 10
        elif pct < -1:   score -= 20
        elif pct < -0.3: score -= 10

        if trend["trend"] == "強勢": score += 15
        elif trend["trend"] == "弱勢": score -= 15

        if inst_flow > 0:   score += 10
        elif inst_flow < 0: score -= 10

        score = max(0, min(100, score))

        if score >= 65:
            sig, sig_label, sig_color = "🟢", "強勢", "#39d98a"
        elif score >= 40:
            sig, sig_label, sig_color = "🟡", "觀察", "#e8c84a"
        else:
            sig, sig_label, sig_color = "🔴", "弱勢", "#ff4d6d"

        results.append({
            "sector":     sector_name,
            "change_pct": f"{pct:+.2f}%",
            "score":      score,
            "signal":     sig,
            "signal_label": sig_label,
            "signal_color": sig_color,
            "trend_5d":   trend["trend"],
            "inst_flow":  inst_flow,
        })

    # 按評分排序
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


# ── 從個股反推產業（沒類股指數時的後備方案） ─────────────────────────────────

def score_sectors_from_stocks(stock_signals: list[dict], inst_data: list[dict]) -> list[dict]:
    """
    從已評分的個股訊號聚合出產業燈號。
    FinMind 免費版沒有類股指數，所以用個股加總替代：
      - 同產業綠燈比例高 → 該產業強勢
      - 同產業外資投信流入 → 加分
    """
    from data.stock_universe import STOCK_UNIVERSE

    code_to_sector = {}
    for sec, info in STOCK_UNIVERSE.items():
        for code in info["stocks"]:
            code_to_sector[code] = sec

    code_to_inst = {row.get("code",""): row for row in inst_data}

    sec_stocks: dict[str, list[dict]] = {}
    for s in stock_signals:
        sec = code_to_sector.get(s.get("code",""), "")
        if sec:
            sec_stocks.setdefault(sec, []).append(s)

    results = []
    for sec_name in STOCK_UNIVERSE.keys():
        members = sec_stocks.get(sec_name, [])
        if not members:
            continue
        n = len(members)
        avg_score = sum(s.get("score", 0) for s in members) / n
        green = sum(1 for s in members if s.get("signal") == "🟢")
        red   = sum(1 for s in members if s.get("signal") == "🔴")

        chgs = []
        for s in members:
            try:
                chgs.append(float(str(s.get("change_pct", "0")).replace("%","").replace("+","")))
            except (ValueError, TypeError):
                pass
        avg_chg = sum(chgs) / len(chgs) if chgs else 0

        inst_flow = sum(code_to_inst.get(s.get("code",""), {}).get("total_net", 0) for s in members)

        # 個股平均分 + 綠燈比例加成 − 紅燈比例懲罰
        sector_score = avg_score + (green / n) * 20 - (red / n) * 10
        sector_score = max(0, min(100, sector_score))

        if sector_score >= 60:
            sig, sig_label, sig_color, trend = "🟢", "強勢", "#39d98a", "強勢"
        elif sector_score >= 40:
            sig, sig_label, sig_color, trend = "🟡", "觀察", "#e8c84a", "震盪"
        else:
            sig, sig_label, sig_color, trend = "🔴", "弱勢", "#ff4d6d", "弱勢"

        results.append({
            "sector":       sec_name,
            "change_pct":   f"{avg_chg:+.2f}%",
            "score":        round(sector_score),
            "signal":       sig,
            "signal_label": sig_label,
            "signal_color": sig_color,
            "trend_5d":     trend,
            "inst_flow":    inst_flow,
            "green_count":  green,
            "red_count":    red,
            "stock_count":  n,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
