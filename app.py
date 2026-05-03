import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import fastf1
import requests
from icalendar import Calendar
import json

# --- 設定 ---
JST = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(JST)
start_window = now_jst - timedelta(hours=6)
end_window = now_jst + timedelta(days=30)

st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️", layout="centered")

# --- スタイル ---
st.markdown("""
<style>
.session-card {
    padding: 12px; margin-bottom: 8px; border-radius: 6px;
    background-color: #1E1E1E; border-left: 5px solid #FFFFFF;
}
.f1-card { border-left-color: #FF1801; }
.f2-card { border-left-color: #0090D0; }
.fb-card { border-left-color: #00C853; }

.session-name { font-size: 15px; font-weight: bold; color: #FAFAFA; }
.time-jst { color: #FF4B4B; font-weight: bold; font-size: 15px; }
.time-local { color: #BBBBBB; font-size: 13px; }
.event-title {
    background: #262730; padding: 8px 12px;
    border-radius: 5px; margin-top: 15px; font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- ICS取得 ---
@st.cache_data(ttl=3600)
def load_ics_events(url, team):
    events = []
    try:
        r = requests.get(url, timeout=10)
        cal = Calendar.from_ical(r.text)

        for comp in cal.walk():
            if comp.name == "VEVENT":
                dt = comp.get("dtstart").dt

                # タイムゾーン処理
                if dt.tzinfo:
                    local_time = dt
                else:
                    local_time = pytz.utc.localize(dt)

                jst_time = local_time.astimezone(JST)

                events.append({
                    "team": team,
                    "opp": str(comp.get("summary")),
                    "jst": jst_time,
                    "local": local_time
                })
    except:
        pass

    return events

# --- fallback ---
def load_fallback():
    try:
        with open("soccer_fallback.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            events = []
            for d in data:
                jst_time = datetime.fromisoformat(d["time"])
                local = jst_time.astimezone(pytz.timezone(d["venue_tz"]))

                events.append({
                    "team": d["team"],
                    "opp": d["opp"],
                    "jst": jst_time,
                    "local": local
                })
            return events
    except:
        return []

# --- サッカー統合 ---
@st.cache_data(ttl=3600)
def get_soccer_events():
    ICS_SOURCES = [
        {"team": "名古屋グランパス", "url": "https://example.com/nagoya.ics"},
        {"team": "レアル・ソシエダ", "url": "https://example.com/sociedad.ics"},
        {"team": "日本代表", "url": "https://example.com/japan.ics"},
        {"team": "U23日本代表", "url": "https://example.com/u23.ics"},
    ]

    all_events = []
    for src in ICS_SOURCES:
        all_events += load_ics_events(src["url"], src["team"])

    if not all_events:
        all_events = load_fallback()

    return all_events

# --- F1 ---
@st.cache_data(ttl=3600)
def get_f1():
    return fastf1.get_event_schedule(now_jst.year)

# --- UI ---
st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Now: **{now_jst.strftime('%m/%d %H:%M')} JST**")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1", "🏁 F2"])

# --- サッカー ---
with tab_fb:
    events = get_soccer_events()

    filtered = [e for e in events if start_window <= e["jst"] <= end_window]

    if filtered:
        for e in sorted(filtered, key=lambda x: x["jst"]):
            st.markdown(f"""
            <div class="session-card fb-card">
                <div class="session-name">【{e['team']}】 vs {e['opp']}</div>
                <div class="time-jst">🇯🇵 {e['jst'].strftime('%m/%d %H:%M')} JST</div>
                <div class="time-local">🌍 {e['local'].strftime('%m/%d %H:%M %Z')}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("直近30日間の試合予定なし")

# --- F1 ---
with tab_f1:
    events = get_f1()
    if not events.empty:
        for _, e in events.iterrows():
            race_time = e['Session5DateUtc']
            if pd.notna(race_time):
                jst_time = race_time.replace(tzinfo=pytz.UTC).astimezone(JST)

                if start_window <= jst_time <= end_window:
                    st.markdown(f"""
                    <div class="session-card f1-card">
                        <div class="session-name">{e['EventName']} - Race</div>
                        <div class="time-jst">🇯🇵 {jst_time.strftime('%m/%d %H:%M')}</div>
                    </div>
                    """, unsafe_allow_html=True)

# --- F2タブ ---
with tab_f2:
    if not events.empty:
        found_f2 = False
        for _, event in events.iterrows():
            f2_sessions = [('F2 Practice', 'Session1DateUtc'), ('F2 Qualifying', 'Session2DateUtc'), ('F2 Sprint', 'Session3DateUtc'), ('F2 Feature', 'Session5DateUtc')]
            display_f2 = []
            for n, k in f2_sessions:
                if k in event and pd.notna(event[k]):
                    t = event[k].replace(tzinfo=pytz.UTC).astimezone(JST)
                    if start_window <= t <= end_window: display_f2.append((n, t))
            
            if display_f2:
                found_f2 = True
                st.markdown(f"<div class='event-title'>🏁 {event['EventName']} (F2)</div>", unsafe_allow_html=True)
                cols = st.columns(len(display_f2))
                for i, (n, t) in enumerate(display_f2):
                    with cols[i]:
                        st.markdown(f"<div class='session-card f2-card'><div class='session-name'>{n}</div><div class='time-jst'>{t.strftime('%m/%d %H:%M')}</div></div>", unsafe_allow_html=True)
        if not found_f2: st.write("直近のF2予定はありません。")
