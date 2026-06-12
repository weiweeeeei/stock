# 台股強勢產業日報系統 — Claude Code Context

## 專案目的
每個交易日 14:30（GitHub Actions 免費版常延遲到 ~18:30）自動從 FinMind API 抓取數據，
量化評分＋洞察分析後由 Gemini 生成盤勢解讀，寄送 HTML 報告到 Email，
同步發佈到 GitHub Pages（https://weiweeeeei.github.io/stock/）。

## 檔案結構
```
stock/
├── analyzer.py          # 主程式，串接所有模組
├── fetcher.py           # FinMind API 抓取（137檔個股價格+三大法人）
├── database.py          # SQLite 歷史數據存取與趨勢計算
├── technicals.py        # 技術指標計算（MA/KD/MACD/布林）
├── signals.py           # 燈號引擎（四維度→🟢🟡🔴；無類股指數時從個股反推產業）
├── insights.py          # 洞察引擎（輪動/資金集中/量價背離/鏈動/主題聚合）
├── reporter.py          # HTML 報告生成（四Tab互動頁面＋今日焦點區塊）
├── data/
│   └── stock_universe.py  # 台股分類資料庫（30產業/137檔/8主題）
├── .github/workflows/
│   └── daily.yml        # GitHub Actions 排程＋Pages 部署
├── requirements.txt     # google-genai>=1.0.0, requests>=2.31.0
└── .gitignore           # 排除 db/ reports/ public/
```

---

## 核心架構流程

```
analyzer.py main()
  1. init_db()                          # 建立 SQLite 資料表
  2. fetch_all_market_data()            # fetcher.py → FinMind（137檔並行）
  3. save_market_data()                 # database.py → 存入 db/twstock.db
  4. score_market()                     # signals.py → 市場燈號
  5. score_stock() × 137檔             # signals.py → 個股燈號
  6. score_sectors_from_stocks()        # signals.py → 30個產業燈號（從個股聚合）
  7. compute_insights()                 # insights.py → 輪動/集中度/背離/鏈動/主題
  8. save_sector_scores()               # database.py → 族群分數入庫（供隔日輪動比較）
  9. get_claude_summary()               # Gemini 2.5 Flash 盤勢解讀
 10. generate_report()                  # reporter.py → HTML（含今日焦點）
 11. 寫入 public/index.html             # GitHub Pages 部署
 12. send_email()                       # Gmail SMTP SSL（頂部帶網頁版連結）
```

---

## 環境變數（GitHub Secrets）

```
GEMINI_API_KEY      Google Gemini API Key（aistudio.google.com/apikey，免費）
FINMIND_TOKEN       FinMind API Token（finmindtrade.com，免費 600次/小時）
GMAIL_USER          寄件 Gmail
GMAIL_APP_PWD       Gmail 應用程式密碼（16碼）
RECIPIENT_EMAIL     收件信箱
SEND_EMAIL          true/false（手動觸發時用）
```

---

## 數據來源

| API | 用途 | 端點 |
|-----|------|------|
| TWSE | 加權指數 | `www.twse.com.tw/exchangeReport/MI_INDEX` |
| TWSE | 全部上市收盤 | `www.twse.com.tw/exchangeReport/STOCK_DAY_ALL` |
| TWSE | 三大法人明細 | `www.twse.com.tw/fund/T86` |
| TWSE | 外資Top20 | `www.twse.com.tw/fund/MI_QFIIS_sort_20` |
| TWSE | 投信Top20 | `www.twse.com.tw/fund/MI_SITC_sort_20` |
| TWSE | 類股指數 | `www.twse.com.tw/exchangeReport/MI_INDEX?type=IND` |
| TWSE | 融資融券 | `www.twse.com.tw/exchangeReport/MI_MARGN` |
| TPEx | 上櫃收盤 | `www.tpex.org.tw/web/stock/aftertrading/otc_quotes_no1430/` |
| TPEx | 上櫃法人 | `www.tpex.org.tw/web/stock/3insti/daily_trade/` |
| TPEx | 上櫃類股 | `www.tpex.org.tw/web/stock/iNdex_info/inx/` |

---

## SQLite 資料表

```sql
daily_price         (date, code, name, close, change, change_pct, volume, open, high, low)
daily_institutional (date, code, name, foreign_net, trust_net, dealer_net, total_net)
daily_sector        (date, sector, market, close, change_pct)
daily_market        (date, taiex_close, taiex_change_pct, foreign_net_b, trust_net_b, dealer_net_b, margin_balance, short_balance)
monthly_revenue     (year_month, code, name, revenue, yoy_pct, mom_pct)
```

SQLite 透過 `actions/cache` 在每次 Actions 執行之間保存（key: `twstock-db-{OS}-{run_id}`），技術指標隨時間累積。

---

## 燈號評分系統

```python
# signals.py: score_stock(code, today_data) → dict
# 四維度加權：
技術面 30分  calc_technicals()  → MA排列/KD/MACD/量比
法人面 30分  get_institutional_trend()  → 今日+連續N日買賣超
趨勢面 20分  10日累積外資方向
大盤面 20分  get_market_trend()  → 市場偏多/震盪/偏空

# 燈號閾值：
🟢 >= 70  強力做多
🟡 40-69  觀察等待
🔴 < 40   暫時迴避

# score_sectors(sector_data, inst_data) → list[dict]
# 依 STOCK_UNIVERSE 把法人買賣超對應到各產業
```

---

## 產業分類結構

```python
# data/stock_universe.py
STOCK_UNIVERSE = {
    "IC設計":    {"mega":"科技", "group":"半導體", "theme":[...], "stocks":{...}},
    "晶圓代工":  {"mega":"科技", "group":"半導體", ...},
    "記憶體":    {"mega":"科技", "group":"半導體", ...},
    "封測":      {"mega":"科技", "group":"半導體", ...},
    "半導體設備材料": {...},
    "被動元件":  {...},
    "AI伺服器組裝": {"mega":"科技", "group":"AI雲端", ...},
    "AI加速卡/主機板": {...},
    "散熱":      {...},
    "光通訊":    {...},
    "PCB電路板": {...},
    "車用半導體": {"mega":"科技", "group":"電動車", ...},
    "EV零組件":  {...},
    "整車/充電": {"mega":"傳產", "group":"電動車", ...},
    "鋼鐵":      {"mega":"傳產", "group":"原物料", ...},
    "石化":      {...},
    "水泥建材":  {...},
    "航運貨櫃":  {"mega":"傳產", "group":"航運", ...},
    "航運散裝/航空": {...},
    "機械工具機": {...},
    "食品消費":  {"mega":"傳產", "group":"消費", ...},
    "紡織成衣":  {...},
    "公股銀行":  {"mega":"金融", "group":"金融", ...},
    "民營金控":  {...},
    "保險證券":  {...},
    "生技新藥":  {"mega":"生技", ...},
    "醫療器材":  {...},
    "太陽能":    {"mega":"其他", "group":"綠能", ...},
    "儲能/電池": {...},
    "不動產":    {...},
}
# 每個 stock: {"name":..., "chain":"上游/中游/下游", "sub":"次產業", "note":"..."}
# 總計：30個產業，137檔個股

THEMES = {
    "AI完整供應鏈": [...],
    "半導體完整鏈": [...],
    "電動車供應鏈": [...],
    ...共8個主題
}
```

---

## 報告結構（reporter.py）

```
HTML 四Tab 互動頁面：
  Tab1 今日總覽   大盤儀表板 + 強勢TOP5卡片 + 轉弱TOP5卡片 + AI建議
  Tab2 全族群排行  30個產業排行，點擊展開→看族群內每檔個股燈號
  Tab3 個股訊號   🟢強力做多清單 + 🟡觀察等待前8名
  Tab4 詳細報告   AI深度分析 + 強弱族群完整條列

設計語言：深色系(#0a0b12背景)，燈號用emoji，極簡
```

---

## GitHub Actions 關鍵設定

```yaml
# .github/workflows/daily.yml
on:
  schedule:
    - cron: '30 6 * * 1-5'   # UTC 06:30 = 台灣 14:30，週一到週五
  workflow_dispatch:           # 允許手動觸發

# SQLite cache（讓技術指標歷史累積）
- uses: actions/cache@v4
  with:
    path: db/twstock.db
    key: twstock-db-${{ runner.os }}-${{ github.run_id }}
    restore-keys: twstock-db-

# 報告保存 90 天
- uses: actions/upload-artifact@v4
  with:
    name: 台股日報-${{ github.run_id }}
    path: reports/
    retention-days: 90
```

---

## 已知限制與待改進

1. **技術指標冷啟動**：MA20需20個交易日，MA60需60個交易日，前期顯示「數據不足」
2. **個股數量**：目前137檔精選，可擴充至更多（`stock_universe.py` 新增即可）
3. **月營收功能**：`database.py` 已有 `monthly_revenue` 資料表，但尚未實作抓取與分析
4. **農曆假日**：cron 無法自動判斷台股假日，休市日 TWSE 回傳空數據，系統會正常跑但數據為空
5. **Email 大小**：30個產業×若干個股，報告約 400KB，Gmail 正常，若擴充個股需注意

---

## 常用指令

```bash
# 本機測試（需設環境變數）
export ANTHROPIC_API_KEY=sk-ant-...
export GMAIL_USER=xxx@gmail.com
export GMAIL_APP_PWD=xxxx-xxxx-xxxx-xxxx
export RECIPIENT_EMAIL=xxx@gmail.com
python analyzer.py

# 只測試數據抓取
python fetcher.py

# 只測試產業資料庫
python data/stock_universe.py

# 查看 SQLite 內容
sqlite3 db/twstock.db "SELECT date, taiex_close FROM daily_market ORDER BY date DESC LIMIT 5;"
```
