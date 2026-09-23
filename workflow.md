# Workflow — Taiwan Weather Forecast（AIot-HW1-CWA）

> 從 CWA API → JSON → Pandas → SQLite → Streamlit / Folium 的實作流程。
> 共 24 個步驟，分成 6 個階段。**每個步驟都有一道 Gate（關卡）**：Gate 沒通過，就不進入下一步。

---

## 如何使用這份文件

每個步驟包含四個部分：

| 欄位 | 意義 |
|---|---|
| **目標** | 這一步要完成什麼 |
| **產出** | 完成後應該存在的檔案、程式或結果 |
| **Gate ✅** | 可以實際執行或檢查的驗收條件，全部打勾才算通過 |
| **Gate 沒過時** | 最常見的原因與處理方式 |

階段結束時另有一道 **階段 Gate（Milestone）**，用來確認整段流程串得起來。

> ⚠️ 目前 repo 只有 `README.md`（1 個 commit）。README 中列出的 `config.py`、`fetch_cwa.py`、`database.py`、`app.py`、`requirements.txt` 都還需要依本流程建立。

---

## 進度總表

| # | 步驟 | 階段 | 主要產出 | Gate |
|---|---|---|---|---|
| 01 | 課程介紹 | A 準備 | 專案目標說明 | ☐ |
| 02 | 台灣的天氣與生活 | A 準備 | 應用情境 | ☐ |
| 03 | CWA Open Data 平台 | A 準備 | API Key、`.env` | ☐ |
| 04 | API 資料取得 | B 資料取得 | `fetch_cwa.py`（抓取） | ☐ |
| 05 | JSON 結構解析 | B 資料取得 | 氣溫資料路徑 | ☐ |
| 06 | 提取 MinT / MaxT | B 資料取得 | `parse_temperatures()` | ☐ |
| 07 | Pandas 整理與預覽 | B 資料取得 | 乾淨的 DataFrame | ☐ |
| 08 | 建立 SQLite 資料庫 | C 資料庫 | `data/data.db` | ☐ |
| 09 | 資料庫設計 | C 資料庫 | `TemperatureForecasts` | ☐ |
| 10 | SQL 查詢驗證 | C 資料庫 | 驗證查詢結果 | ☐ |
| 11 | Streamlit 入門 | D Web App | Hello World | ☐ |
| 12 | 從資料庫讀取資料 | D Web App | `load_data()` | ☐ |
| 13 | 下拉選單選地區 | D Web App | `st.selectbox` | ☐ |
| 14 | 繪製折線圖 | D Web App | MaxT / MinT 折線圖 | ☐ |
| 15 | 顯示資料表格 | D Web App | 一週預報表 | ☐ |
| 16 | 整合 Web App 介面 | D Web App | 完整 `app.py` | ☐ |
| 17 | 台灣地圖視覺化 | E 進階 | Folium 地圖 | ☐ |
| 18 | 選擇日期顯示地圖 | E 進階 | 日期切換地圖 | ☐ |
| 19 | 完整成果展示 | E 進階 | Dashboard | ☐ |
| 20 | 程式碼品質與優化 | F 收尾 | 重構、錯誤處理 | ☐ |
| 21 | 上傳至 GitHub | F 收尾 | Commit & Push | ☐ |
| 22 | 延伸應用與想法 | F 收尾 | 延伸構想 | ☐ |
| 23 | 回顧與重點整理 | F 收尾 | 學習重點 | ☐ |
| 24 | 下一步：繼續探索 | F 收尾 | 後續計畫 | ☐ |

---

## 目標目錄結構

```
AIot-HW1-CWA/
├── .gitignore
├── .env                  # 不上傳（放 API Key）
├── .env.example          # 上傳（範本，不含真實 Key）
├── README.md
├── workflow.md
├── requirements.txt
├── config.py
├── fetch_cwa.py
├── database.py
├── app.py
└── data/
    ├── raw_cwa.json      # 原始 API 回應（除錯用，不上傳）
    └── data.db
```

---

# 階段 A — 準備（Step 01–03）

## Step 01｜課程介紹：AI × 資料 × 天氣 × 實作

**目標**：清楚知道要做出什麼，以及資料怎麼流動。

**產出**
- 能用一句話說明專案：「抓 CWA 一週天氣預報 → 存進 SQLite → 用 Streamlit 選地區看氣溫與地圖」
- 資料流程：`CWA API → JSON → Pandas → SQLite → Streamlit（折線圖／表格／地圖）`

**Gate ✅**
- [ ] 能畫出（或口述）上面的 5 段資料流程
- [ ] 知道最終成果包含 3 個畫面元件：折線圖、資料表、台灣地圖

**Gate 沒過時**：重看 README 的「系統架構與資料流程」。

---

## Step 02｜台灣的天氣與生活

**目標**：定義使用者情境，讓後面的 UI 設計有依據。

**產出**
- 2–3 個使用情境，例如：出門前看中部地區這週高低溫、比較全台同一天的溫度分布

**Gate ✅**
- [ ] 每個情境都對應到 App 的一個功能（選地區 → 折線圖／表格；選日期 → 地圖）

**Gate 沒過時**：刪掉無法對應到功能的情境，或把它記到 Step 22 的延伸想法。

---

## Step 03｜中央氣象署 CWA Open Data 平台

**目標**：取得 API Key、選定資料集，並把 Key 安全地放在程式外。

**做法**
1. 到 <https://opendata.cwa.gov.tw/> 註冊並登入，取得「授權碼」（API Key）。
2. 選定資料集。課程圖使用的地區為 **北部、中部、南部、東北部、東部、東南部地區**，對應的是「一週天氣預報（分區）」類型的資料集（常用代碼為 `F-A0010-001`，**請在平台上確認代碼與欄位**）。
   若改用縣市資料（如 `F-C0032-001` 36 小時預報、`F-D0047-091` 一週縣市預報），`regionName` 就會變成縣市名稱，後續地圖座標也要跟著改。
3. 建立 `.env` 與 `.env.example`，並設定 `.gitignore`。

```
# .env（不上傳）
CWA_API_KEY=CWA-XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX
```

```
# .gitignore
.env
venv/
__pycache__/
data/raw_cwa.json
# 若不想把資料庫放進 repo，再加上：data/data.db
```

```python
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

CWA_API_KEY = os.getenv("CWA_API_KEY")
DATASET_ID = "F-A0010-001"        # 依 Step 03 確認的資料集修改
DB_PATH = "data/data.db"
RAW_JSON_PATH = "data/raw_cwa.json"
```

**產出**：`.env`、`.env.example`、`.gitignore`、`config.py`、`requirements.txt`

```
# requirements.txt
requests
pandas
python-dotenv
streamlit
altair
folium
streamlit-folium
```

**Gate ✅**
- [ ] `python -c "import config; print(bool(config.CWA_API_KEY))"` 印出 `True`
- [ ] `git check-ignore .env` 有輸出 `.env`（代表不會被上傳）
- [ ] `pip install -r requirements.txt` 無錯誤
- [ ] 已記錄選用的資料集代碼，以及它的地區清單

**Gate 沒過時**
- 印出 `False`：`.env` 不在專案根目錄，或變數名稱拼錯。
- `.env` 沒被忽略：確認 `.gitignore` 內容；若之前已 commit 過，要 `git rm --cached .env`，並**到 CWA 平台重新產生 Key**。

### 🏁 階段 A Milestone
- [ ] 虛擬環境可用、套件已安裝、Key 可讀取且不會進 Git

---

# 階段 B — 資料取得（Step 04–07）

## Step 04｜API 資料取得（Requests → JSON）

**目標**：成功呼叫 API，並把原始 JSON 存檔，方便後續解析。

```python
# fetch_cwa.py（第一部分）
import json
import requests
import config

def fetch_raw() -> dict:
    url = f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{config.DATASET_ID}"
    params = {"Authorization": config.CWA_API_KEY, "format": "JSON"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    with open(config.RAW_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data
```

> 端點格式依資料集而異：檔案型資料集用 `/fileapi/v1/opendataapi/{ID}`，一般資料集用 `/api/v1/rest/datastore/{ID}`。以平台上的 API 說明為準。

**產出**：`data/raw_cwa.json`

**Gate ✅**
- [ ] HTTP 狀態碼為 `200`
- [ ] `data/raw_cwa.json` 存在，且大小 > 0
- [ ] `python -c "import json;print(list(json.load(open('data/raw_cwa.json',encoding='utf-8')).keys()))"` 能印出最外層鍵值

**Gate 沒過時**
- `401`／`403`：API Key 錯誤，或忘記傳 `Authorization`。
- `404`：資料集代碼錯誤，或端點類型（`fileapi` / `datastore`）用錯。
- Timeout：確認網路，或把 `timeout` 調大。

---

## Step 05｜JSON 資料結構解析

**目標**：找到「地區名稱」、「日期」、「最低溫」、「最高溫」各自位於哪一層。

**做法**：用程式逐層印出鍵值，不要靠猜：

```python
import json
d = json.load(open("data/raw_cwa.json", encoding="utf-8"))

def walk(node, path="root", depth=0, max_depth=6):
    if depth > max_depth:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            print("  " * depth + f"{path}.{k}  ({type(v).__name__})")
            walk(v, f"{path}.{k}", depth + 1)
    elif isinstance(node, list) and node:
        print("  " * depth + f"{path}[0]  (list, len={len(node)})")
        walk(node[0], f"{path}[0]", depth + 1)

walk(d)
```

**產出**：寫進程式註解的「資料路徑表」，例如：

```
地區清單：   <路徑>.location[]
地區名稱：   location[i].locationName
最高溫：     location[i]...MaxT...（每日陣列）
最低溫：     location[i]...MinT...（每日陣列）
日期欄位：   dataDate / startTime（依資料集）
溫度欄位：   temperature / value（依資料集）
```

**Gate ✅**
- [ ] 能用一行程式取到「第一個地區的名稱」
- [ ] 能用一行程式取到「第一個地區、第一天的 MaxT 與日期」
- [ ] 地區數量符合預期（分區資料集應為 6 個地區）

**Gate 沒過時**：溫度可能放在 `weatherElement[]` 陣列中，需要依 `elementName == "MaxT"` 篩選，而不是直接用鍵名取值。

---

## Step 06｜提取最高與最低氣溫（MinT / MaxT）

**目標**：把巢狀 JSON 轉成「一列一筆」的扁平資料。

```python
# fetch_cwa.py（第二部分）— 依 Step 05 的路徑表調整
def parse_temperatures(data: dict) -> list[dict]:
    rows = []
    locations = ...  # 依 Step 05 找到的路徑填入
    for loc in locations:
        region = loc["locationName"]
        max_by_date = {d["dataDate"]: d["temperature"] for d in ...}  # MaxT 每日陣列
        min_by_date = {d["dataDate"]: d["temperature"] for d in ...}  # MinT 每日陣列
        for date in sorted(set(max_by_date) | set(min_by_date)):
            rows.append({
                "regionName": region,
                "dataDate": date,
                "minT": min_by_date.get(date),
                "maxT": max_by_date.get(date),
            })
    return rows
```

**產出**：`parse_temperatures()` 函式，回傳 `list[dict]`

**Gate ✅**
- [ ] 回傳筆數 ≈ 地區數 × 天數（例如 6 × 7 = 42）
- [ ] 每筆都有 `regionName`、`dataDate`、`minT`、`maxT` 四個鍵
- [ ] 抽查 1 筆，數值與 `raw_cwa.json` 原始資料一致

**Gate 沒過時**：MinT 與 MaxT 的日期若沒對齊，檢查是否一個用日期、一個用時間戳記；統一截成 `YYYY-MM-DD` 後再合併。

---

## Step 07｜資料整理與預覽（Pandas）

**目標**：轉型、清洗，確保進資料庫前的資料是乾淨的。

```python
import pandas as pd

def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["dataDate"] = pd.to_datetime(df["dataDate"]).dt.strftime("%Y-%m-%d")
    df["minT"] = pd.to_numeric(df["minT"], errors="coerce")
    df["maxT"] = pd.to_numeric(df["maxT"], errors="coerce")
    df = df.dropna(subset=["regionName", "dataDate"])
    df = df.drop_duplicates(subset=["regionName", "dataDate"], keep="last")
    return df.sort_values(["regionName", "dataDate"]).reset_index(drop=True)
```

**產出**：DataFrame，欄位為 `regionName | dataDate | minT | maxT`

**Gate ✅**
- [ ] `df.dtypes`：`minT`、`maxT` 為 `float64`，`dataDate` 為 `YYYY-MM-DD` 字串
- [ ] `df.duplicated(["regionName","dataDate"]).sum() == 0`
- [ ] `(df["minT"] <= df["maxT"]).all()` 為 `True`
- [ ] 溫度落在合理範圍：`df[["minT","maxT"]].stack().between(-10, 45).all()`
- [ ] `df.head()` 的樣子和課程圖 Step 7 的表格一致

**Gate 沒過時**：有 `NaN` 時，回到 Step 06 檢查該地區、該日期是否缺資料；缺資料可以保留 `NaN`，但要在 Step 20 決定顯示方式。

### 🏁 階段 B Milestone
- [ ] `python fetch_cwa.py`（暫時只到 Step 07）能從 API 一路產出乾淨的 DataFrame，並印出前 5 列

---

# 階段 C — 資料庫（Step 08–10）

## Step 08｜建立 SQLite 資料庫

**目標**：建立 `data/data.db`，並把連線邏輯集中在 `database.py`。

```python
# database.py
import os
import sqlite3
import config

def get_conn() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    return sqlite3.connect(config.DB_PATH)
```

**Gate ✅**
- [ ] 執行後 `data/data.db` 存在
- [ ] `python -c "import database; database.get_conn().close()"` 無錯誤

**Gate 沒過時**：`unable to open database file` 通常代表 `data/` 資料夾不存在，或路徑是相對於「執行位置」而不是專案根目錄。

---

## Step 09｜資料庫設計（TemperatureForecasts）

**目標**：建立資料表，並用唯一鍵防止重複寫入。

```python
# database.py（續）
SCHEMA = """
CREATE TABLE IF NOT EXISTS TemperatureForecasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    regionName TEXT NOT NULL,
    dataDate   TEXT NOT NULL,
    minT REAL,
    maxT REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(regionName, dataDate)
);
"""

def init_db():
    with get_conn() as conn:
        conn.execute(SCHEMA)

def upsert(df):
    sql = """
    INSERT INTO TemperatureForecasts (regionName, dataDate, minT, maxT)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(regionName, dataDate)
    DO UPDATE SET minT = excluded.minT,
                  maxT = excluded.maxT,
                  created_at = CURRENT_TIMESTAMP;
    """
    records = df[["regionName", "dataDate", "minT", "maxT"]].itertuples(index=False, name=None)
    with get_conn() as conn:
        conn.executemany(sql, list(records))
```

```python
# fetch_cwa.py（主程式）
import database

if __name__ == "__main__":
    data = fetch_raw()
    df = to_dataframe(parse_temperatures(data))
    database.init_db()
    database.upsert(df)
    print(f"寫入 {len(df)} 筆")
```

**Gate ✅**
- [ ] `sqlite3 data/data.db ".schema TemperatureForecasts"` 顯示含 `UNIQUE(regionName, dataDate)` 的結構
- [ ] 第一次執行 `python fetch_cwa.py`，資料筆數 = DataFrame 筆數
- [ ] **連續執行兩次**後，筆數不變（證明沒有重複插入）

**Gate 沒過時**：`ON CONFLICT ... DO UPDATE` 需要 SQLite 3.24 以上；可用 `python -c "import sqlite3;print(sqlite3.sqlite_version)"` 確認，版本太舊就改用 `INSERT OR REPLACE`。

---

## Step 10｜查詢資料驗證（SQL）

**目標**：用 SQL 確認資料庫內容正確，再交給前端使用。

```sql
-- 1. 所有地區
SELECT DISTINCT regionName FROM TemperatureForecasts;

-- 2. 特定地區一週氣溫
SELECT dataDate, minT, maxT
FROM TemperatureForecasts
WHERE regionName = '中部地區'
ORDER BY dataDate;

-- 3. 每個地區的天數（應該一致）
SELECT regionName, COUNT(*) AS days
FROM TemperatureForecasts
GROUP BY regionName;

-- 4. 異常資料（應回傳 0 列）
SELECT * FROM TemperatureForecasts
WHERE minT IS NULL OR maxT IS NULL OR minT > maxT;
```

**Gate ✅**
- [ ] 查詢 1 回傳的地區數，與 Step 05 一致
- [ ] 查詢 2 回傳 7 天左右、日期遞增的資料
- [ ] 查詢 3 各地區天數相同
- [ ] 查詢 4 回傳 0 列（或每一列都有已知原因）

**Gate 沒過時**：查詢 2 回傳空結果，最常見的原因是地區名稱不一致（例如「臺」和「台」、多了空白）。先用查詢 1 複製實際名稱再查。

### 🏁 階段 C Milestone
- [ ] `python fetch_cwa.py` 一個指令就能完成「抓取 → 解析 → 清洗 → 入庫」，而且可以重複執行

---

# 階段 D — Web App（Step 11–16）

## Step 11｜Streamlit 入門

```python
# app.py（暫時版本）
import streamlit as st
st.title("Taiwan Weather Forecast")
st.write("Hello World")
```

**Gate ✅**
- [ ] `streamlit run app.py` 啟動，瀏覽器開啟 `http://localhost:8501`
- [ ] 頁面顯示標題與 Hello World

**Gate 沒過時**：Port 被占用時可用 `streamlit run app.py --server.port 8502`。

---

## Step 12｜從資料庫讀取資料

```python
import sqlite3
import pandas as pd
import streamlit as st
import config

@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:
    with sqlite3.connect(config.DB_PATH) as conn:
        return pd.read_sql_query(
            "SELECT regionName, dataDate, minT, maxT "
            "FROM TemperatureForecasts ORDER BY regionName, dataDate",
            conn,
        )
```

**Gate ✅**
- [ ] `load_data()` 回傳筆數，和 Step 10 `SELECT COUNT(*)` 的結果相同
- [ ] 資料庫不存在或為空時，頁面顯示友善訊息（例如「請先執行 `python fetch_cwa.py`」），而不是錯誤堆疊

**Gate 沒過時**：`no such table` 代表 Streamlit 讀到另一個 `data.db`；確認是在專案根目錄執行，或在 `config.py` 改用絕對路徑。

---

## Step 13｜下拉選單選擇地區

```python
df = load_data()
regions = sorted(df["regionName"].unique())
region = st.selectbox("Select Region", regions)
region_df = df[df["regionName"] == region]
```

**Gate ✅**
- [ ] 選單列出所有地區（北部、中部、南部、東北部、東部、東南部）
- [ ] 切換地區後，`region_df` 的內容跟著改變

---

## Step 14｜繪製折線圖（一週最高與最低氣溫）

```python
import altair as alt

chart_df = region_df.melt(
    id_vars="dataDate", value_vars=["maxT", "minT"],
    var_name="type", value_name="temp",
)
chart = alt.Chart(chart_df).mark_line(point=True).encode(
    x=alt.X("dataDate:N", title="日期"),
    y=alt.Y("temp:Q", title="氣溫 (°C)", scale=alt.Scale(zero=False)),
    color=alt.Color("type:N", scale=alt.Scale(
        domain=["maxT", "minT"], range=["#e4572e", "#2e86de"])),
    tooltip=["dataDate", "type", "temp"],
)
st.altair_chart(chart, use_container_width=True)
```

**Gate ✅**
- [ ] 圖上有 MaxT（紅）與 MinT（藍）兩條線
- [ ] X 軸日期由左到右遞增
- [ ] MaxT 線整條都在 MinT 線之上
- [ ] 滑鼠移到點上，數值和 Step 10 查詢 2 的結果一致

---

## Step 15｜顯示資料表格

```python
st.dataframe(
    region_df.rename(columns={"dataDate": "Date", "minT": "MinT", "maxT": "MaxT"})
             [["Date", "MinT", "MaxT"]],
    hide_index=True, use_container_width=True,
)
```

**Gate ✅**
- [ ] 表格欄位為 `Date | MinT | MaxT`，列數等於該地區天數
- [ ] 表格與折線圖的數值一致

---

## Step 16｜整合 Web App 介面

**目標**：把 Step 11–15 組成一個完整頁面。

**建議版面**
- 標題與說明（資料來源：中央氣象署、最後更新時間）
- 側邊欄：地區選單
- 主畫面：左邊折線圖、右邊資料表（`st.columns`）

**Gate ✅**
- [ ] 只用一個地區選單，就能同步控制折線圖與表格
- [ ] 顯示資料的最後更新時間（`MAX(created_at)`）
- [ ] 手機寬度（瀏覽器縮窄）下仍可閱讀
- [ ] 頁面無錯誤或警告訊息

### 🏁 階段 D Milestone
- [ ] 從空資料夾開始：`pip install -r requirements.txt` → `python fetch_cwa.py` → `streamlit run app.py`，能看到可操作的「選地區看氣溫」頁面

---

# 階段 E — 進階視覺化（Step 17–19）

## Step 17｜台灣地圖視覺化（Folium + Streamlit）

```python
import folium
from streamlit_folium import st_folium

# 分區的大略中心座標（改用縣市資料時要換成縣市座標）
REGION_COORDS = {
    "北部地區":   (25.03, 121.52),
    "東北部地區": (24.70, 121.75),
    "中部地區":   (24.15, 120.68),
    "東部地區":   (23.98, 121.60),
    "南部地區":   (22.90, 120.35),
    "東南部地區": (22.75, 121.15),
}

def temp_color(avg: float) -> str:
    if avg < 20:  return "blue"
    if avg < 25:  return "green"
    if avg < 30:  return "orange"
    return "red"

def build_map(day_df):
    m = folium.Map(location=[23.7, 121.0], zoom_start=7, tiles="cartodbpositron")
    for _, r in day_df.iterrows():
        lat, lon = REGION_COORDS[r["regionName"]]
        avg = (r["minT"] + r["maxT"]) / 2
        folium.CircleMarker(
            location=[lat, lon], radius=12,
            color=temp_color(avg), fill=True, fill_opacity=0.8,
            tooltip=f'{r["regionName"]}<br>Min: {r["minT"]}°C<br>Max: {r["maxT"]}°C',
        ).add_to(m)
    return m
```

**Gate ✅**
- [ ] 地圖以台灣為中心，所有地區都有標記
- [ ] 顏色依平均溫度分成 4 級：`< 20°C` 藍、`20–25°C` 綠、`25–30°C` 橘、`> 30°C` 紅
- [ ] 有圖例說明顏色代表的溫度區間
- [ ] 滑鼠移到標記上會顯示地區名稱與高低溫
- [ ] `REGION_COORDS` 的鍵，和資料庫的 `regionName` **完全一致**（沒有地區因找不到座標而漏畫）

**Gate 沒過時**：`KeyError` 代表地區名稱不一致；可以改用 `REGION_COORDS.get()`，並在畫面上列出找不到座標的地區。

---

## Step 18｜選擇日期顯示地圖

```python
dates = sorted(df["dataDate"].unique())
selected_date = st.selectbox("Select Date", dates)
day_df = df[df["dataDate"] == selected_date]
st_folium(build_map(day_df), height=520, use_container_width=True)
```

**Gate ✅**
- [ ] 日期選單只列出資料庫中有的日期
- [ ] 切換日期後，地圖標記顏色與提示數值跟著改變
- [ ] 抽查 1 個地區、1 個日期，地圖數值和 Step 10 的查詢結果一致

---

## Step 19｜完整成果展示（Taiwan Weather Dashboard）

**目標**：整合成一個完整儀表板。

**建議版面**
- `st.tabs(["地區預報", "全台地圖"])`，或上下排版
- 地區預報：地區選單 + 折線圖 + 表格
- 全台地圖：日期選單 + 地圖 + 當日各地區資料表

**Gate ✅**
- [ ] 課程圖 Step 13–18 的每個功能都能在 Dashboard 找到
- [ ] 所有元件的數值彼此一致
- [ ] 截圖存檔（之後放進 README）

### 🏁 階段 E Milestone
- [ ] 請一位沒看過程式的人操作 Dashboard，他能在 1 分鐘內回答：「中部地區明天最高溫幾度？」與「哪一天全台最熱？」

---

# 階段 F — 收尾（Step 20–24）

## Step 20｜程式碼品質與優化

**檢查清單**

| 項目 | 要求 |
|---|---|
| 結構清晰 | 抓取在 `fetch_cwa.py`、資料庫在 `database.py`、畫面在 `app.py`、設定在 `config.py` |
| 錯誤處理 | 網路錯誤、401/404、JSON 結構改變、資料庫不存在，都要有明確訊息 |
| 防重複插入 | 靠 `UNIQUE(regionName, dataDate)` + upsert |
| 註解 | 每個函式都有 docstring；JSON 路徑附上說明 |
| 機密 | 程式碼中沒有寫死 API Key |

```python
# fetch_cwa.py 錯誤處理範例
try:
    data = fetch_raw()
except requests.HTTPError as e:
    raise SystemExit(f"CWA API 回應錯誤：{e.response.status_code}，請確認 API Key 與資料集代碼")
except requests.RequestException as e:
    raise SystemExit(f"無法連線到 CWA API：{e}")
```

**Gate ✅**
- [ ] 把 `.env` 暫時改成錯誤的 Key，執行 `python fetch_cwa.py` 會出現清楚的中文錯誤訊息，而不是錯誤堆疊
- [ ] 刪掉 `data/data.db` 再開 App，畫面會提示要先抓資料
- [ ] `git grep -n "CWA-"` 沒有找到任何真實 Key
- [ ] （選做）`pip install ruff && ruff check .` 沒有錯誤

---

## Step 21｜專案上傳至 GitHub

```bash
git status                      # 確認 .env 不在清單中
git add .
git commit -m "feat: CWA weather dashboard (fetch, SQLite, Streamlit, Folium)"
git remote -v                   # 確認指向 BlueET1/AIot-HW1-CWA
git push origin main
```

**Gate ✅**
- [ ] `git status` 在 commit 前沒有出現 `.env`
- [ ] GitHub 網頁上看得到 `config.py`、`fetch_cwa.py`、`database.py`、`app.py`、`requirements.txt`
- [ ] GitHub 網頁上**看不到** `.env`
- [ ] 在新資料夾 `git clone` 下來，依 README 的步驟可以成功跑起來
- [ ] README 的目錄結構與實際檔案一致，並放上 Step 19 的截圖

**Gate 沒過時**：若 Key 已經被推上去，只刪檔案不夠（Git 歷史還在）——請**立刻到 CWA 平台重新產生 Key**。

---

## Step 22｜延伸應用與想法

**產出**：在 README「未來延伸」挑 1 項，寫下可行性評估

| 想法 | 需要的額外資料或服務 | 難度 |
|---|---|---|
| 天氣提醒 Line Bot | LINE Messaging API、排程 | 中 |
| 旅遊行程建議 | 降雨機率欄位（PoP） | 低 |
| 農業／防災應用 | 低溫、豪雨警特報資料集 | 中 |
| 結合 AI 做分析 | LLM API，把一週資料生成口語摘要 | 低–中 |

**Gate ✅**
- [ ] 選定 1 個延伸項目，寫出：需要的資料集、新增的欄位或表格、預估工作量

---

## Step 23｜回顧與重點整理

**Gate ✅（每項都能自己解釋）**
- [ ] API 資料取得：端點、授權參數、錯誤碼的意思
- [ ] JSON 資料分析：怎麼找到巢狀資料的路徑
- [ ] SQLite 資料庫：為什麼需要 `UNIQUE` 和 upsert
- [ ] Streamlit Web App：`cache_data` 的用途、元件如何連動
- [ ] AI × Coding 實作流程：哪些部分請 AI 協助、哪些部分自己驗證

---

## Step 24｜下一步：繼續探索

**方向**：更多公開資料 API、資料視覺化應用、AI 輔助開發、打造自己的專案作品

**Gate ✅**
- [ ] 列出下一個要串接的公開資料集（例如 CWA 其他資料集、環境部空品資料）
- [ ] 寫下 1 個可以重複使用這套流程（API → DB → Dashboard）的新題目

### 🏁 階段 F Milestone（作業完成）
- [ ] 24 個 Gate 全部打勾
- [ ] Repo 可以從零 clone、安裝、執行
- [ ] 沒有外洩任何 API Key
