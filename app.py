"""
Taiwan Weather Forecast - Streamlit Web Dashboard
Displays regional 7-day temperature trends and interactive geospatial map.
Uses CWA API data stored in SQLite database.
"""

import os
import sqlite3
import pandas as pd
import altair as alt
import folium
import branca.colormap as cm
import streamlit as st
from streamlit_folium import st_folium
import config

# 頁面基本設定
st.set_page_config(
    page_title="Taiwan Weather Forecast | 台灣天氣預報",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 台灣 6 大分區座標中心點
REGION_COORDS = {
    "北部地區": (25.03, 121.52),
    "東北部地區": (24.70, 121.75),
    "中部地區": (24.15, 120.68),
    "東部地區": (23.98, 121.60),
    "南部地區": (22.90, 120.35),
    "東南部地區": (22.75, 121.15),
}


def temp_color(avg: float) -> str:
    """Return color string according to 4-tier temperature scale (Step 17)."""
    if avg < 20:
        return "#2e86de"  # 藍色 (< 20°C)
    elif avg < 25:
        return "#2ecc71"  # 綠色 (20–25°C)
    elif avg < 30:
        return "#f39c12"  # 橘色 (25–30°C)
    else:
        return "#e74c3c"  # 紅色 (> 30°C)


def temp_color_name(avg: float) -> str:
    """Return Folium marker color name."""
    if avg < 20:
        return "blue"
    elif avg < 25:
        return "green"
    elif avg < 30:
        return "orange"
    else:
        return "red"


@st.cache_data(ttl=600)
def load_data() -> tuple[pd.DataFrame, str | None]:
    """
    Load forecast records and latest update timestamp from SQLite database (Step 12).
    """
    if not os.path.exists(config.DB_PATH):
        return pd.DataFrame(), None

    try:
        with sqlite3.connect(config.DB_PATH) as conn:
            # Check if table exists
            table_check = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='TemperatureForecasts'"
            ).fetchone()
            if not table_check:
                return pd.DataFrame(), None

            df = pd.read_sql_query(
                "SELECT regionName, dataDate, minT, maxT, created_at "
                "FROM TemperatureForecasts ORDER BY regionName, dataDate",
                conn,
            )

            last_updated = None
            if not df.empty and "created_at" in df.columns:
                last_updated = df["created_at"].max()

            return df, last_updated
    except Exception as e:
        st.error(f"資料庫讀取失敗: {e}")
        return pd.DataFrame(), None


def build_map(day_df: pd.DataFrame) -> folium.Map:
    """
    Build interactive Folium map centered on Taiwan with temperature markers (Step 17 & 18).
    """
    m = folium.Map(
        location=[23.7, 121.0],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # 繪製各分區圓形標記
    for _, r in day_df.iterrows():
        region_name = r["regionName"]
        coords = REGION_COORDS.get(region_name)
        if not coords:
            continue

        min_t = r["minT"]
        max_t = r["maxT"]
        avg_t = round((min_t + max_t) / 2, 1)
        hex_color = temp_color(avg_t)

        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 13px; line-height: 1.5; min-width: 140px;">
            <b style="font-size: 15px; color: #2c3e50;">{region_name}</b><br>
            <hr style="margin: 5px 0; border: none; border-top: 1px solid #ddd;">
            <span style="color: #e74c3c;">▲ 最高溫: <b>{max_t}°C</b></span><br>
            <span style="color: #2980b9;">▼ 最低溫: <b>{min_t}°C</b></span><br>
            <span style="color: #7f8c8d;">● 平均溫: <b>{avg_t}°C</b></span>
        </div>
        """

        tooltip_text = f"{region_name} | {avg_t}°C (低: {min_t}°C / 高: {max_t}°C)"

        folium.CircleMarker(
            location=coords,
            radius=16,
            color="#ffffff",
            weight=2,
            fill=True,
            fill_color=hex_color,
            fill_opacity=0.85,
            tooltip=tooltip_text,
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(m)

        # 在圓形中央標記平均溫度文字
        folium.Marker(
            location=coords,
            icon=folium.DivIcon(
                html=f"""<div style="font-size: 11px; font-weight: bold; color: #ffffff;
                         text-align: center; line-height: 32px; transform: translate(-50%, -50%);
                         text-shadow: 1px 1px 2px rgba(0,0,0,0.6);">{avg_t:.0f}°</div>"""
            ),
        ).add_to(m)

    return m


def main():
    # 頂部標題區塊 (Step 16)
    st.markdown(
        """
        <div style="padding: 10px 0 20px 0;">
            <h1 style="margin: 0; font-size: 2.2rem; color: #1e3799;">🌤️ Taiwan Weather Forecast — 台灣一週氣象儀表板</h1>
            <p style="margin-top: 6px; color: #57606f; font-size: 1.05rem;">
                資料來源：<b>交通部中央氣象署 (CWA Open Data)</b> ｜ 結合 SQLite 資料庫、Altair 趨勢圖與 Folium 地圖視覺化
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 讀取資料 (Step 12)
    df, last_updated = load_data()

    # 資料庫不存在或無資料時的友善提示
    if df.empty:
        st.warning("⚠️ 資料庫尚無氣象資料，請先在命令列執行資料擷取程式：")
        st.code("python fetch_cwa.py", language="bash")
        st.info("執行完成後重新整理此頁面即可檢視預報圖表與地圖。")
        return

    # 側邊欄控制與資訊
    with st.sidebar:
        st.header("⚙️ 儀表板控制台")
        st.markdown("---")
        if last_updated:
            st.caption(f"🕒 資料庫更新時間：`{last_updated}`")
        st.caption("📡 氣象資料集代碼：`F-D0047-091` / `F-A0010-001`")

        if st.button("🔄 重新載入最新資料", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎨 氣溫色標階層")
        st.markdown(
            """
            - 🔴 **高溫炎熱** (`> 30°C`)
            - 🟠 **溫暖舒適** (`25 - 30°C`)
            - 🟢 **涼爽宜人** (`20 - 25°C`)
            - 🔵 **偏冷低溫** (`< 20°C`)
            """
        )
        st.markdown("---")
        st.caption("AIot-HW1-CWA 專案實作成果")

    # 分頁配置 (Step 19 Taiwan Weather Dashboard)
    tab1, tab2 = st.tabs(["📊 地區氣溫預報 (Regional Forecast)", "🗺️ 全台氣溫地圖 (Taiwan Map)"])

    # -------------------------------------------------------------
    # Tab 1: 地區氣溫預報 (Step 13, 14, 15, 16)
    # -------------------------------------------------------------
    with tab1:
        regions = sorted(df["regionName"].unique())
        selected_region = st.selectbox(
            "📍 選擇預報地區 (Select Region)",
            regions,
            index=regions.index("中部地區") if "中部地區" in regions else 0,
            key="region_selector",
        )

        region_df = df[df["regionName"] == selected_region].sort_values("dataDate").copy()

        # 關鍵指標卡片
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("預報天數", f"{len(region_df)} 天")
        with col_m2:
            st.metric("一週最高溫", f"{region_df['maxT'].max():.1f} °C", delta="MaxT", delta_color="inverse")
        with col_m3:
            st.metric("一週最低溫", f"{region_df['minT'].min():.1f} °C", delta="MinT")
        with col_m4:
            avg_temp = (region_df["minT"].mean() + region_df["maxT"].mean()) / 2
            st.metric("平均預報氣溫", f"{avg_temp:.1f} °C")

        st.markdown("### 📈 一週氣溫趨勢變化 (Altair 折線圖)")
        
        # 繪製 Altair 折線圖 (Step 14)
        chart_df = region_df.melt(
            id_vars=["dataDate", "regionName"],
            value_vars=["maxT", "minT"],
            var_name="temp_type",
            value_name="temperature",
        )
        chart_df["類別"] = chart_df["temp_type"].map({"maxT": "最高氣溫 (MaxT)", "minT": "最低氣溫 (MinT)"})

        line_chart = (
            alt.Chart(chart_df)
            .mark_line(point=alt.OverlayMarkDef(filled=True, size=65))
            .encode(
                x=alt.X("dataDate:N", title="預報日期 (Date)", axis=alt.Axis(labelAngle=0)),
                y=alt.Y(
                    "temperature:Q",
                    title="氣溫 (°C)",
                    scale=alt.Scale(zero=False, padding=15),
                ),
                color=alt.Color(
                    "類別:N",
                    scale=alt.Scale(
                        domain=["最高氣溫 (MaxT)", "最低氣溫 (MinT)"],
                        range=["#e4572e", "#2e86de"],  # 紅色與藍色
                    ),
                    legend=alt.Legend(title="氣溫項目", orient="top"),
                ),
                tooltip=[
                    alt.Tooltip("regionName:N", title="地區"),
                    alt.Tooltip("dataDate:N", title="日期"),
                    alt.Tooltip("類別:N", title="類型"),
                    alt.Tooltip("temperature:Q", title="氣溫 (°C)", format=".1f"),
                ],
            )
            .properties(height=360)
            .interactive()
        )

        st.altair_chart(line_chart, use_container_width=True)

        st.markdown("### 📋 一週詳細預報數據表格 (Step 15)")
        # 顯示資料表格 (Step 15)
        display_table = region_df.rename(
            columns={"dataDate": "Date", "minT": "MinT (°C)", "maxT": "MaxT (°C)"}
        )[["Date", "MinT (°C)", "MaxT (°C)"]]
        
        st.dataframe(
            display_table,
            hide_index=True,
            use_container_width=True,
        )

    # -------------------------------------------------------------
    # Tab 2: 全台氣溫地圖 (Step 17, 18)
    # -------------------------------------------------------------
    with tab2:
        dates = sorted(df["dataDate"].unique())
        selected_date = st.selectbox("📅 選擇觀測日期 (Select Date)", dates, key="date_selector")
        day_df = df[df["dataDate"] == selected_date].copy()

        col_map, col_details = st.columns([3, 2])

        with col_map:
            st.markdown(f"#### 🗺️ {selected_date} 全台各地區氣溫地理標註")
            folium_map = build_map(day_df)
            st_folium(folium_map, height=520, use_container_width=True)

        with col_details:
            st.markdown(f"#### 📊 {selected_date} 各分區氣溫數值")
            day_summary = day_df[["regionName", "minT", "maxT"]].copy()
            day_summary["平均溫 (°C)"] = ((day_summary["minT"] + day_summary["maxT"]) / 2).round(1)
            day_summary = day_summary.rename(
                columns={"regionName": "地區", "minT": "最低溫 (°C)", "maxT": "最高溫 (°C)"}
            )

            st.dataframe(
                day_summary.sort_values("平均溫 (°C)", ascending=False),
                hide_index=True,
                use_container_width=True,
            )

            st.info(
                "💡 **操作說明**：\n"
                "- 點擊地圖上的彩色圓圈標記可展開分區詳細氣溫卡片。\n"
                "- 標記圓圈內的數字代表當日預報之日平均氣溫。\n"
                "- 切換上方日期即可動態觀察全台灣各分區之氣溫走勢與分佈變化。"
            )


if __name__ == "__main__":
    main()
