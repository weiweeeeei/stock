"""
台股日報 reporter v3
- 全部 30 個細分產業強弱排行（可展開看個股）
- 強勢 TOP5 / 轉弱 TOP5 卡片
- 個股燈號詳細列表（Tab 切換）
- 詳細報告 Tab
"""

from datetime import datetime
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "data"))


def _pc(pct_str):
    s = str(pct_str)
    try:
        return "#39d98a" if float(s.replace("+","").replace("%","")) > 0 else "#ff4d6d"
    except:
        return "#5a6080"

def _bar(score, color, w=60):
    fw = round(score / 100 * w)
    return (f'<div style="background:#0d0f18;height:4px;border-radius:2px;'
            f'width:{w}px;display:inline-block;vertical-align:middle;">'
            f'<div style="background:{color};height:4px;border-radius:2px;width:{fw}px;"></div></div>')

def _dots(up_days, total=5):
    return "".join(
        f'<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
        f'background:{"#39d98a" if i < up_days else "#252838"};margin-right:2px;"></span>'
        for i in range(total)
    )

def _badge(consec):
    if consec >= 5:
        return f'<span style="font-size:9px;color:#e8c84a;border:1px solid #e8c84a55;padding:1px 5px;border-radius:2px;margin-left:3px;">外資連買{consec}日</span>'
    if consec >= 3:
        return f'<span style="font-size:9px;color:#5a6080;border:1px solid #252838;padding:1px 5px;border-radius:2px;margin-left:3px;">外資買{consec}日</span>'
    return ""


def generate_report(date_str, market_signal, sector_signals, stock_signals, claude_summary, sector_stock_map):
    from stock_universe import STOCK_UNIVERSE

    date_display = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
    wday = ["一","二","三","四","五","六","日"][datetime.strptime(date_str, "%Y%m%d").weekday()]

    # 市場
    ms  = market_signal.get("score", 50)
    ml  = market_signal.get("label", "市場震盪")
    mc  = market_signal.get("color", "#e8c84a")
    mad = market_signal.get("advice", "")
    f5d = market_signal.get("foreign_5d_b", 0)
    up5 = market_signal.get("up_days_5d", 0)
    offset = 283 - (ms / 100 * 283)

    # 補齊 sector_signals 欄位
    for s in sector_signals:
        info = STOCK_UNIVERSE.get(s["sector"], {})
        s.setdefault("group", info.get("group",""))
        chains = set(st.get("chain","") for st in info.get("stocks",{}).values())
        chains -= {"—",""}
        s.setdefault("chain_dist", "→".join(c for c in ["上游","中游","下游"] if c in chains))
        t = s.get("trend_5d","震盪")
        s.setdefault("up_days", 4 if t=="強勢" else (1 if t=="弱勢" else 2))

    sorted_desc = sorted(sector_signals, key=lambda x: x["score"], reverse=True)
    sorted_asc  = sorted(sector_signals, key=lambda x: x["score"])
    strong5 = sorted_desc[:5]
    weak5   = sorted_asc[:5]

    green_stocks  = [s for s in stock_signals if s.get("signal")=="🟢"]
    yellow_stocks = [s for s in stock_signals if s.get("signal")=="🟡"][:8]

    total_sec  = len(sector_signals)
    green_sec  = sum(1 for s in sector_signals if s["signal"]=="🟢")
    yellow_sec = sum(1 for s in sector_signals if s["signal"]=="🟡")
    red_sec    = sum(1 for s in sector_signals if s["signal"]=="🔴")
    green_st   = len(green_stocks)
    total_st   = len(stock_signals)

    # ── 產業列（可展開） ──────────────────────────────────────────────────────
    def stock_detail_rows(stocks):
        if not stocks:
            return '<div style="padding:10px 16px;color:#5a6080;font-size:12px;">暫無個股數據</div>'
        html = ""
        for s in sorted(stocks, key=lambda x: x.get("score",50), reverse=True):
            sig = s.get("signal","🟡"); code = s.get("code",""); name = s.get("name","")
            pct = s.get("change_pct","—"); close = s.get("close",""); score = s.get("score",50)
            line = s.get("one_line",""); chain = s.get("chain",""); sub = s.get("sub","")
            sc = s.get("signal_color","#e8c84a")
            consec = s.get("consecutive_foreign_buy",0)
            html += f"""
            <div style="display:flex;align-items:center;gap:10px;padding:9px 16px;border-bottom:1px solid #0e1018;">
              <span style="font-size:15px;flex-shrink:0;">{sig}</span>
              <div style="width:80px;flex-shrink:0;">
                <div style="font-family:monospace;font-size:10px;color:#e8c84a;">{code} {_badge(consec)}</div>
                <div style="font-size:12px;font-weight:700;color:#ddddf0;">{name}</div>
              </div>
              <div style="width:44px;flex-shrink:0;text-align:right;">
                <div style="font-family:monospace;font-size:12px;font-weight:700;color:{_pc(pct)};">{pct}</div>
                <div style="font-size:9px;color:#5a6080;">{close}元</div>
              </div>
              <div style="flex-shrink:0;">{_bar(score,sc,48)}<div style="font-size:9px;color:#5a6080;">{score}分</div></div>
              <div style="flex:1;min-width:0;">
                <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:2px;">
                  <span style="font-size:9px;color:#5a6080;background:#151720;padding:1px 4px;border-radius:2px;">{chain}</span>
                  <span style="font-size:9px;color:#5a6080;background:#151720;padding:1px 4px;border-radius:2px;">{sub}</span>
                </div>
                <div style="font-size:11px;color:#9090a8;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{line}</div>
              </div>
            </div>"""
        return html

    def sector_row(s, rank, is_last=False):
        sid = f"sec_{rank}"
        sig = s["signal"]; sec = s["sector"]; group = s.get("group","")
        pct = s.get("change_pct","—"); score = s.get("score",50)
        trend = s.get("trend_5d","—"); up_d = s.get("up_days",2)
        chain = s.get("chain_dist",""); sc = s.get("signal_color","#e8c84a")
        inst = s.get("inst_flow",0)
        inst_txt = f'外資{inst/1000000:+.1f}M' if inst else ""
        stks = sector_stock_map.get(sec,[])
        green_n = sum(1 for st in stks if st.get("signal")=="🟢")
        total_n = len(stks)
        detail = stock_detail_rows(stks)
        return f"""
        <div style="border-bottom:{'none' if is_last else '1px solid #0e1018'};">
          <div onclick="toggle('{sid}')"
               style="display:flex;align-items:center;gap:10px;padding:11px 16px;cursor:pointer;"
               onmouseover="this.style.background='#0f111e'" onmouseout="this.style.background='transparent'">
            <div style="font-family:monospace;font-size:10px;color:#3a3d52;width:22px;flex-shrink:0;text-align:right;">{rank}</div>
            <div style="font-size:17px;flex-shrink:0;">{sig}</div>
            <div style="flex:1;min-width:0;">
              <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                <span style="font-weight:700;font-size:13px;color:#ddddf0;">{sec}</span>
                <span style="font-size:9px;color:#5a6080;background:#151720;padding:1px 5px;border-radius:3px;">{group}</span>
                {f'<span style="font-size:9px;color:#5a6080;">{chain}</span>' if chain else ""}
              </div>
              <div style="margin-top:3px;display:flex;align-items:center;gap:8px;">
                {_dots(up_d)}
                <span style="font-size:10px;color:#5a6080;">近5日{trend}</span>
                {f'<span style="font-size:10px;color:#5a6080;">{inst_txt}</span>' if inst_txt else ""}
              </div>
            </div>
            <div style="font-family:monospace;font-weight:700;font-size:14px;color:{_pc(pct)};flex-shrink:0;min-width:52px;text-align:right;">{pct}</div>
            <div style="flex-shrink:0;">{_bar(score,sc,52)}<div style="font-size:9px;color:#5a6080;">{score}分</div></div>
            <div style="font-size:10px;color:#5a6080;flex-shrink:0;min-width:48px;text-align:right;">🟢{green_n}/{total_n}</div>
            <div id="arr_{sid}" style="font-size:10px;color:#3a3d52;flex-shrink:0;transition:transform .2s;">▶</div>
          </div>
          <div id="{sid}" style="display:none;background:#080910;border-top:1px solid #0e1018;">
            <div style="padding:7px 16px;font-size:9px;color:#5a6080;letter-spacing:.1em;border-bottom:1px solid #0e1018;">
              {sec} · {total_n} 檔個股
            </div>
            {detail}
          </div>
        </div>"""

    all_rows = "".join(sector_row(s, i+1, i==len(sorted_desc)-1) for i,s in enumerate(sorted_desc))

    # ── TOP5 卡片 ─────────────────────────────────────────────────────────────
    def top5_card(s, mode):
        accent = "#39d98a" if mode=="strong" else "#ff4d6d"
        pct = s.get("change_pct","—")
        stks = sector_stock_map.get(s["sector"],[])
        best = sorted(stks, key=lambda x: x.get("score",0), reverse=True)[:3]
        best_html = "".join(
            f'<div style="font-size:10px;color:#8888a0;margin-top:3px;">'
            f'{b.get("signal","")} <span style="font-family:monospace;color:#e8c84a;">{b.get("code","")}</span>'
            f' {b.get("name","")} <span style="color:{_pc(b.get("change_pct",""))};">{b.get("change_pct","")}</span>'
            f'</div>'
            for b in best
        )
        return f"""
        <div style="background:#0d0f1a;border:1px solid #1a1d28;border-top:2px solid {accent};padding:14px 16px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
            <div>
              <span style="font-size:15px;">{s['signal']}</span>
              <span style="font-weight:700;font-size:13px;color:#ddddf0;margin-left:6px;">{s['sector']}</span>
              <span style="font-size:9px;color:#5a6080;background:#151720;padding:1px 5px;border-radius:3px;margin-left:4px;">{s.get('group','')}</span>
            </div>
            <div style="font-family:monospace;font-weight:800;font-size:15px;color:{_pc(pct)};">{pct}</div>
          </div>
          <div style="margin-bottom:8px;">{_dots(s.get('up_days',2))}<span style="font-size:10px;color:#5a6080;margin-left:6px;">近5日{s.get('trend_5d','')}</span></div>
          <div style="border-top:1px solid #151720;padding-top:8px;">
            <div style="font-size:9px;color:{accent};letter-spacing:.1em;margin-bottom:4px;">代表個股</div>
            {best_html or '<div style="font-size:10px;color:#5a6080;">—</div>'}
          </div>
        </div>"""

    strong_cards = "".join(top5_card(s,"strong") for s in strong5)
    weak_cards   = "".join(top5_card(s,"weak")   for s in weak5)

    # ── 個股全列表 ─────────────────────────────────────────────────────────────
    def stock_full_row(s):
        sig = s.get("signal","🟡"); code = s.get("code",""); name = s.get("name","")
        pct = s.get("change_pct","—"); close = s.get("close",""); score = s.get("score",50)
        line = s.get("one_line",""); sector = s.get("sector",""); chain = s.get("chain","")
        sc = s.get("signal_color","#e8c84a"); consec = s.get("consecutive_foreign_buy",0)
        reasons = s.get("reasons",[])
        reasons_html = "".join(f'<div style="font-size:10px;color:#5a6080;margin-top:1px;">{r}</div>' for r in reasons[:3])
        return f"""
        <tr style="border-bottom:1px solid #0e1018;">
          <td style="padding:12px 8px 12px 4px;white-space:nowrap;">
            <div style="display:flex;align-items:center;gap:8px;">
              <span style="font-size:19px;">{sig}</span>
              <div>
                <div style="display:flex;align-items:center;">{f'<span style="font-family:monospace;font-size:11px;color:#e8c84a;">{code}</span>'}{_badge(consec)}</div>
                <div style="font-weight:700;font-size:13px;color:#ddddf0;">{name}</div>
                <div style="font-size:10px;color:#5a6080;">{sector} · {chain}</div>
              </div>
            </div>
          </td>
          <td style="padding:12px 8px;text-align:right;white-space:nowrap;">
            <div style="font-family:monospace;font-weight:800;font-size:15px;color:{_pc(pct)};">{pct}</div>
            <div style="font-size:10px;color:#5a6080;">{close} 元</div>
          </td>
          <td style="padding:12px 8px;white-space:nowrap;">
            {_bar(score,sc,64)}<div style="font-size:9px;color:#5a6080;font-family:monospace;">{score}/100</div>
          </td>
          <td style="padding:12px 8px;">
            <div style="font-size:12px;color:#a0a4b8;line-height:1.5;">{line}</div>
            {reasons_html}
          </td>
        </tr>"""

    green_rows  = "".join(stock_full_row(s) for s in green_stocks)
    yellow_rows = "".join(stock_full_row(s) for s in yellow_stocks)
    no_stock = '<tr><td colspan="4" style="padding:24px;text-align:center;color:#5a6080;font-size:13px;">數據累積中，明日再看</td></tr>'

    paras = "".join(
        f'<p style="margin:0 0 12px;font-size:13px;line-height:1.85;color:#8890b0;">{p.strip()}</p>'
        for p in claude_summary.split("\n") if p.strip()
    )

    mkt_sigs = market_signal.get("signals",[])
    pills = "".join(
        f'<span style="background:#1a1d28;border:1px solid #252838;color:#8890b0;padding:3px 10px;border-radius:20px;font-size:11px;">{s}</span>'
        for s in mkt_sigs
    )

    return f"""<!DOCTYPE html>
<html lang="zh-TW"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>台股日報 {date_display}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{background:#0a0b12;font-family:system-ui,'PingFang TC','Microsoft JhengHei',sans-serif;color:#ddddf0;}}
.wrap{{max-width:960px;margin:0 auto;}}
.tab{{display:none;}}.tab.active{{display:block;}}
.tabbar button{{background:none;border:none;padding:10px 18px;font-size:13px;color:#5a6080;
               cursor:pointer;border-bottom:2px solid transparent;font-family:inherit;transition:all .2s;}}
.tabbar button.active{{color:#e8c84a;border-bottom-color:#e8c84a;}}
.tabbar button:hover{{color:#ddddf0;}}
@media(max-width:640px){{.two-col{{grid-template-columns:1fr !important;}}}}
</style>
<script>
function toggle(id){{
  var el=document.getElementById(id),arr=document.getElementById('arr_'+id);
  if(!el)return;
  var open=el.style.display!=='none';
  el.style.display=open?'none':'block';
  arr.style.transform=open?'':'rotate(90deg)';
  arr.style.color=open?'#3a3d52':'#e8c84a';
}}
function switchTab(n){{
  document.querySelectorAll('.tab').forEach(e=>e.classList.remove('active'));
  document.querySelectorAll('.tabbar button').forEach(e=>e.classList.remove('active'));
  document.getElementById('tab_'+n).classList.add('active');
  document.getElementById('btn_'+n).classList.add('active');
}}
function expandAll(expand){{
  for(var i=1;i<={total_sec};i++){{
    var el=document.getElementById('sec_'+i);
    var arr=document.getElementById('arr_sec_'+i);
    if(el){{el.style.display=expand?'block':'none';}}
    if(arr){{arr.style.transform=expand?'rotate(90deg)':'';arr.style.color=expand?'#e8c84a':'#3a3d52';}}
  }}
}}
</script>
</head>
<body>
<div class="wrap">

<!-- HEADER -->
<div style="background:#0d0f1a;border-bottom:2px solid {mc};padding:18px 24px;
            display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
  <div>
    <div style="font-size:9px;letter-spacing:.25em;color:#5a6080;text-transform:uppercase;">台股強勢產業日報</div>
    <div style="font-size:22px;font-weight:900;color:#fff;margin-top:2px;">
      {date_display} <span style="font-size:13px;font-weight:400;color:#5a6080;margin-left:6px;">星期{wday}</span>
    </div>
    <div style="font-size:9px;color:#5a6080;margin-top:3px;">TWSE + TPEx 官方數據</div>
  </div>
  <div style="display:flex;align-items:center;gap:14px;">
    <svg width="70" height="70" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="45" fill="none" stroke="#1a1d28" stroke-width="10"/>
      <circle cx="50" cy="50" r="45" fill="none" stroke="{mc}" stroke-width="10"
              stroke-dasharray="283" stroke-dashoffset="{offset:.1f}"
              stroke-linecap="round" transform="rotate(-90 50 50)"/>
      <text x="50" y="46" text-anchor="middle" fill="{mc}" font-size="20" font-weight="900">{ms}</text>
      <text x="50" y="61" text-anchor="middle" fill="#5a6080" font-size="9">/100</text>
    </svg>
    <div>
      <div style="font-size:20px;font-weight:900;color:{mc};">{ml}</div>
      <div style="font-size:11px;color:#8890b0;margin-top:2px;">{mad}</div>
      <div style="font-size:10px;color:#5a6080;margin-top:3px;">
        外資5日 <span style="color:{'#39d98a' if f5d>=0 else '#ff4d6d'};font-weight:700;">{f5d:+.1f}億</span>
        &nbsp;·&nbsp; 上漲<span style="font-weight:700;color:#ddddf0;"> {up5}/5</span>天
      </div>
    </div>
  </div>
</div>

<!-- 統計列 -->
<div style="background:#0d0f1a;border-bottom:1px solid #151720;padding:10px 24px;
            display:flex;gap:20px;flex-wrap:wrap;align-items:center;">
  <div style="font-size:11px;color:#5a6080;">
    族群掃描：<span style="color:#39d98a;font-weight:700;">🟢{green_sec}</span>
    <span style="color:#e8c84a;"> 🟡{yellow_sec}</span>
    <span style="color:#ff4d6d;"> 🔴{red_sec}</span>
    <span style="color:#5a6080;"> ／共{total_sec}個</span>
  </div>
  <div style="font-size:11px;color:#5a6080;">
    個股：<span style="color:#39d98a;font-weight:700;">🟢{green_st}檔強力做多</span> ／共{total_st}檔
  </div>
  {f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-left:auto;">{pills}</div>' if pills else ''}
</div>

<!-- TAB BAR -->
<div class="tabbar" style="background:#0d0f1a;border-bottom:1px solid #151720;display:flex;padding:0 16px;overflow-x:auto;">
  <button id="btn_overview" class="active" onclick="switchTab('overview')">📊 今日總覽</button>
  <button id="btn_sectors"  onclick="switchTab('sectors')">🏭 全族群排行</button>
  <button id="btn_stocks"   onclick="switchTab('stocks')">📈 個股訊號</button>
  <button id="btn_report"   onclick="switchTab('report')">📋 詳細報告</button>
</div>

<!-- TAB: 今日總覽 -->
<div id="tab_overview" class="tab active" style="padding:20px 24px;">
  <!-- 圖例 -->
  <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px;padding:12px 16px;background:#0d0f1a;border:1px solid #151720;">
    <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:15px;">🟢</span><span style="font-size:12px;color:#39d98a;font-weight:700;">強力做多</span><span style="font-size:11px;color:#5a6080;">多維度對齊，可積極布局</span></div>
    <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:15px;">🟡</span><span style="font-size:12px;color:#e8c84a;font-weight:700;">觀察等待</span><span style="font-size:11px;color:#5a6080;">訊號分歧，等確認再進場</span></div>
    <div style="display:flex;align-items:center;gap:6px;"><span style="font-size:15px;">🔴</span><span style="font-size:12px;color:#ff4d6d;font-weight:700;">暫時迴避</span><span style="font-size:11px;color:#5a6080;">空頭訊號為主</span></div>
  </div>
  <!-- TOP5 -->
  <div class="two-col" style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
        <div style="width:3px;height:16px;background:#39d98a;border-radius:2px;"></div>
        <span style="font-size:11px;font-weight:700;color:#39d98a;letter-spacing:.15em;">強勢族群 TOP 5</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px;">{strong_cards}</div>
    </div>
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
        <div style="width:3px;height:16px;background:#ff4d6d;border-radius:2px;"></div>
        <span style="font-size:11px;font-weight:700;color:#ff4d6d;letter-spacing:.15em;">轉弱族群 TOP 5</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:10px;">{weak_cards}</div>
    </div>
  </div>
  <!-- 操作建議 -->
  <div style="background:#0d0f1a;border:1px solid #1a1d28;border-left:3px solid {mc};padding:16px 20px;">
    <div style="font-size:10px;font-weight:700;color:#e8c84a;letter-spacing:.15em;text-transform:uppercase;margin-bottom:12px;">今日操作建議</div>
    {paras}
  </div>
</div>

<!-- TAB: 全族群排行 -->
<div id="tab_sectors" class="tab">
  <div style="padding:12px 24px;background:#0d0f1a;border-bottom:1px solid #151720;
              display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
    <div style="font-size:11px;color:#5a6080;">共 {total_sec} 個細分族群 · 點擊任一列展開個股明細</div>
    <div style="display:flex;gap:8px;">
      <button onclick="expandAll(true)"  style="background:none;border:1px solid #252838;color:#8890b0;padding:4px 12px;font-size:11px;cursor:pointer;font-family:inherit;">全部展開</button>
      <button onclick="expandAll(false)" style="background:none;border:1px solid #252838;color:#8890b0;padding:4px 12px;font-size:11px;cursor:pointer;font-family:inherit;">全部收合</button>
    </div>
  </div>
  <div style="display:flex;gap:10px;padding:7px 16px;background:#080910;border-bottom:1px solid #0e1018;">
    <div style="width:22px;"></div><div style="width:20px;"></div>
    <div style="flex:1;font-size:9px;color:#5a6080;letter-spacing:.1em;">族群</div>
    <div style="font-size:9px;color:#5a6080;min-width:52px;text-align:right;">漲跌</div>
    <div style="font-size:9px;color:#5a6080;width:56px;">強度</div>
    <div style="font-size:9px;color:#5a6080;min-width:48px;text-align:right;">個股</div>
    <div style="width:14px;"></div>
  </div>
  {all_rows}
</div>

<!-- TAB: 個股訊號 -->
<div id="tab_stocks" class="tab" style="padding:20px 24px;">
  {f'<div style="margin-bottom:20px;"><div style="font-size:10px;color:#39d98a;letter-spacing:.15em;font-weight:700;margin-bottom:10px;">🟢 強力做多 — {len(green_stocks)} 檔</div><table style="width:100%;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid #151720;"><th style="padding:6px 8px 6px 4px;text-align:left;font-size:9px;color:#5a6080;letter-spacing:.1em;">個股</th><th style="padding:6px 8px;text-align:right;font-size:9px;color:#5a6080;">漲跌</th><th style="padding:6px 8px;font-size:9px;color:#5a6080;">評分</th><th style="padding:6px 8px;font-size:9px;color:#5a6080;">理由</th></tr></thead><tbody>{green_rows or no_stock}</tbody></table></div>' if True else ''}
  {f'<div><div style="font-size:10px;color:#e8c84a;letter-spacing:.15em;font-weight:700;margin-bottom:10px;">🟡 觀察等待 — {len(yellow_stocks)} 檔（前8名）</div><table style="width:100%;border-collapse:collapse;"><tbody>{yellow_rows}</tbody></table></div>' if yellow_stocks else ''}
</div>

<!-- TAB: 詳細報告 -->
<div id="tab_report" class="tab" style="padding:24px;">
  <div style="background:#0d0f1a;border:1px solid #1a1d28;padding:24px;font-size:13px;line-height:1.9;color:#8890b0;">
    <div style="font-size:10px;color:#e8c84a;letter-spacing:.15em;font-weight:700;margin-bottom:16px;">AI 深度分析報告 · {date_display}</div>
    {paras}
    <div style="margin-top:24px;padding-top:20px;border-top:1px solid #1a1d28;">
      <div style="font-size:10px;color:#39d98a;letter-spacing:.15em;font-weight:700;margin-bottom:12px;">今日強勢族群完整列表</div>
      {"".join(f'<div style="margin-bottom:8px;padding:10px 14px;background:#080910;border-left:2px solid #39d98a;"><span style="font-weight:700;color:#ddddf0;">{s["sector"]}</span><span style="font-family:monospace;color:#39d98a;margin-left:8px;">{s.get("change_pct","")}</span><span style="font-size:10px;color:#5a6080;margin-left:8px;">{s.get("group","")} · 近5日{s.get("trend_5d","")}</span></div>' for s in strong5)}
    </div>
    <div style="margin-top:16px;padding-top:16px;border-top:1px solid #1a1d28;">
      <div style="font-size:10px;color:#ff4d6d;letter-spacing:.15em;font-weight:700;margin-bottom:12px;">今日轉弱族群完整列表</div>
      {"".join(f'<div style="margin-bottom:8px;padding:10px 14px;background:#080910;border-left:2px solid #ff4d6d;"><span style="font-weight:700;color:#ddddf0;">{s["sector"]}</span><span style="font-family:monospace;color:#ff4d6d;margin-left:8px;">{s.get("change_pct","")}</span><span style="font-size:10px;color:#5a6080;margin-left:8px;">{s.get("group","")} · 近5日{s.get("trend_5d","")}</span></div>' for s in weak5)}
    </div>
  </div>
</div>

<!-- FOOTER -->
<div style="padding:12px 24px;border-top:1px solid #0e1018;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;">
  <div style="font-size:9px;color:#3a3d52;">台股強勢產業日報 · {date_display} · TWSE + TPEx 官方數據</div>
  <div style="font-size:9px;color:#3a3d52;">⚠ 僅供參考，不構成投資建議</div>
</div>

</div>
</body></html>"""
