"""
洞察引擎 - 從「狀態」提煉「變化」
解決報告流水帳問題：輪動、資金集中、量價背離、上中下游鏈動、主題聚合

所有分析只用既有數據（FinMind 抓的個股價格+三大法人），不需新資料來源。
"""

import logging
from data.stock_universe import STOCK_UNIVERSE, THEMES, get_all_stocks
from database import get_prev_sector_scores, get_sector_signal_history

log = logging.getLogger(__name__)


def _pct(s) -> float:
    try:
        return float(str(s).replace("%", "").replace("+", ""))
    except (ValueError, TypeError):
        return 0.0


def _close(s) -> float:
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0


# ── 1. 族群輪動（今日 vs 昨日） ────────────────────────────────────────────────

def sector_rotation(sector_signals: list[dict], date_str: str) -> dict:
    """
    比較今日族群分數與前一交易日，找出轉強/轉弱與連續紀錄。
    回傳 {"available": bool, "improving": [...], "weakening": [...], "streaks": [...]}
    """
    prev = get_prev_sector_scores(date_str)
    if not prev:
        return {"available": False, "improving": [], "weakening": [], "streaks": []}

    deltas = []
    for rank, s in enumerate(sector_signals, 1):
        name = s.get("sector", "")
        p = prev.get(name)
        if not p:
            continue
        deltas.append({
            "sector":      name,
            "score":       s.get("score", 0),
            "signal":      s.get("signal", ""),
            "score_delta": s.get("score", 0) - (p["score"] or 0),
            "rank_delta":  (p["rank"] or rank) - rank,  # 正數 = 排名上升
            "new_green":   s.get("signal") == "🟢" and p["signal"] != "🟢",
            "new_red":     s.get("signal") == "🔴" and p["signal"] != "🔴",
        })

    improving = sorted([d for d in deltas if d["score_delta"] > 0],
                       key=lambda x: x["score_delta"], reverse=True)[:3]
    weakening = sorted([d for d in deltas if d["score_delta"] < 0],
                       key=lambda x: x["score_delta"])[:3]

    # 連續綠燈天數（≥2 天才值得講）
    history = get_sector_signal_history(days=10)
    streaks = []
    for s in sector_signals:
        name = s.get("sector", "")
        sigs = history.get(name, [])
        run = 0
        for sig in sigs:
            if sig == "🟢":
                run += 1
            else:
                break
        if run >= 2:
            streaks.append({"sector": name, "days": run})
    streaks.sort(key=lambda x: x["days"], reverse=True)

    return {"available": True, "improving": improving,
            "weakening": weakening, "streaks": streaks[:5]}


# ── 2. 資金集中度 ──────────────────────────────────────────────────────────────

def money_concentration(inst_data: list[dict], stock_signals: list[dict]) -> dict:
    """
    外資資金往哪些族群集中（以股數×收盤價估算金額），加上族群內買超廣度。
    回傳 {"top_inflow": [...], "top_outflow": [...], "total_in_b": float}
    """
    code_close = {s.get("code", ""): _close(s.get("close")) for s in stock_signals}
    code_to_sector = {
        code: sec
        for sec, info in STOCK_UNIVERSE.items()
        for code in info["stocks"]
    }

    flows: dict[str, dict] = {}
    for row in inst_data:
        code = row.get("code", "")
        sec = code_to_sector.get(code, "")
        if not sec:
            continue
        value = row.get("foreign_net", 0) * code_close.get(code, 60)  # 元
        f = flows.setdefault(sec, {"value": 0.0, "buy_cnt": 0, "total_cnt": 0})
        f["value"] += value
        f["total_cnt"] += 1
        if row.get("foreign_net", 0) > 0:
            f["buy_cnt"] += 1

    total_in = sum(f["value"] for f in flows.values() if f["value"] > 0)
    rows = []
    for sec, f in flows.items():
        rows.append({
            "sector":   sec,
            "value_b":  round(f["value"] / 1e8, 1),       # 億元
            "share":    round(f["value"] / total_in * 100) if total_in > 0 and f["value"] > 0 else 0,
            "breadth":  f"{f['buy_cnt']}/{f['total_cnt']}",
            "breadth_pct": round(f["buy_cnt"] / f["total_cnt"] * 100) if f["total_cnt"] else 0,
        })

    top_inflow  = sorted([r for r in rows if r["value_b"] > 0],
                         key=lambda x: x["value_b"], reverse=True)[:3]
    top_outflow = sorted([r for r in rows if r["value_b"] < 0],
                         key=lambda x: x["value_b"])[:3]

    return {"top_inflow": top_inflow, "top_outflow": top_outflow,
            "total_in_b": round(total_in / 1e8, 1)}


# ── 3. 量價背離警示 ────────────────────────────────────────────────────────────

def divergences(stock_signals: list[dict], inst_data: list[dict]) -> list[dict]:
    """
    抓兩種背離（以金額 3000 萬為門檻）：
      出貨嫌疑：股價漲 ≥1% 但外資大賣
      逆勢吸籌：股價跌 ≤-1% 但外資大買
    """
    code_inst = {r.get("code", ""): r for r in inst_data}
    out = []
    for s in stock_signals:
        code = s.get("code", "")
        chg = _pct(s.get("change_pct"))
        inst = code_inst.get(code)
        if not inst:
            continue
        value = inst.get("foreign_net", 0) * _close(s.get("close"))
        if chg >= 1.0 and value <= -3e7:
            out.append({"code": code, "name": s.get("name", ""), "type": "出貨嫌疑",
                        "desc": f"漲{chg:+.1f}% 但外資賣超 {abs(value)/1e8:.1f}億"})
        elif chg <= -1.0 and value >= 3e7:
            out.append({"code": code, "name": s.get("name", ""), "type": "逆勢吸籌",
                        "desc": f"跌{chg:+.1f}% 但外資買超 {value/1e8:.1f}億"})
    # 出貨排前面（風險優先）
    out.sort(key=lambda x: 0 if x["type"] == "出貨嫌疑" else 1)
    return out[:6]


# ── 4. 上中下游鏈動 ────────────────────────────────────────────────────────────

def chain_analysis(stock_signals: list[dict]) -> list[dict]:
    """
    依 group（半導體/AI雲端/電動車…）檢查上中下游平均分數，
    偵測「上游領漲、中下游未跟」這類早期循環訊號。
    """
    universe = get_all_stocks()
    groups: dict[str, dict[str, list[int]]] = {}
    for s in stock_signals:
        info = universe.get(s.get("code", ""))
        if not info:
            continue
        g = info.get("group", "")
        chain = info.get("chain", "—")
        if not g or chain not in ("上游", "中游", "下游"):
            continue
        groups.setdefault(g, {}).setdefault(chain, []).append(s.get("score", 0))

    findings = []
    for g, chains in groups.items():
        avgs = {c: sum(v) / len(v) for c, v in chains.items() if v}
        if len(avgs) < 2:
            continue
        up = avgs.get("上游")
        down = avgs.get("下游", avgs.get("中游"))
        if up is None or down is None:
            continue
        if up - down >= 12:
            findings.append({"group": g, "pattern": "上游領漲",
                             "desc": f"{g}：上游平均{up:.0f}分 vs 中下游{down:.0f}分，資金先卡位上游"})
        elif down - up >= 12:
            findings.append({"group": g, "pattern": "下游領漲",
                             "desc": f"{g}：中下游平均{down:.0f}分 vs 上游{up:.0f}分，需求端先動"})
    return findings


# ── 5. 主題聚合 ────────────────────────────────────────────────────────────────

def theme_scores(sector_signals: list[dict]) -> list[dict]:
    """8 個主題鏈（AI完整供應鏈等）的整體強弱。"""
    sec_score = {s.get("sector", ""): s.get("score", 0) for s in sector_signals}
    sec_signal = {s.get("sector", ""): s.get("signal", "") for s in sector_signals}
    out = []
    for theme, members in THEMES.items():
        scores = [sec_score[m] for m in members if m in sec_score]
        if not scores:
            continue
        avg = sum(scores) / len(scores)
        green = sum(1 for m in members if sec_signal.get(m) == "🟢")
        sig = "🟢" if avg >= 60 else ("🟡" if avg >= 40 else "🔴")
        out.append({"theme": theme, "score": round(avg), "signal": sig,
                    "green_count": green, "member_count": len(scores)})
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


# ── 整合入口 ──────────────────────────────────────────────────────────────────

def compute_insights(date_str: str, sector_signals: list[dict],
                     stock_signals: list[dict], inst_data: list[dict]) -> dict:
    """一次計算全部洞察，回傳給 AI prompt 與報告用。"""
    return {
        "rotation":      sector_rotation(sector_signals, date_str),
        "concentration": money_concentration(inst_data, stock_signals),
        "divergences":   divergences(stock_signals, inst_data),
        "chains":        chain_analysis(stock_signals),
        "themes":        theme_scores(sector_signals),
    }


def insights_to_text(insights: dict) -> str:
    """把洞察整理成給 AI 的文字 context。"""
    lines = []

    rot = insights["rotation"]
    if rot["available"]:
        if rot["improving"]:
            lines.append("【今日轉強】" + "；".join(
                f"{d['sector']}（分數{d['score_delta']:+d}、排名{'升' if d['rank_delta']>0 else '持平'}"
                + ("、新轉綠燈" if d["new_green"] else "") + "）"
                for d in rot["improving"]))
        if rot["weakening"]:
            lines.append("【今日轉弱】" + "；".join(
                f"{d['sector']}（分數{d['score_delta']:+d}"
                + ("、跌出綠燈" if d["new_red"] else "") + "）"
                for d in rot["weakening"]))
        if rot["streaks"]:
            lines.append("【連續強勢】" + "；".join(
                f"{s['sector']}連{s['days']}日綠燈" for s in rot["streaks"][:3]))
    else:
        lines.append("【輪動】歷史資料累積中，今日無法比較昨日。")

    con = insights["concentration"]
    if con["top_inflow"]:
        lines.append("【外資資金集中】" + "；".join(
            f"{r['sector']} +{r['value_b']}億（占買超{r['share']}%、族群內{r['breadth']}檔被買）"
            for r in con["top_inflow"]))
    if con["top_outflow"]:
        lines.append("【外資撤出】" + "；".join(
            f"{r['sector']} {r['value_b']}億" for r in con["top_outflow"]))

    if insights["divergences"]:
        lines.append("【量價背離警示】" + "；".join(
            f"{d['name']}（{d['type']}：{d['desc']}）" for d in insights["divergences"][:4]))

    for f in insights["chains"]:
        lines.append(f"【鏈動訊號】{f['desc']}")

    themes = insights["themes"]
    if themes:
        lines.append("【主題強弱】" + "；".join(
            f"{t['theme']}{t['signal']}{t['score']}分" for t in themes))

    return "\n".join(lines)
