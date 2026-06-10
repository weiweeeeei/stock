"""
技術指標計算模組
用 SQLite 歷史數據計算 MA / KD / MACD / 布林通道
不依賴任何外部付費 API
"""

import math
from typing import Optional
from database import get_price_history


def _sma(vals: list[float], n: int) -> Optional[float]:
    """簡單移動平均"""
    if len(vals) < n:
        return None
    return sum(vals[-n:]) / n


def _ema(vals: list[float], n: int) -> list[float]:
    """指數移動平均（回傳完整序列）"""
    if not vals:
        return []
    k = 2 / (n + 1)
    result = [vals[0]]
    for v in vals[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result


def calc_technicals(code: str) -> dict:
    """
    計算個股技術指標
    回傳：{
      ma5, ma20, ma60,         # 均線
      kd_k, kd_d,              # KD
      macd, macd_signal, macd_hist,  # MACD
      bb_upper, bb_mid, bb_lower,    # 布林通道
      volume_ratio,            # 量比（今日量/5日均量）
      signals: [訊號列表],
      score: 0~100,            # 技術分數
      summary: "技術面一句話"
    }
    """
    history = get_price_history(code, days=90)

    if len(history) < 5:
        return {
            "ma5": None, "ma20": None, "ma60": None,
            "kd_k": None, "kd_d": None,
            "macd": None, "macd_signal": None, "macd_hist": None,
            "bb_upper": None, "bb_mid": None, "bb_lower": None,
            "volume_ratio": None,
            "signals": [], "score": 50,
            "summary": "歷史數據不足（需累積更多交易日）",
        }

    closes  = [h["close"]  for h in history]
    volumes = [h["volume"] for h in history if h["volume"]]
    highs   = [h["high"]   for h in history if h["high"]]
    lows    = [h["low"]    for h in history if h["low"]]

    result = {}
    signals = []
    score_pts = []

    # ── 均線 ──────────────────────────────────────────────────────────────────
    result["ma5"]  = round(_sma(closes, 5),  2) if _sma(closes, 5)  else None
    result["ma20"] = round(_sma(closes, 20), 2) if _sma(closes, 20) else None
    result["ma60"] = round(_sma(closes, 60), 2) if _sma(closes, 60) else None

    cur = closes[-1]
    if result["ma5"] and result["ma20"] and result["ma60"]:
        if cur > result["ma5"] > result["ma20"] > result["ma60"]:
            signals.append("✅ 多頭排列（站上5/20/60日均線）")
            score_pts.append(30)
        elif cur < result["ma5"] < result["ma20"]:
            signals.append("🔴 空頭排列（跌破均線）")
            score_pts.append(-20)
        elif cur > result["ma20"]:
            signals.append("🟡 站上月線，趨勢偏多")
            score_pts.append(10)

        # 均線交叉
        if len(closes) >= 6:
            prev5  = _sma(closes[:-1], 5)
            prev20 = _sma(closes[:-1], 20)
            if prev5 and prev20:
                if prev5 < prev20 and result["ma5"] > result["ma20"]:
                    signals.append("✅ 黃金交叉（MA5上穿MA20）")
                    score_pts.append(20)
                elif prev5 > prev20 and result["ma5"] < result["ma20"]:
                    signals.append("🔴 死亡交叉（MA5下穿MA20）")
                    score_pts.append(-20)

    # ── KD 指標 ──────────────────────────────────────────────────────────────
    if len(highs) >= 9 and len(lows) >= 9:
        # RSV
        rsv_list = []
        for i in range(8, len(closes)):
            h9 = max(highs[i-8:i+1])
            l9 = min(lows[i-8:i+1])
            rsv = (closes[i] - l9) / (h9 - l9) * 100 if h9 != l9 else 50
            rsv_list.append(rsv)

        k_list = [50.0]
        d_list = [50.0]
        for rsv in rsv_list:
            k = k_list[-1] * 2/3 + rsv * 1/3
            d = d_list[-1] * 2/3 + k   * 1/3
            k_list.append(k)
            d_list.append(d)

        k_val = round(k_list[-1], 1)
        d_val = round(d_list[-1], 1)
        result["kd_k"] = k_val
        result["kd_d"] = d_val

        if k_val < 20 and d_val < 20:
            signals.append("✅ KD 超賣區（可能反彈）")
            score_pts.append(15)
        elif k_val > 80 and d_val > 80:
            signals.append("⚠️ KD 超買區（注意回檔）")
            score_pts.append(-10)
        elif k_val > d_val and k_val < 50:
            signals.append("🟡 KD 低檔黃金交叉")
            score_pts.append(10)
    else:
        result["kd_k"] = result["kd_d"] = None

    # ── MACD ─────────────────────────────────────────────────────────────────
    if len(closes) >= 26:
        ema12 = _ema(closes, 12)
        ema26 = _ema(closes, 26)
        dif   = [a - b for a, b in zip(ema12[25:], ema26[25:])]
        dem   = _ema(dif, 9)
        hist  = [d - s for d, s in zip(dif[8:], dem[8:])]

        if dif and dem and hist:
            result["macd"]        = round(dif[-1], 3)
            result["macd_signal"] = round(dem[-1], 3)
            result["macd_hist"]   = round(hist[-1], 3)

            if dif[-1] > 0 and hist[-1] > 0:
                signals.append("✅ MACD 多頭區間，動能向上")
                score_pts.append(15)
            elif dif[-1] < 0 and hist[-1] < 0:
                signals.append("🔴 MACD 空頭區間")
                score_pts.append(-10)
            # 柱狀體由負轉正
            if len(hist) >= 2 and hist[-2] < 0 < hist[-1]:
                signals.append("✅ MACD 柱狀翻正（動能轉強）")
                score_pts.append(15)
    else:
        result["macd"] = result["macd_signal"] = result["macd_hist"] = None

    # ── 布林通道 ─────────────────────────────────────────────────────────────
    if len(closes) >= 20:
        mid = _sma(closes, 20)
        std = math.sqrt(sum((c - mid)**2 for c in closes[-20:]) / 20)
        result["bb_upper"] = round(mid + 2 * std, 2)
        result["bb_mid"]   = round(mid, 2)
        result["bb_lower"] = round(mid - 2 * std, 2)

        if cur < result["bb_lower"]:
            signals.append("🟡 跌破布林下軌（超賣，注意反彈）")
            score_pts.append(10)
        elif cur > result["bb_upper"]:
            signals.append("⚠️ 突破布林上軌（強勢但注意過熱）")
            score_pts.append(5)
    else:
        result["bb_upper"] = result["bb_mid"] = result["bb_lower"] = None

    # ── 量能分析 ─────────────────────────────────────────────────────────────
    if len(volumes) >= 6 and volumes[-1]:
        avg5 = sum(volumes[-6:-1]) / 5
        vol_ratio = volumes[-1] / avg5 if avg5 > 0 else 1
        result["volume_ratio"] = round(vol_ratio, 2)

        chg = closes[-1] - closes[-2] if len(closes) >= 2 else 0
        if vol_ratio >= 1.5 and chg > 0:
            signals.append("✅ 量增價漲（強勢突破訊號）")
            score_pts.append(20)
        elif vol_ratio >= 1.5 and chg < 0:
            signals.append("🔴 量增價跌（賣壓沉重）")
            score_pts.append(-15)
        elif vol_ratio < 0.5 and chg > 0:
            signals.append("🟡 縮量上漲（動能不足，需觀察）")
            score_pts.append(0)
    else:
        result["volume_ratio"] = None

    # ── 綜合評分 ─────────────────────────────────────────────────────────────
    base  = 50
    total = base + sum(score_pts)
    total = max(0, min(100, total))
    result["score"]   = total
    result["signals"] = signals

    if total >= 75:
        result["summary"] = "技術面強勢，多項指標確認做多"
    elif total >= 60:
        result["summary"] = "技術面偏多，趨勢向上但需確認量能"
    elif total >= 40:
        result["summary"] = "技術面中性，觀望為宜"
    elif total >= 25:
        result["summary"] = "技術面偏弱，避免追高"
    else:
        result["summary"] = "技術面空頭，建議迴避"

    return result


def calc_sector_technicals(sector: str) -> dict:
    """產業指數技術強度（簡化版）"""
    from database import get_sector_trend
    trend = get_sector_trend(sector, days=10)

    score = 50
    if trend["trend"] == "強勢":
        score = 75
    elif trend["trend"] == "弱勢":
        score = 25

    return {
        "score":    score,
        "trend":    trend["trend"],
        "avg_5d":   trend.get("avg_pct", 0),
        "up_days":  trend.get("up_days", 0),
    }
