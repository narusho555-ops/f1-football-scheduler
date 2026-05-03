import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import requests
from icalendar import Calendar
import fastf1
import os
import fastf1

CACHE_DIR = "cache"

if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

fastf1.Cache.enable_cache(CACHE_DIR)
# -----------------------------
# 基本設定
# -----------------------------
JST = pytz.timezone("Asia/Tokyo")
now_jst = datetime.now(JST)

# 表示ウィンドウ
start_window = now_jst - timedelta(hours=6)
end_window = now_jst + timedelta(days=30)

# FastF1キャッシュ（安定化）
fastf1.Cache.enable_cache("cache")

st.set_page_config(
    page_title="Paddock & Pitch",
    page_icon="🏎️",
    layout="centered"
)

# -----------------------------
# UIスタイル
# -----------------------------
st.markdown("""
<style>
.card {
    padding: 12px;
    margin-bottom: 10px;
    border-radius: 8px;
    background-color: #1E1E1E;
    border-left: 5px solid #00C853;
}
.f1 { border-left-color: #FF1801; }

.title {
    font-weight: bold;
    font-size: 15px;
    color: #FAFAFA;
}

.time-jst {
    color: #FF4B4B;
    font-weight: bold;
}

.time-local {
    color: #BBBBBB;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# ICS取得
# -----------------------------
@st.cache_data(ttl=3600)
def load_laliga():
    url = "https://www.webcal.fi/cal.php?id=la-liga&format=ics"
    events = []

    try:
        r = requests.get(url, timeout=10)
        cal = Calendar.from_ical(r.text)

        for comp in cal.walk():
            if comp.name == "VEVENT":
                summary = str(comp.get("summary"))

                # ★ レアル・ソシエダのみ抽出
                if "sociedad" not in summary.lower():
                    continue

                dt = comp.get("dtstart").dt

                if dt.tzinfo:
                    local_time = dt
                else:
                    local_time = pytz.utc.localize(dt)

                jst_time = local_time.astimezone(JST)

                events.append({
                    "title": summary,
                    "jst": jst_time,
                    "local": local_time
                })

    except Exception as e:
        st.error("La Liga ICS取得エラー")

    return events

# -----------------------------
# F1取得
# -----------------------------
@st.cache_data(ttl=3600)
def load_f1():
    return fastf1.get_event_schedule(now_jst.year)

# -----------------------------
# UI
# -----------------------------
st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Now: **{now_jst.strftime('%m/%d %H:%M')} JST**")

tab_soc, tab_f1 = st.tabs(["⚽ Real Sociedad", "🏎️ F1"])

# -----------------------------
# ソシエダ
# -----------------------------
with tab_soc:
    events = load_laliga()

    filtered = [e for e in events if start_window <= e["jst"] <= end_window]

    if filtered:
        for e in sorted(filtered, key=lambda x: x["jst"]):

            st.markdown(f"""
            <div class="card">
                <div class="title">⚽ {e['title']}</div>
                <div class="time-jst">🇯🇵 {e['jst'].strftime('%m/%d %H:%M')} JST</div>
                <div class="time-local">🌍 {e['local'].strftime('%m/%d %H:%M %Z')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("直近30日間の試合予定なし")

# -----------------------------
# F1
# -----------------------------
with tab_f1:
    events = load_f1()

    if not events.empty:
        for _, e in events.iterrows():
            race_time = e["Session5DateUtc"]

            if pd.notna(race_time):
                jst_time = race_time.replace(tzinfo=pytz.UTC).astimezone(JST)

                if start_window <= jst_time <= end_window:
                    st.markdown(f"""
                    <div class="card f1">
                        <div class="title">🏎️ {e['EventName']} - Race</div>
                        <div class="time-jst">🇯🇵 {jst_time.strftime('%m/%d %H:%M')} JST</div>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.error("F1データ取得失敗")
