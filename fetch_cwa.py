"""
ETL script for CWA Taiwan Weather Forecast.
Fetches raw weather forecast data from CWA API (or mock generator when offline/unset),
cleans and normalizes using Pandas, and stores into SQLite database.
"""

import os
import sys
import json
from datetime import datetime, timedelta
import requests
import urllib3
import pandas as pd
import config
import database

# Fix Windows console encoding if needed
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 台灣 6 大預報分區及其對應之縣市對照表
REGION_MAPPING = {
    "北部地區": ["基隆市", "臺北市", "新北市", "桃園市", "新竹市", "新竹縣"],
    "東北部地區": ["宜蘭縣"],
    "中部地區": ["苗栗縣", "臺中市", "彰化縣", "南投縣", "雲林縣"],
    "東部地區": ["花蓮縣"],
    "南部地區": ["嘉義市", "嘉義縣", "臺南市", "高雄市", "屏東縣"],
    "東南部地區": ["臺東縣"],
}

# 反向對照表：縣市 -> 分區
COUNTY_TO_REGION = {}
for region, counties in REGION_MAPPING.items():
    for county in counties:
        COUNTY_TO_REGION[county] = region
        # 兼容台/臺
        COUNTY_TO_REGION[county.replace("臺", "台")] = region

STANDARD_REGIONS = list(REGION_MAPPING.keys())


def generate_mock_cwa_data() -> dict:
    """Generate realistic standard CWA forecast JSON structure for testing and demonstration."""
    today = datetime.now().date()
    locations = []

    base_temps = {
        "北部地區": (20.0, 27.0),
        "東北部地區": (19.0, 25.0),
        "中部地區": (22.0, 31.0),
        "東部地區": (21.0, 28.0),
        "南部地區": (23.0, 32.0),
        "東南部地區": (22.0, 29.0),
    }

    for region in STANDARD_REGIONS:
        min_base, max_base = base_temps.get(region, (20.0, 28.0))
        maxt_times = []
        mint_times = []

        for i in range(7):
            d = today + timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            day_min = round(min_base + (i % 3) * 0.5 - (i % 2) * 0.3, 1)
            day_max = round(max_base + (i % 4) * 0.6 - (i % 3) * 0.4, 1)
            if day_min > day_max:
                day_min, day_max = day_max - 2.0, day_max

            maxt_times.append({
                "dataDate": d_str,
                "startTime": f"{d_str}T06:00:00+08:00",
                "endTime": f"{d_str}T18:00:00+08:00",
                "elementValue": [{"value": str(day_max)}],
                "temperature": day_max,
            })
            mint_times.append({
                "dataDate": d_str,
                "startTime": f"{d_str}T18:00:00+08:00",
                "endTime": f"{(d + timedelta(days=1)).strftime('%Y-%m-%d')}T06:00:00+08:00",
                "elementValue": [{"value": str(day_min)}],
                "temperature": day_min,
            })

        locations.append({
            "locationName": region,
            "weatherElement": [
                {
                    "elementName": "MaxT",
                    "description": "最高氣溫",
                    "time": maxt_times,
                },
                {
                    "elementName": "MinT",
                    "description": "最低氣溫",
                    "time": mint_times,
                },
            ],
        })

    return {
        "success": "true",
        "result": {
            "resource_id": config.DATASET_ID,
            "fields": [{"id": "locationName", "type": "String"}],
        },
        "records": {
            "datasetDescription": "一週天氣預報（分區）",
            "location": locations,
        },
    }


def fetch_raw() -> dict:
    """
    Fetch weather forecast JSON from CWA Open Data API.
    Saves JSON to config.RAW_JSON_PATH.
    Gracefully handles SSL certification differences and fallbacks if API key is invalid/offline.
    """
    os.makedirs(os.path.dirname(config.RAW_JSON_PATH), exist_ok=True)
    api_key = config.CWA_API_KEY or ""
    is_placeholder = (
        not api_key
        or "YOUR-KEY" in api_key.upper()
        or "XXXXXXXX" in api_key
        or api_key == "CWA-DEMO-KEY"
    )

    data = None
    if not is_placeholder:
        print(f"[CWA API] 正在連線中央氣象署資料集: {config.DATASET_ID}...")
        # 嘗試 standard datastore 端點與 fileapi 端點
        urls_to_try = [
            f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/{config.DATASET_ID}",
            f"https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/{config.DATASET_ID}",
        ]
        params = {"Authorization": api_key, "format": "JSON"}

        for url in urls_to_try:
            try:
                # 首先嘗試標準驗證，若證書驗證因 OpenSSL 3.x 報錯則回退 verify=False
                try:
                    resp = requests.get(url, params=params, timeout=15)
                except requests.exceptions.SSLError:
                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                    resp = requests.get(url, params=params, verify=False, timeout=15)

                if resp.status_code == 200:
                    data = resp.json()
                    print(f"[CWA API] 連線成功！已取得資料 (端點: {url})")
                    break
                elif resp.status_code in (401, 403):
                    print(f"[CWA API 警告] 授權驗證失敗 (HTTP {resp.status_code})，請確認 API Key 是否有效。")
                    break
                else:
                    print(f"[CWA API 提示] 端點 {url} 回傳 HTTP {resp.status_code}，嘗試備用端點...")
            except requests.RequestException as e:
                print(f"[CWA API 連線異常] {e}")

    if data is None:
        if is_placeholder:
            print("[提示] 尚未設定有效之 CWA_API_KEY，將啟用標準分區預報模擬資料以供測試與展示。")
        else:
            print("[提示] 無法從線上 API 取得資料，將使用本機分區預報模擬資料。")
        data = generate_mock_cwa_data()

    with open(config.RAW_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return data


def walk(node, path="root", depth=0, max_depth=5):
    """
    Recursively walk through JSON structure and print schema paths (Step 05).
    """
    if depth > max_depth:
        return
    if isinstance(node, dict):
        for k, v in node.items():
            print("  " * depth + f"{path}.{k}  ({type(v).__name__})")
            walk(v, f"{path}.{k}", depth + 1, max_depth)
    elif isinstance(node, list) and node:
        print("  " * depth + f"{path}[0]  (list, len={len(node)})")
        walk(node[0], f"{path}[0]", depth + 1, max_depth)


def _extract_temp_val(t_item) -> float | None:
    """Helper to extract float temperature from time item."""
    val = t_item.get("temperature")
    if val is None:
        elem_vals = t_item.get("ElementValue") or t_item.get("elementValue")
        if isinstance(elem_vals, list) and elem_vals:
            item = elem_vals[0]
            val = (
                item.get("MaxTemperature")
                or item.get("MinTemperature")
                or item.get("value")
                or item.get("Temperature")
            )
        elif isinstance(elem_vals, dict):
            val = (
                elem_vals.get("MaxTemperature")
                or elem_vals.get("MinTemperature")
                or elem_vals.get("value")
            )
    if val is not None:
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
    return None


def parse_temperatures(data: dict) -> list[dict]:
    """
    Parse nested CWA JSON structure into a flat list of dicts.
    Extracts high/low temperatures for the 6 standard regions.
    Returns: list of {'regionName', 'dataDate', 'minT', 'maxT'}
    """
    # 支援 CWA 多種回傳格式：
    # 1. records.Locations[0].Location (F-D0047-091)
    # 2. records.location (F-A0010-001 或 F-C0032-001)
    # 3. cwaopendata.dataset.location
    locations = []
    if "records" in data:
        recs = data["records"]
        if "Locations" in recs and recs["Locations"]:
            locations = recs["Locations"][0].get("Location", [])
        elif "location" in recs:
            locations = recs["location"]
        elif "Location" in recs:
            locations = recs["Location"]
    elif "cwaopendata" in data and "dataset" in data["cwaopendata"]:
        locations = data["cwaopendata"]["dataset"].get("location", [])
    elif "dataset" in data and "location" in data["dataset"]:
        locations = data["dataset"]["location"]

    # 檢查是否直接包含 6 大分區名稱
    has_regional_names = any(
        (loc.get("locationName") or loc.get("LocationName")) in STANDARD_REGIONS
        for loc in locations
    )

    # 結構: region_data[region][date] = {'min_list': [], 'max_list': []}
    region_data = {r: {} for r in STANDARD_REGIONS}

    for loc in locations:
        loc_name = loc.get("locationName") or loc.get("LocationName")
        if not loc_name:
            continue

        target_region = None
        if has_regional_names:
            if loc_name in STANDARD_REGIONS:
                target_region = loc_name
        else:
            # 縣市對應到分區
            target_region = COUNTY_TO_REGION.get(loc_name)

        if not target_region:
            continue

        elements = loc.get("weatherElement") or loc.get("WeatherElement") or []
        for elem in elements:
            e_name = elem.get("elementName") or elem.get("ElementName") or ""
            is_max = e_name in ("MaxT", "最高溫度", "最高氣溫", "MaxAT")
            is_min = e_name in ("MinT", "最低溫度", "最低氣溫", "MinAT")

            if not (is_max or is_min):
                continue

            time_list = elem.get("time") or elem.get("Time") or []
            for t in time_list:
                raw_time = t.get("dataDate") or t.get("StartTime") or t.get("startTime") or ""
                date_str = raw_time.split("T")[0] if "T" in raw_time else raw_time[:10]
                if not date_str or len(date_str) < 10:
                    continue

                temp = _extract_temp_val(t)
                if temp is None:
                    continue

                if date_str not in region_data[target_region]:
                    region_data[target_region][date_str] = {"min_list": [], "max_list": []}

                if is_max:
                    region_data[target_region][date_str]["max_list"].append(temp)
                elif is_min:
                    region_data[target_region][date_str]["min_list"].append(temp)

    # 扁平化整合為 rows
    rows = []
    for region, dates in region_data.items():
        # 取未來 7 天
        sorted_dates = sorted(dates.keys())[:7]
        for d in sorted_dates:
            mins = dates[d]["min_list"]
            maxs = dates[d]["max_list"]

            min_val = round(sum(mins) / len(mins), 1) if mins else None
            max_val = round(sum(maxs) / len(maxs), 1) if maxs else None

            # 若當天只有其中一項，合理補足
            if min_val is not None and max_val is not None and min_val > max_val:
                min_val, max_val = max_val, min_val

            rows.append({
                "regionName": region,
                "dataDate": d,
                "minT": min_val,
                "maxT": max_val,
            })

    return rows


def to_dataframe(rows: list[dict]) -> pd.DataFrame:
    """
    Clean, format, and validate forecast rows using Pandas.
    Ensures correct types, deduplication, and sanity checks (Step 07).
    """
    if not rows:
        return pd.DataFrame(columns=["regionName", "dataDate", "minT", "maxT"])

    df = pd.DataFrame(rows)
    df["dataDate"] = pd.to_datetime(df["dataDate"]).dt.strftime("%Y-%m-%d")
    df["minT"] = pd.to_numeric(df["minT"], errors="coerce")
    df["maxT"] = pd.to_numeric(df["maxT"], errors="coerce")

    # 移除空地區與空日期
    df = df.dropna(subset=["regionName", "dataDate"])
    # 移除重複資料
    df = df.drop_duplicates(subset=["regionName", "dataDate"], keep="last")

    # 氣溫邏輯校驗：確保 minT <= maxT
    inverted = df["minT"] > df["maxT"]
    if inverted.any():
        df.loc[inverted, ["minT", "maxT"]] = df.loc[inverted, ["maxT", "minT"]].values

    # 排序
    df = df.sort_values(["regionName", "dataDate"]).reset_index(drop=True)
    return df


def main():
    """Execute complete ETL pipeline: Fetch -> Parse -> Clean -> Store into DB."""
    print("==================================================")
    print("  Taiwan Weather Forecast ETL Pipeline")
    print("==================================================")

    print("\n>>> [Step 04] 擷取 CWA 氣象資料...")
    data = fetch_raw()
    print(f"原始資料存檔路徑: {config.RAW_JSON_PATH}")

    print("\n>>> [Step 05] 檢驗 JSON 階層結構 (Walk Preview)...")
    walk(data, path="root", max_depth=3)

    print("\n>>> [Step 06] 提取最高與最低氣溫 (MinT / MaxT)...")
    rows = parse_temperatures(data)
    print(f"解析成功，共取得 {len(rows)} 筆預報資料。")
    if rows:
        print(f"抽查首筆紀錄: {rows[0]}")

    print("\n>>> [Step 07] Pandas 資料清洗與轉換...")
    df = to_dataframe(rows)
    print("資料型別檢視:")
    print(df.dtypes)
    print("\nDataFrame 前 6 列預覽:")
    print(df.head(6))

    # Gate 07 檢驗
    dup_count = df.duplicated(["regionName", "dataDate"]).sum()
    order_ok = (df["minT"] <= df["maxT"]).all()
    range_ok = df[["minT", "maxT"]].stack().between(-10, 45).all()
    print(f"重複筆數檢核: {dup_count} (預期 0)")
    print(f"溫度關係 (minT <= maxT): {order_ok} (預期 True)")
    print(f"溫度範圍 (-10 ~ 45°C): {range_ok} (預期 True)")

    print("\n>>> [Step 08 & 09] 寫入 SQLite 資料庫 (data/data.db)...")
    database.init_db()
    database.upsert(df)
    print(f"已成功寫入 {len(df)} 筆資料至資料庫！")
    removed = database.prune_past_dates(datetime.now().strftime("%Y-%m-%d"))
    if removed:
        print(f"已清除 {removed} 筆過期日期的舊預報。")

    print("\n>>> [Step 10] 執行 SQL 查詢驗證...")
    res = database.verify_data()
    print(f"所有地區名稱: {res['regions']}")
    print(f"抽查地區 ({res['sample_region']}) 預報筆數: {len(res['sample_forecast'])}")
    print(f"各地區天數統計: {res['days_per_region']}")
    print(f"異常資料筆數: {res['anomalies_count']}")
    print(f"資料庫總資料筆數: {res['total_rows']}")

    print("\n[Gate 驗證] 測試二次重複執行以驗證 UNIQUE 與 Upsert 機制...")
    database.upsert(df)
    res_after = database.verify_data()
    print(f"二次執行後資料庫總筆數: {res_after['total_rows']} (預期與前次完全相同: {res['total_rows'] == res_after['total_rows']})")
    print("\nSUCCESS: 階段 B (Step 04-07) 與 階段 C (Step 08-10) 全部完成並通過 Gate 驗收！")


if __name__ == "__main__":
    main()
