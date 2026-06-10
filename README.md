# 📈 台股強勢產業日報

每個交易日 **14:30 自動執行**，從 TWSE + TPEx 官方 API 抓取真實數據，
透過 Claude AI 分析強弱產業與個股，寄送精美 HTML 報告到你的 Email。

---

## 部署步驟（5分鐘完成）

### Step 1｜Fork 這個 Repo

點右上角 **Fork** 按鈕，複製到你自己的 GitHub 帳號。

---

### Step 2｜設定 Secrets

到你的 repo → **Settings → Secrets and variables → Actions → New repository secret**

| Secret 名稱 | 填什麼 | 哪裡取得 |
|------------|--------|---------|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| `GMAIL_USER` | `yourname@gmail.com` | 你的 Gmail 帳號 |
| `GMAIL_APP_PWD` | `xxxx xxxx xxxx xxxx` | 見下方說明 |
| `RECIPIENT_EMAIL` | `yourname@gmail.com` | 收報告的信箱（可跟上面一樣）|

#### 如何取得 Gmail App Password

1. 到 [myaccount.google.com/security](https://myaccount.google.com/security)
2. 確認已開啟「兩步驟驗證」
3. 搜尋「應用程式密碼」→ 選「郵件」→ 點「產生」
4. 複製 16 碼密碼填入 `GMAIL_APP_PWD`

---

### Step 3｜啟用 Actions

到你的 repo → **Actions** 頁面 → 點「I understand my workflows, go ahead and enable them」

---

### Step 4｜測試執行

**Actions → 台股強勢產業日報 → Run workflow → Run workflow**

約 2 分鐘後收到第一封報告，確認正常後就完成了。

之後每個交易日 14:30 自動執行，完全不需要你做任何事。

---

## 報告內容

| Tab | 內容 |
|-----|------|
| 📊 今日總覽 | 大盤燈號、強勢 TOP5、轉弱 TOP5、AI 操作建議 |
| 🏭 全族群排行 | 30 個細分族群強弱排行，**點擊展開**看族群內每一檔個股 |
| 📈 個股訊號 | 所有 🟢強力做多 個股清單，含外資連買天數 |
| 📋 詳細報告 | AI 深度分析，強弱族群完整條列 |

---

## 評分系統

```
技術面  30分   均線排列 / KD / MACD / 量能比
法人面  30分   今日三大法人 + 連續N日買賣超
趨勢面  20分   10日累積法人方向
大盤面  20分   市場整體環境（外資5日、上漲天數）
─────────────────────────────────
滿分   100分

🟢 70分以上 → 強力做多
🟡 40-69分  → 觀察等待
🔴 40分以下 → 暫時迴避
```

> 技術指標需累積歷史數據：MA20 需 20 個交易日，MA60 需 60 個交易日。
> SQLite 透過 GitHub Actions Cache 自動保存，每天累積不中斷。

---

## 費用

| 服務 | 費用 |
|------|------|
| GitHub Actions | ✅ 免費（每月 2000 分鐘，每次約 2 分鐘）|
| TWSE / TPEx API | ✅ 完全免費，官方數據 |
| Gmail | ✅ 免費 |
| Claude API | 約 NT$3-5 / 次（Sonnet，每月約 NT$65-110）|

---

## 常見問題

**Q: 為什麼技術指標第一週都顯示「數據不足」？**
A: 正常的，技術指標需要歷史數據累積。約累積 20 個交易日後 MA20 才準確，60 個交易日後 MA60 才啟用。

**Q: 非交易日（假日）會執行嗎？**
A: cron 只設週一到週五，但農曆假日台股休市時 TWSE API 會回傳空數據，系統會偵測並跳過。

**Q: 可以改成其他時間執行嗎？**
A: 修改 `daily.yml` 的 cron 設定。建議不要早於 14:00，因為三大法人數據約 14:00-14:30 才揭露完整。

**Q: 報告存在哪裡？**
A: 每次執行後自動上傳到 GitHub Actions Artifacts，保存 90 天可下載。同時寄送到你的 Email。

---

## 資料來源

- 台灣證券交易所 TWSE OpenAPI
- 財團法人中華民國證券櫃檯買賣中心 TPEx API
- AI 分析：Anthropic Claude

⚠️ 本系統生成之報告僅供參考，不構成任何投資建議。投資有風險，請獨立判斷。
