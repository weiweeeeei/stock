"""
台股強勢產業分析器 v3
架構：官方數據 → 存DB → 技術/法人/趨勢計算 → 燈號 → 極簡報告
"""

import os, sys, json, logging, smtplib, datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from google import genai
from google.genai import types

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "data"))

from stock_universe import STOCK_UNIVERSE, get_all_stocks
from fetcher   import fetch_all_market_data, build_context_for_claude
from database  import init_db, save_market_data, get_market_trend
from signals   import score_market, score_sectors, score_stock, score_sectors_from_stocks
from reporter  import generate_report
from insights  import compute_insights, insights_to_text
from database  import save_sector_scores

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

GEMINI_API_KEY  = os.environ["GEMINI_API_KEY"]
GMAIL_USER      = os.environ["GMAIL_USER"]
GMAIL_APP_PWD   = os.environ["GMAIL_APP_PWD"]
RECIPIENT_EMAIL = os.environ.get("RECIPIENT_EMAIL", GMAIL_USER)
PAGES_URL       = os.environ.get("PAGES_URL", "https://weiweeeeei.github.io/stock/")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)


def get_claude_summary(date_str, market_signal, top_sectors, top_stocks, insights_text=""):
    green_s  = [s["sector"] for s in top_sectors if s["signal"] == "🟢"][:4]
    green_st = [f"{s['code']} {s['name']}（{s['one_line']}）"
                for s in top_stocks if s["signal"] == "🟢"][:4]
    prompt = f"""你是台股盤勢分析師。以下是今日量化系統的完整輸出：

市場燈號：{market_signal['label']}（{market_signal['score']}分）
強勢產業：{', '.join(green_s) or '無'}
綠燈個股：{chr(10).join(green_st) or '無'}

──系統洞察──
{insights_text or '（無額外洞察）'}

請用繁體中文寫今日盤勢解讀，分3段、共約200字：

第一段【今天哪裡不一樣】：只講「變化」——誰剛轉強、誰連續上榜、資金從哪流到哪。
不要重複排名清單，不要寫「市場震盪、謹慎操作」這種任何一天都成立的廢話。

第二段【焦點族群為什麼】：挑1-2個最值得注意的族群，講清楚邏輯
（例：外資錢集中+族群內買超廣度高=真行情；只有單一檔被拉=假突破）。
若有上中下游鏈動訊號，務必點出。

第三段【風險與明日觀察】：量價背離的具體個股警示優先講，
然後給一個明日「驗證點」（例：若XX族群明天量縮回檔則輪動失敗）。

語氣像資深操盤手跟同事覆盤，直接、具體、有數字，禁止空泛形容詞。"""
    try:
        resp = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=700,
                temperature=0.7,
            ),
        )
        return resp.text.strip()
    except Exception as e:
        log.warning(f"Gemini 呼叫失敗，使用後備摘要：{e}")
        return (
            f"【AI 摘要暫不可用】今日大盤：{market_signal['label']}"
            f"（{market_signal['score']}分）。建議：{market_signal['advice']}。"
            f"強勢產業：{', '.join(green_s) or '無'}。"
            f"請參考下方分頁的詳細燈號與排行。"
        )


_EMAIL_BANNER = """
<div style="background:#1a1d28;border:1px solid #39d98a;padding:14px 20px;
margin:0 0 16px;border-radius:8px;font-family:-apple-system,BlinkMacSystemFont,
'Segoe UI',Roboto,sans-serif;text-align:center;">
  <a href="{url}" style="color:#39d98a;font-weight:700;font-size:15px;
  text-decoration:none;">📱 點此查看完整網頁版（Email 版面如有跑掉以此為準）→</a>
</div>
"""


def send_email(html, date_str):
    dd = f"{date_str[:4]}/{date_str[4:6]}/{date_str[6:]}"
    # 把「網頁版」橫幅插到 <body> 開頭，讓 Gmail 不論怎麼處理 CSS 都看得到
    banner = _EMAIL_BANNER.format(url=PAGES_URL)
    if "<body" in html:
        email_html = html.replace("<body>", "<body>" + banner, 1)
    else:
        email_html = banner + html

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 台股日報 {dd}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(email_html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PWD)
        smtp.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
    log.info(f"✅ Email 已寄送至 {RECIPIENT_EMAIL}")


def main():
    log.info("=" * 55)
    log.info("台股日報系統 v3 啟動")
    init_db()

    log.info("\n[1/5] 抓取 TWSE + TPEx 官方數據...")
    market_data = fetch_all_market_data()
    date_str = market_data["date"]

    log.info("\n[2/5] 儲存至資料庫...")
    save_market_data(market_data)

    log.info("\n[3/5] 計算燈號...")
    mkt_signal = score_market(market_data)
    log.info(f"      市場：{mkt_signal['label']} ({mkt_signal['score']}分)")

    # 先嘗試用類股指數評分（舊 TWSE 直連方案）
    sector_signals = score_sectors(
        market_data.get("sector_twse", []),
        market_data.get("institutional_twse", []),
    )

    all_stocks_db = get_all_stocks()
    all_price = {s["code"]: s for s in
                 market_data.get("stocks_twse",[]) + market_data.get("stocks_tpex",[])}
    all_inst  = {s["code"]: s for s in market_data.get("institutional_twse",[])}

    stock_signals = []
    for code, info in all_stocks_db.items():
        price = all_price.get(code, {})
        if not price:
            continue
        inst = all_inst.get(code, {})
        sig = score_stock(code, {
            "name":    info["name"],
            "close":   price.get("close"),
            "change_pct": price.get("change_pct",""),
            "institutional": {
                "foreign_net": inst.get("foreign_net", 0),
                "trust_net":   inst.get("trust_net",   0),
                "dealer_net":  inst.get("dealer_net",  0),
            }
        })
        stock_signals.append(sig)

    stock_signals.sort(key=lambda x: x["score"], reverse=True)
    green_st = sum(1 for s in stock_signals if s["signal"] == "🟢")

    # 沒有類股指數時（FinMind 免費版），從個股訊號反推產業
    if not sector_signals:
        sector_signals = score_sectors_from_stocks(
            stock_signals,
            market_data.get("institutional_twse", []),
        )
    green_sec = sum(1 for s in sector_signals if s["signal"] == "🟢")
    log.info(f"      🟢產業 {green_sec}個  🟢個股 {green_st}檔")

    # 建立族群→個股對應表（報告展開用）
    code_to_sector = {
        code: sec
        for sec, info in STOCK_UNIVERSE.items()
        for code in info["stocks"]
    }
    sector_stock_map: dict[str, list] = {}
    for s in stock_signals:
        sec = code_to_sector.get(s.get("code",""), "")
        s["sector"] = sec  # 補上 sector 欄位給報告用
        if sec:
            sector_stock_map.setdefault(sec, []).append(s)

    # 洞察分析：輪動/資金集中/背離/鏈動/主題（先算再存今日分數，避免跟自己比）
    insights = compute_insights(
        date_str, sector_signals, stock_signals,
        market_data.get("institutional_twse", []),
    )
    save_sector_scores(date_str, sector_signals)
    rot = insights["rotation"]
    log.info(f"      洞察：轉強{len(rot['improving'])} 轉弱{len(rot['weakening'])} "
             f"背離{len(insights['divergences'])} 鏈動{len(insights['chains'])}")

    log.info("\n[4/5] AI 生成盤勢解讀...")
    summary = get_claude_summary(date_str, mkt_signal, sector_signals[:10],
                                 stock_signals[:10], insights_to_text(insights))

    log.info("\n[5/5] 生成並寄送報告...")
    html = generate_report(date_str, mkt_signal, sector_signals, stock_signals, summary,
                           sector_stock_map, insights=insights)

    out = Path(__file__).parent / f"reports/report_{date_str}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding="utf-8")

    # 同時寫到 public/ 給 GitHub Pages 用：index.html 是最新、{date}.html 是當天備份
    pub = Path(__file__).parent / "public"
    pub.mkdir(exist_ok=True)
    (pub / "index.html").write_text(html, encoding="utf-8")
    (pub / f"{date_str}.html").write_text(html, encoding="utf-8")
    log.info(f"      已寫入 public/index.html（GitHub Pages 用）")

    send_email(html, date_str)
    log.info(f"\n✅ 完成！")

if __name__ == "__main__":
    main()
