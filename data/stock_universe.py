"""
台股產業分類資料庫 v2
分類架構：
  mega     : 科技 / 傳產 / 金融 / 生技 / 其他
  sector   : 細分產業（42個）
  chain    : 上游 / 中游 / 下游
  sub      : 次產業（更細）
"""

STOCK_UNIVERSE = {

    # ════════════════════════════════════════
    # 🔵 半導體供應鏈（拆成6個細分）
    # ════════════════════════════════════════

    "IC設計": {
        "mega": "科技", "group": "半導體",
        "theme": ["AI", "半導體", "IC設計"],
        "stocks": {
            "2454": {"name": "聯發科",   "chain": "上游", "sub": "手機/AIoT SoC", "note": "天璣系列，AI PC布局"},
            "3034": {"name": "聯詠",     "chain": "上游", "sub": "顯示驅動IC",    "note": "面板驅動IC龍頭"},
            "2379": {"name": "瑞昱",     "chain": "上游", "sub": "網通/音效IC",   "note": "乙太網路控制器"},
            "2388": {"name": "威盛",     "chain": "上游", "sub": "晶片組",        "note": "USB/儲存控制"},
            "6533": {"name": "晶心科",   "chain": "上游", "sub": "RISC-V IP",    "note": "處理器IP授權"},
            "3443": {"name": "創意",     "chain": "上游", "sub": "特殊IC設計",    "note": "台積電生態系ASIC"},
            "5347": {"name": "世界",     "chain": "上游", "sub": "功率IC",        "note": "車用功率半導體"},
            "6533": {"name": "晶心科",   "chain": "上游", "sub": "IP核",         "note": "RISC-V架構"},
            "4966": {"name": "譜瑞-KY",  "chain": "上游", "sub": "訊號IC",       "note": "高速訊號傳輸IC"},
            "6271": {"name": "同欣電",   "chain": "上游", "sub": "感測IC",       "note": "CMOS感測"},
            "3661": {"name": "世芯-KY",  "chain": "上游", "sub": "AI ASIC",     "note": "雲端AI晶片設計服務"},
            "3035": {"name": "智原",     "chain": "上游", "sub": "ASIC",        "note": "聯電系ASIC設計"},
            "5269": {"name": "祥碩",     "chain": "上游", "sub": "高速介面IC",   "note": "USB4/PCIe，華碩子公司"},
            "5274": {"name": "信驊",     "chain": "上游", "sub": "BMC",         "note": "伺服器遠端管理晶片龍頭"},
            "3529": {"name": "力旺",     "chain": "上游", "sub": "記憶體IP",     "note": "eNVM矽智財"},
            "2458": {"name": "義隆",     "chain": "上游", "sub": "觸控IC",       "note": "筆電觸控板"},
            "3227": {"name": "原相",     "chain": "上游", "sub": "感測IC",       "note": "滑鼠/遊戲機感測"},
            "6202": {"name": "盛群",     "chain": "上游", "sub": "MCU",         "note": "消費性MCU"},
        }
    },

    "晶圓代工": {
        "mega": "科技", "group": "半導體",
        "theme": ["AI", "半導體", "晶圓代工"],
        "stocks": {
            "2330": {"name": "台積電",   "chain": "中游", "sub": "先進製程",     "note": "3nm/2nm，CoWoS先進封裝"},
            "2303": {"name": "聯電",     "chain": "中游", "sub": "成熟製程",     "note": "22/28nm，特殊製程"},
            "5347": {"name": "世界",     "chain": "中游", "sub": "功率製程",     "note": "BCD/GaN功率製程"},
            "2344": {"name": "華邦電",   "chain": "中游", "sub": "嵌入式記憶體", "note": "邏輯+記憶體整合"},
            "6770": {"name": "力積電",   "chain": "中游", "sub": "成熟製程",     "note": "DRAM+邏輯代工"},
        }
    },

    "記憶體": {
        "mega": "科技", "group": "半導體",
        "theme": ["AI", "半導體", "記憶體"],
        "stocks": {
            "2408": {"name": "南亞科",   "chain": "中游", "sub": "DRAM",        "note": "DDR5，HBM布局"},
            "2337": {"name": "旺宏",     "chain": "中游", "sub": "NOR Flash",   "note": "車用/工業Flash"},
            "4919": {"name": "新唐",     "chain": "上游", "sub": "MCU+Flash",   "note": "微控制器+記憶體"},
            "3702": {"name": "大聯大",   "chain": "下游", "sub": "半導體代理",   "note": "亞太最大半導體通路"},
            "3005": {"name": "神基",     "chain": "下游", "sub": "工業電腦",     "note": "邊緣運算"},
            "8299": {"name": "群聯",     "chain": "上游", "sub": "NAND控制IC",  "note": "快閃記憶體控制+模組"},
            "3260": {"name": "威剛",     "chain": "下游", "sub": "記憶體模組",   "note": "DRAM/SSD模組"},
            "4967": {"name": "十銓",     "chain": "下游", "sub": "記憶體模組",   "note": "電競記憶體"},
        }
    },

    "封測": {
        "mega": "科技", "group": "半導體",
        "theme": ["AI", "半導體", "封測"],
        "stocks": {
            "3711": {"name": "日月光投控","chain": "下游", "sub": "先進封裝",    "note": "SiP/Fan-out，CoW"},
            "2325": {"name": "矽品",     "chain": "下游", "sub": "傳統封測",     "note": "日月光子公司"},
            "6271": {"name": "同欣電",   "chain": "下游", "sub": "感測封裝",     "note": "CMOS影像感測封裝"},
            "2330": {"name": "台積電",   "chain": "下游", "sub": "CoWoS封裝",   "note": "先進封裝整合"},
            "8150": {"name": "南茂",     "chain": "下游", "sub": "記憶體封裝",   "note": "DRAM/Flash封裝"},
            "6239": {"name": "力成",     "chain": "下游", "sub": "記憶體封測",   "note": "DRAM封測龍頭"},
            "2449": {"name": "京元電子", "chain": "下游", "sub": "晶圓測試",     "note": "AI晶片測試大廠"},
            "6147": {"name": "頎邦",     "chain": "下游", "sub": "驅動IC封測",   "note": "COF封裝"},
            "3264": {"name": "欣銓",     "chain": "下游", "sub": "晶圓測試",     "note": "車用/邏輯測試"},
        }
    },

    "半導體設備材料": {
        "mega": "科技", "group": "半導體",
        "theme": ["半導體", "設備"],
        "stocks": {
            "3189": {"name": "景碩",     "chain": "上游", "sub": "IC載板",      "note": "ABF/BT基板"},
            "3037": {"name": "欣興",     "chain": "上游", "sub": "ABF載板",     "note": "AI晶片主要載板"},
            "8046": {"name": "南電",     "chain": "上游", "sub": "ABF/BT載板",  "note": "高階載板"},
            "6274": {"name": "台燿",     "chain": "上游", "sub": "高頻基材",     "note": "高頻PCB基材"},
            "3680": {"name": "家登",     "chain": "上游", "sub": "EUV光罩盒",   "note": "EUV pod獨家供應"},
            "1560": {"name": "中砂",     "chain": "上游", "sub": "鑽石碟",       "note": "CMP研磨耗材"},
            "5434": {"name": "崇越",     "chain": "上游", "sub": "材料通路",     "note": "信越光阻劑代理"},
            "2404": {"name": "漢唐",     "chain": "中游", "sub": "無塵室工程",   "note": "晶圓廠統包工程"},
            "6196": {"name": "帆宣",     "chain": "中游", "sub": "廠務系統",     "note": "半導體廠務工程"},
            "3413": {"name": "京鼎",     "chain": "上游", "sub": "製程設備",     "note": "應用材料供應商"},
            "3583": {"name": "辛耘",     "chain": "上游", "sub": "再生晶圓",     "note": "設備代理+再生晶圓"},
        }
    },

    "被動元件": {
        "mega": "科技", "group": "半導體",
        "theme": ["半導體", "電子零組件"],
        "stocks": {
            "2327": {"name": "國巨",     "chain": "上游", "sub": "MLCC/電阻",   "note": "全球前三大被動元件"},
            "2492": {"name": "華新科",   "chain": "上游", "sub": "MLCC",        "note": "車用MLCC"},
            "2308": {"name": "台達電",   "chain": "上游", "sub": "電源模組",     "note": "電源+被動元件"},
            "2312": {"name": "金寶",     "chain": "中游", "sub": "EMS",         "note": "電子代工"},
            "2351": {"name": "順德",     "chain": "上游", "sub": "電感",        "note": "繞線電感"},
            "3026": {"name": "禾伸堂",   "chain": "上游", "sub": "MLCC",        "note": "高壓MLCC利基型"},
        }
    },

    # ════════════════════════════════════════
    # 🟦 AI / 雲端 / 伺服器
    # ════════════════════════════════════════

    "AI伺服器組裝": {
        "mega": "科技", "group": "AI雲端",
        "theme": ["AI", "伺服器"],
        "stocks": {
            "2317": {"name": "鴻海",     "chain": "下游", "sub": "EMS整機",     "note": "GB200 NVL72組裝"},
            "2382": {"name": "廣達",     "chain": "下游", "sub": "ODM伺服器",   "note": "雲端AI伺服器龍頭"},
            "2356": {"name": "英業達",   "chain": "下游", "sub": "ODM伺服器",   "note": "伺服器+儲存"},
            "3231": {"name": "緯創",     "chain": "下游", "sub": "ODM",         "note": "AI伺服器/邊緣運算"},
            "2353": {"name": "宏碁",     "chain": "下游", "sub": "品牌PC",      "note": "AI PC轉型"},
            "2357": {"name": "華碩",     "chain": "下游", "sub": "品牌+主機板",  "note": "RTX GPU主機板"},
            "6669": {"name": "緯穎",     "chain": "下游", "sub": "雲端伺服器",   "note": "Meta/微軟白牌伺服器"},
            "2301": {"name": "光寶科",   "chain": "中游", "sub": "電源供應器",   "note": "AI伺服器電源"},
            "2324": {"name": "仁寶",     "chain": "下游", "sub": "ODM",         "note": "筆電+伺服器代工"},
            "2354": {"name": "鴻準",     "chain": "中游", "sub": "機構件",       "note": "散熱+機殼"},
            "8210": {"name": "勤誠",     "chain": "中游", "sub": "伺服器機殼",   "note": "AI伺服器機箱"},
            "2059": {"name": "川湖",     "chain": "中游", "sub": "伺服器滑軌",   "note": "導軌寡占，毛利率逾60%"},
        }
    },

    "AI加速卡/主機板": {
        "mega": "科技", "group": "AI雲端",
        "theme": ["AI", "GPU"],
        "stocks": {
            "2377": {"name": "微星",     "chain": "中游", "sub": "GPU主機板",   "note": "NVIDIA合作夥伴"},
            "2376": {"name": "技嘉",     "chain": "中游", "sub": "GPU主機板",   "note": "HGX/MGX平台"},
            "3706": {"name": "神達",     "chain": "中游", "sub": "伺服器主機板", "note": "邊緣AI伺服器"},
            "6415": {"name": "矽力-KY",  "chain": "上游", "sub": "電源管理IC",  "note": "GPU電源IC龍頭"},
            "3045": {"name": "台灣大",   "chain": "下游", "sub": "電信",        "note": "AI雲端+邊緣運算"},
            "3515": {"name": "華擎",     "chain": "中游", "sub": "伺服器板卡",   "note": "AI工作站主機板"},
        }
    },

    "散熱": {
        "mega": "科技", "group": "AI雲端",
        "theme": ["AI", "散熱"],
        "stocks": {
            "3017": {"name": "奇鋐",     "chain": "中游", "sub": "氣冷/水冷",   "note": "AI散熱龍頭，液冷佔比提升"},
            "3324": {"name": "雙鴻",     "chain": "中游", "sub": "液冷散熱",    "note": "CDU液冷模組"},
            "6409": {"name": "旭隼",     "chain": "中游", "sub": "液冷",        "note": "冷板式液冷"},
            "2350": {"name": "環電",     "chain": "中游", "sub": "電源供應器",  "note": "伺服器PSU"},
            "1563": {"name": "巧新",     "chain": "中游", "sub": "鋁擠散熱",    "note": "高功率散熱片"},
            "2421": {"name": "建準",     "chain": "中游", "sub": "散熱風扇",    "note": "伺服器風扇馬達"},
            "3338": {"name": "泰碩",     "chain": "中游", "sub": "熱管",        "note": "熱管/均熱片"},
            "3483": {"name": "力致",     "chain": "中游", "sub": "散熱模組",    "note": "筆電+伺服器散熱"},
            "6230": {"name": "超眾",     "chain": "中游", "sub": "散熱模組",    "note": "熱管+均溫板"},
            "8996": {"name": "高力",     "chain": "中游", "sub": "液冷熱交換",  "note": "AI液冷板式熱交換器"},
        }
    },

    "光通訊": {
        "mega": "科技", "group": "AI雲端",
        "theme": ["AI", "光通訊"],
        "stocks": {
            "3491": {"name": "昇達科",   "chain": "中游", "sub": "光收發器",    "note": "800G/1.6T光模組"},
            "4977": {"name": "眾達-KY",  "chain": "中游", "sub": "高速光模組",  "note": "CPO共封裝光學"},
            "3466": {"name": "聯鈞",     "chain": "上游", "sub": "雷射晶片",    "note": "VCSEL/EML雷射"},
            "3047": {"name": "訊舟",     "chain": "下游", "sub": "網通設備",    "note": "工業以太網路"},
            "2345": {"name": "智邦",     "chain": "下游", "sub": "資料中心交換器","note": "400G/800G交換器"},
            "3363": {"name": "上詮",     "chain": "中游", "sub": "光纖元件",    "note": "CPO光連接"},
            "3163": {"name": "波若威",   "chain": "中游", "sub": "光被動元件",  "note": "光分波器"},
            "3081": {"name": "聯亞",     "chain": "上游", "sub": "磊晶",        "note": "雷射二極體磊晶"},
            "4979": {"name": "華星光",   "chain": "中游", "sub": "光收發模組",  "note": "資料中心光模組"},
            "6451": {"name": "訊芯-KY",  "chain": "中游", "sub": "光模組SiP",   "note": "鴻海系光模組封裝"},
        }
    },

    "PCB電路板": {
        "mega": "科技", "group": "AI雲端",
        "theme": ["AI", "PCB"],
        "stocks": {
            "3037": {"name": "欣興",     "chain": "中游", "sub": "ABF載板",     "note": "AI晶片主載板"},
            "8046": {"name": "南電",     "chain": "中游", "sub": "IC載板",      "note": "BT+ABF"},
            "2367": {"name": "燿華",     "chain": "中游", "sub": "高頻PCB",     "note": "毫米波天線板"},
            "6269": {"name": "台郡",     "chain": "中游", "sub": "軟板FPC",     "note": "iPhone/AI穿戴"},
            "3376": {"name": "新日興",   "chain": "中游", "sub": "鉸鏈",        "note": "AI PC鉸鏈"},
            "6213": {"name": "聯茂",     "chain": "中游", "sub": "高頻基材",    "note": "車用+5G基材"},
            "2383": {"name": "台光電",   "chain": "上游", "sub": "CCL銅箔基板", "note": "AI伺服器CCL龍頭"},
            "2368": {"name": "金像電",   "chain": "中游", "sub": "伺服器PCB",   "note": "GPU加速卡板"},
            "3044": {"name": "健鼎",     "chain": "中游", "sub": "多層板",      "note": "伺服器+車用PCB"},
            "2313": {"name": "華通",     "chain": "中游", "sub": "HDI",         "note": "衛星+手機板"},
            "4958": {"name": "臻鼎-KY",  "chain": "中游", "sub": "軟硬板",      "note": "全球PCB產值第一"},
        }
    },

    # ════════════════════════════════════════
    # 🟩 電動車 / 車用
    # ════════════════════════════════════════

    "車用半導體": {
        "mega": "科技", "group": "電動車",
        "theme": ["電動車", "半導體"],
        "stocks": {
            "5347": {"name": "世界",     "chain": "上游", "sub": "SiC功率元件",  "note": "碳化矽MOSFET"},
            "2454": {"name": "聯發科",   "chain": "上游", "sub": "車用SoC",     "note": "Dimensity Auto"},
            "6770": {"name": "力智",     "chain": "上游", "sub": "車用電源IC",   "note": "GaN驅動IC"},
            "3105": {"name": "穩懋",     "chain": "上游", "sub": "GaAs/GaN",   "note": "PA+車用功率"},
            "4966": {"name": "譜瑞-KY",  "chain": "上游", "sub": "車用訊號IC",  "note": "車用DisplayPort"},
            "8261": {"name": "富鼎",     "chain": "上游", "sub": "MOSFET",      "note": "功率元件"},
            "2481": {"name": "強茂",     "chain": "上游", "sub": "二極體",      "note": "車用整流二極體"},
        }
    },

    "EV零組件": {
        "mega": "科技", "group": "電動車",
        "theme": ["電動車", "零組件"],
        "stocks": {
            "3665": {"name": "貿聯-KY",  "chain": "中游", "sub": "充電線束",    "note": "Tesla主要供應商"},
            "2308": {"name": "台達電",   "chain": "中游", "sub": "車載電源",    "note": "OBC車載充電器"},
            "1590": {"name": "亞德客-KY","chain": "上游", "sub": "氣動元件",    "note": "車用+工控氣動"},
            "2049": {"name": "上銀",     "chain": "上游", "sub": "線性傳動",    "note": "滾珠螺桿+機器人"},
            "1597": {"name": "直得",     "chain": "上游", "sub": "線性滑軌",    "note": "精密傳動"},
            "6153": {"name": "嘉聯益",   "chain": "中游", "sub": "車用軟板",    "note": "車用FPC"},
            "1536": {"name": "和大",     "chain": "中游", "sub": "減速齒輪",    "note": "Tesla傳動系統"},
            "2228": {"name": "劍麟",     "chain": "中游", "sub": "安全零件",    "note": "安全帶/氣囊組件"},
            "6279": {"name": "胡連",     "chain": "中游", "sub": "連接器",      "note": "車用端子連接器"},
            "2231": {"name": "為升",     "chain": "中游", "sub": "感測器",      "note": "胎壓偵測TPMS"},
            "1504": {"name": "東元",     "chain": "中游", "sub": "馬達",        "note": "工業+EV馬達"},
        }
    },

    "整車/充電": {
        "mega": "傳產", "group": "電動車",
        "theme": ["電動車"],
        "stocks": {
            "2207": {"name": "和泰車",   "chain": "下游", "sub": "Toyota代理",  "note": "油電混合+bZ系列"},
            "2201": {"name": "裕隆",     "chain": "下游", "sub": "Luxgen品牌",  "note": "n⁷/n⁸電動車"},
            "2204": {"name": "中華車",   "chain": "下游", "sub": "電動巴士",    "note": "三菱+電動商用車"},
            "1513": {"name": "中興電",   "chain": "中游", "sub": "充電樁",      "note": "公共充電基礎設施"},
            "2206": {"name": "三陽工業", "chain": "下游", "sub": "機車",        "note": "機車龍頭+電動機車"},
            "1519": {"name": "華城",     "chain": "中游", "sub": "變壓器",      "note": "重電+充電樁，資料中心電力"},
            "1503": {"name": "士電",     "chain": "中游", "sub": "重電",        "note": "變壓器+配電盤"},
        }
    },

    # ════════════════════════════════════════
    # 🟡 傳統產業
    # ════════════════════════════════════════

    "鋼鐵": {
        "mega": "傳產", "group": "原物料",
        "theme": ["原物料", "鋼鐵"],
        "stocks": {
            "2002": {"name": "中鋼",     "chain": "中游", "sub": "高爐鋼",      "note": "台灣鋼鐵龍頭"},
            "2015": {"name": "豐興",     "chain": "中游", "sub": "電弧爐長材",   "note": "螺紋鋼/型鋼"},
            "2003": {"name": "榮鋼",     "chain": "中游", "sub": "不鏽鋼",      "note": "304/316不鏽鋼"},
            "2014": {"name": "中鴻",     "chain": "下游", "sub": "冷軋鋼板",    "note": "中鋼子公司"},
            "2023": {"name": "燁輝",     "chain": "下游", "sub": "鍍鋅鋼板",    "note": "彩塗鋼板"},
            "2006": {"name": "東和鋼鐵", "chain": "中游", "sub": "電爐鋼",      "note": "鋼筋+型鋼"},
            "2027": {"name": "大成鋼",   "chain": "下游", "sub": "不鏽鋼通路",  "note": "美國鋁捲通路"},
            "9958": {"name": "世紀鋼",   "chain": "下游", "sub": "風電鋼構",    "note": "離岸風電水下基礎"},
        }
    },

    "石化": {
        "mega": "傳產", "group": "原物料",
        "theme": ["原物料", "石化"],
        "stocks": {
            "6505": {"name": "台塑化",   "chain": "上游", "sub": "煉油",        "note": "六輕煉油"},
            "1301": {"name": "台塑",     "chain": "上游", "sub": "PVC原料",     "note": "台塑四寶"},
            "1303": {"name": "南亞",     "chain": "中游", "sub": "塑膠加工",    "note": "台塑四寶"},
            "1326": {"name": "台化",     "chain": "中游", "sub": "ABS/化纖",   "note": "台塑四寶"},
            "1305": {"name": "華夏",     "chain": "中游", "sub": "PTA",        "note": "聚酯原料"},
            "1314": {"name": "中石化",   "chain": "中游", "sub": "CPL",        "note": "尼龍原料"},
            "1717": {"name": "長興",     "chain": "中游", "sub": "特用化學",    "note": "半導體材料+樹脂"},
        }
    },

    "航運貨櫃": {
        "mega": "傳產", "group": "航運",
        "theme": ["航運"],
        "stocks": {
            "2603": {"name": "長榮",     "chain": "中游", "sub": "貨櫃海運",    "note": "全球前10，跨太平洋線"},
            "2609": {"name": "陽明",     "chain": "中游", "sub": "貨櫃海運",    "note": "亞歐線為主"},
            "2615": {"name": "萬海",     "chain": "中游", "sub": "區域貨櫃",    "note": "亞洲區域線強"},
            "2636": {"name": "台驊投控", "chain": "下游", "sub": "貨代物流",    "note": "海空運承攬"},
            "2608": {"name": "嘉里大榮", "chain": "下游", "sub": "陸運物流",    "note": "島內物流"},
        }
    },

    "航運散裝/航空": {
        "mega": "傳產", "group": "航運",
        "theme": ["航運"],
        "stocks": {
            "2605": {"name": "新興",     "chain": "中游", "sub": "散裝",        "note": "BDI指數連動"},
            "2637": {"name": "慧洋-KY",  "chain": "中游", "sub": "散裝",        "note": "Handysize船隊"},
            "2610": {"name": "華航",     "chain": "中游", "sub": "航空貨運",    "note": "貨運+客運"},
            "2618": {"name": "長榮航",   "chain": "中游", "sub": "航空客運",    "note": "客運復甦"},
            "2606": {"name": "裕民",     "chain": "中游", "sub": "散裝",        "note": "海岬型船隊"},
            "2634": {"name": "漢翔",     "chain": "中游", "sub": "航太製造",    "note": "軍機+民航機結構件"},
        }
    },

    "機械工具機": {
        "mega": "傳產", "group": "機械",
        "theme": ["機械", "工業自動化"],
        "stocks": {
            "2049": {"name": "上銀",     "chain": "上游", "sub": "滾珠螺桿",    "note": "精密傳動+機器人"},
            "1590": {"name": "亞德客-KY","chain": "上游", "sub": "氣動元件",    "note": "工控氣動龍頭"},
            "4526": {"name": "東台",     "chain": "中游", "sub": "CNC工具機",   "note": "複合加工機"},
            "1597": {"name": "直得",     "chain": "上游", "sub": "線性滑軌",    "note": "精密線性導引"},
            "1583": {"name": "程泰",     "chain": "中游", "sub": "工具機",      "note": "車床+複合機"},
            "4555": {"name": "氣立",     "chain": "上游", "sub": "氣動元件",    "note": "電動缸自動化"},
            "1530": {"name": "亞崴",     "chain": "中游", "sub": "工具機",      "note": "龍門加工機"},
        }
    },

    "食品消費": {
        "mega": "傳產", "group": "消費",
        "theme": ["食品", "民生消費"],
        "stocks": {
            "1216": {"name": "統一",     "chain": "下游", "sub": "食品飲料",    "note": "統一集團旗艦"},
            "2912": {"name": "統一超",   "chain": "下游", "sub": "超商",        "note": "7-11，鮮食佔比高"},
            "5903": {"name": "全家",     "chain": "下游", "sub": "超商",        "note": "FamilyMart"},
            "1229": {"name": "聯華",     "chain": "上游", "sub": "麵粉",        "note": "民生必需"},
            "1210": {"name": "大成",     "chain": "上游", "sub": "飼料肉品",    "note": "農畜垂直整合"},
            "1215": {"name": "卜蜂",     "chain": "上游", "sub": "飼料肉品",    "note": "雞肉供應鏈"},
            "1227": {"name": "佳格",     "chain": "中游", "sub": "食品",        "note": "燕麥+葵花油"},
        }
    },

    "紡織成衣": {
        "mega": "傳產", "group": "消費",
        "theme": ["紡織", "消費"],
        "stocks": {
            "1402": {"name": "遠東新",   "chain": "中游", "sub": "聚酯纖維",    "note": "rPET回收纖維"},
            "1409": {"name": "新纖",     "chain": "中游", "sub": "尼龍",        "note": "工業用絲"},
            "9904": {"name": "寶成",     "chain": "下游", "sub": "運動鞋代工",  "note": "Nike/Adidas最大代工"},
            "1476": {"name": "儒鴻",     "chain": "中游", "sub": "機能布+成衣", "note": "Nike/lululemon供應商"},
            "1477": {"name": "聚陽",     "chain": "下游", "sub": "成衣",        "note": "快時尚代工"},
        }
    },

    "水泥建材": {
        "mega": "傳產", "group": "原物料",
        "theme": ["建材"],
        "stocks": {
            "1101": {"name": "台泥",     "chain": "上游", "sub": "水泥",        "note": "台灣最大水泥+儲能"},
            "1102": {"name": "亞泥",     "chain": "上游", "sub": "水泥",        "note": "中國市場佔比高"},
            "1103": {"name": "嘉泥",     "chain": "上游", "sub": "水泥",        "note": ""},
            "2504": {"name": "國產",     "chain": "中游", "sub": "預拌混凝土",  "note": "全台最大預拌廠"},
        }
    },

    # ════════════════════════════════════════
    # 🟢 金融
    # ════════════════════════════════════════

    "公股銀行": {
        "mega": "金融", "group": "金融",
        "theme": ["金融", "銀行"],
        "stocks": {
            "2886": {"name": "兆豐金",   "chain": "—", "sub": "銀行+票券",  "note": "外匯業務強"},
            "2892": {"name": "第一金",   "chain": "—", "sub": "銀行",      "note": "公股，股利穩定"},
            "2880": {"name": "華南金",   "chain": "—", "sub": "銀行",      "note": "公股"},
            "2801": {"name": "彰銀",     "chain": "—", "sub": "銀行",      "note": "公股"},
            "5880": {"name": "合庫金",   "chain": "—", "sub": "銀行",      "note": "公股，農業金融"},
            "2834": {"name": "臺企銀",   "chain": "—", "sub": "銀行",      "note": "中小企業放款"},
        }
    },

    "民營金控": {
        "mega": "金融", "group": "金融",
        "theme": ["金融", "銀行", "壽險"],
        "stocks": {
            "2882": {"name": "國泰金",   "chain": "—", "sub": "壽險+銀行",  "note": "資產規模最大"},
            "2891": {"name": "中信金",   "chain": "—", "sub": "銀行+證券",  "note": "消費金融強"},
            "2884": {"name": "玉山金",   "chain": "—", "sub": "銀行",       "note": "數位轉型標竿"},
            "2883": {"name": "開發金",   "chain": "—", "sub": "創投+銀行",  "note": "台灣大哥大母公司"},
            "2887": {"name": "台新金",   "chain": "—", "sub": "銀行",       "note": "Richart數位銀行"},
            "2888": {"name": "新光金",   "chain": "—", "sub": "壽險",       "note": "壽險為主"},
            "2890": {"name": "永豐金",   "chain": "—", "sub": "銀行+證券",  "note": ""},
            "2885": {"name": "元大金",   "chain": "—", "sub": "證券+銀行",  "note": "證券龍頭"},
            "5876": {"name": "上海商銀", "chain": "—", "sub": "銀行",       "note": "高ROE老牌銀行"},
        }
    },

    "保險證券": {
        "mega": "金融", "group": "金融",
        "theme": ["金融", "保險"],
        "stocks": {
            "2823": {"name": "中壽",     "chain": "—", "sub": "壽險",       "note": ""},
            "2881": {"name": "富邦金",   "chain": "—", "sub": "壽險+銀行",  "note": "資產規模第二"},
            "6005": {"name": "群益證",   "chain": "—", "sub": "證券",       "note": ""},
            "2855": {"name": "統一證",   "chain": "—", "sub": "證券",       "note": ""},
            "2867": {"name": "三商壽",   "chain": "—", "sub": "壽險",       "note": ""},
        }
    },

    # ════════════════════════════════════════
    # 🔴 生技醫療
    # ════════════════════════════════════════

    "生技新藥": {
        "mega": "生技", "group": "生技醫療",
        "theme": ["生技"],
        "stocks": {
            "4175": {"name": "聯生藥",   "chain": "上游", "sub": "生物相似藥",  "note": "單株抗體"},
            "4537": {"name": "浩鼎",     "chain": "上游", "sub": "癌症新藥",    "note": "乳癌醣類疫苗"},
            "6547": {"name": "高端疫苗", "chain": "上游", "sub": "疫苗",        "note": "次單位蛋白疫苗"},
            "1789": {"name": "神隆",     "chain": "上游", "sub": "原料藥",      "note": "抗癌原料藥"},
            "6446": {"name": "藥華藥",   "chain": "上游", "sub": "新藥",        "note": "P1101罕病新藥，外銷美國"},
            "4743": {"name": "合一",     "chain": "上游", "sub": "新藥",        "note": "糖尿病足潰瘍新藥"},
            "6472": {"name": "保瑞",     "chain": "中游", "sub": "CDMO",        "note": "藥品代工+學名藥"},
            "1795": {"name": "美時",     "chain": "中游", "sub": "學名藥",      "note": "戒癮/抗癌學名藥"},
            "4162": {"name": "智擎",     "chain": "上游", "sub": "新藥",        "note": "胰臟癌安能得"},
        }
    },

    "醫療器材": {
        "mega": "生技", "group": "生技醫療",
        "theme": ["醫療"],
        "stocks": {
            "4737": {"name": "佳醫",     "chain": "下游", "sub": "洗腎服務",    "note": "透析中心+耗材"},
            "4153": {"name": "鐿鈦",     "chain": "中游", "sub": "骨科耗材",    "note": "手術植入物"},
            "4126": {"name": "太醫",     "chain": "中游", "sub": "輸液耗材",    "note": "靜脈輸液管"},
            "1762": {"name": "中化生",   "chain": "中游", "sub": "試劑",        "note": "診斷試劑"},
            "4107": {"name": "邦特",     "chain": "中游", "sub": "血液透析",    "note": "洗腎耗材"},
            "4736": {"name": "泰博",     "chain": "中游", "sub": "血糖機",      "note": "血糖監測+快篩"},
            "6469": {"name": "大樹",     "chain": "下游", "sub": "藥局通路",    "note": "連鎖藥局龍頭"},
        }
    },

    # ════════════════════════════════════════
    # ⚡ 綠能 / 儲能
    # ════════════════════════════════════════

    "太陽能": {
        "mega": "其他", "group": "綠能",
        "theme": ["綠能", "ESG"],
        "stocks": {
            "3576": {"name": "聯合再生", "chain": "中游", "sub": "太陽能電池",  "note": "PERC/TOPCon"},
            "6244": {"name": "茂迪",     "chain": "中游", "sub": "太陽能電池",  "note": "IBC高效電池"},
            "3004": {"name": "億通",     "chain": "下游", "sub": "太陽能系統",  "note": "EPC系統整合"},
            "6443": {"name": "元晶",     "chain": "中游", "sub": "電池模組",    "note": "TOPCon電池"},
            "6806": {"name": "森崴能源", "chain": "下游", "sub": "綠電工程",    "note": "離岸風電EPC"},
        }
    },

    "儲能/電池": {
        "mega": "其他", "group": "綠能",
        "theme": ["綠能", "儲能"],
        "stocks": {
            "1101": {"name": "台泥",     "chain": "中游", "sub": "儲能系統",    "note": "E-dge儲能品牌"},
            "1513": {"name": "中興電",   "chain": "中游", "sub": "儲能+充電",   "note": "台電儲能合作"},
            "6409": {"name": "旭隼",     "chain": "中游", "sub": "冷卻+儲能",   "note": "儲能熱管理"},
            "6121": {"name": "新普",     "chain": "中游", "sub": "電池模組",    "note": "筆電+伺服器BBU"},
            "6781": {"name": "AES-KY",   "chain": "中游", "sub": "電芯",        "note": "高功率圓柱電芯"},
        }
    },

    "不動產": {
        "mega": "其他", "group": "房地產",
        "theme": ["房地產"],
        "stocks": {
            "5522": {"name": "遠雄",     "chain": "—", "sub": "建設",       "note": "大型社區開發"},
            "2511": {"name": "太子",     "chain": "—", "sub": "建設",       "note": ""},
            "2501": {"name": "國建",     "chain": "—", "sub": "建設",       "note": "工業地產"},
            "2515": {"name": "中工",     "chain": "—", "sub": "工程",       "note": ""},
            "9945": {"name": "潤泰全",   "chain": "—", "sub": "量販+建設",  "note": "大潤發"},
            "2542": {"name": "興富發",   "chain": "—", "sub": "建設",       "note": "推案量大"},
            "2548": {"name": "華固",     "chain": "—", "sub": "建設",       "note": "台北豪宅"},
            "5534": {"name": "長虹",     "chain": "—", "sub": "建設",       "note": "商辦+住宅"},
            "9940": {"name": "信義",     "chain": "—", "sub": "仲介",       "note": "房仲龍頭"},
        }
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# 主題板塊（跨產業）
# ──────────────────────────────────────────────────────────────────────────────

THEMES = {
    "AI完整供應鏈":  ["IC設計","晶圓代工","封測","AI伺服器組裝","AI加速卡/主機板","散熱","光通訊","PCB電路板"],
    "半導體完整鏈":  ["IC設計","晶圓代工","記憶體","封測","半導體設備材料","被動元件"],
    "電動車供應鏈":  ["車用半導體","EV零組件","整車/充電","機械工具機"],
    "原物料循環":    ["鋼鐵","石化","水泥建材"],
    "航運大循環":    ["航運貨櫃","航運散裝/航空"],
    "金融防禦":      ["公股銀行","民營金控","保險證券"],
    "綠能轉型":      ["太陽能","儲能/電池","EV零組件"],
    "消費內需":      ["食品消費","紡織成衣","不動產"],
}

# ──────────────────────────────────────────────────────────────────────────────
# 查詢函數
# ──────────────────────────────────────────────────────────────────────────────

def get_all_stocks() -> dict:
    result = {}
    for sector, info in STOCK_UNIVERSE.items():
        for code, s in info["stocks"].items():
            result[code] = {
                **s, "sector": sector,
                "mega":   info["mega"],
                "group":  info.get("group",""),
                "themes": info.get("theme",[]),
            }
    return result

def get_sector_list() -> list:
    return list(STOCK_UNIVERSE.keys())

def get_stocks_by_sector(sector: str) -> dict:
    return STOCK_UNIVERSE.get(sector,{}).get("stocks",{})

def get_supply_chain(sector: str) -> dict:
    stocks = get_stocks_by_sector(sector)
    chain = {"上游":{},"中游":{},"下游":{},"—":{}}
    for code, info in stocks.items():
        chain[info.get("chain","—")][code] = info
    return {k:v for k,v in chain.items() if v}

def get_groups() -> dict:
    """依 group 分組（例如：半導體下有6個細分產業）"""
    result = {}
    for sector, info in STOCK_UNIVERSE.items():
        g = info.get("group","其他")
        if g not in result:
            result[g] = []
        result[g].append(sector)
    return result

def get_summary() -> dict:
    all_s = get_all_stocks()
    groups = get_groups()
    return {
        "total_stocks":  len(all_s),
        "total_sectors": len(STOCK_UNIVERSE),
        "total_groups":  len(groups),
        "total_themes":  len(THEMES),
        "groups": {g: len(s) for g,s in groups.items()},
    }

def search_stock(kw: str) -> dict:
    return {c:i for c,i in get_all_stocks().items()
            if kw in c or kw in i["name"]}


if __name__ == "__main__":
    s = get_summary()
    print(f"台股分類資料庫 v2")
    print(f"  總計：{s['total_stocks']} 檔 / {s['total_sectors']} 產業 / {s['total_groups']} 大類")
    print(f"\n產業群組：")
    for g, cnt in s["groups"].items():
        sectors = [sec for sec,info in STOCK_UNIVERSE.items() if info.get("group")==g]
        print(f"  [{g}] {cnt}個細分：{', '.join(sectors)}")
    print(f"\n主題板塊：{list(THEMES.keys())}")
