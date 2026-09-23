"""
Configuration module for Taiwan Weather Forecast application.
Loads environment variables and sets common paths and constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

CWA_API_KEY = os.getenv("CWA_API_KEY")
# 依據實際 CWA Open Data 平台現行資料集：
# F-D0047-091 為現行一週天氣預報（涵蓋全台縣市，並自動整合為 6 大分區）
# 亦相容 F-A0010-001 或其他資料集
DATASET_ID = os.getenv("DATASET_ID", "F-D0047-091")
DB_PATH = str(BASE_DIR / "data" / "data.db")
RAW_JSON_PATH = str(BASE_DIR / "data" / "raw_cwa.json")
