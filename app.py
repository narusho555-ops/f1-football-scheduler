import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import fastf1
import os
import urllib.request

# --- 1. 設定 ---
JST = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(JST)
start_window = now_jst - timedelta(hours=12)
end_window = now_jst + timedelta(days=30)

st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️", layout="centered")

# デザイン設定
st.markdown("""
    <style>
    .session-card { padding: 12px; margin-bottom: 8px; border-radius: 4px; background-color: #1E1E1E; border-left: 5px solid #FFFFFF; }
    .f1-card { border-left-color: #FF1801; }
    .f2-card { border-left-color: #0090D0; }
    .session-name { font-size: 15px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 16px; }
    .event-title { background: #262730; padding: 8px 12px; border-radius: 5px; margin-top: 15px; font-weight: bold; color: #EEE; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ロジック：サッカー日程（Webスクレイピング） ---
@st.cache_data(ttl=3600)
def get_web_soccer_schedule():
    all_matches = []
    # ユーザーエージェントを設定してアクセス拒否を回避
    url = "https://soccer.yahoo.co.jp/jleague/teams/schedule/95"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read()
        tables = pd.read_html(html)
        df = tables[0]
        
        for _, row in df.iterrows():
            try:
                date_part = str(row[0]) # "5/3（日）"
                time_part = str(row[1]) # "17:00"
                opp = str(row[3])       # "長崎"
                
                m = int(date_part.split('/')[0])
                d = int(date_part.split('/')[1].split('（')[0])
                h = int(time_part.split(':')[0])
                mn = int(time_part.split(':')[1])
                
                match_time = JST.localize(datetime(2026, m, d, h, mn))
                all_matches.append({"team": "名古屋", "opp": opp, "time": match_time})
            except: continue
    except: pass
    return all_matches

# --- 3. ロジック：F1/F2 (FastF1) ---
@st.cache_data(ttl=3600)
def get_racing_events(year):
    try:
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

# --- 4. メイン表示エリア ---
st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Standard: **{now_jst.strftime('%m/%d %H:%M')}** JST")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1", "🏁 F2"])

# Soccer Tab
with tab_fb:
    st.subheader("Web Sync: Nagoya Grampus")
    matches = get_web_soccer_schedule()
    if matches:
        found = False
        for m in matches:
            if start_window <= m['time'] <= end_window:
                found = True
                st.markdown(f"""<div class="session-card"><div class="session-name">【{m['team']}】 vs {m['opp']}</div>
                    <span class="time-jst">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</span></div>""", unsafe_allow_html=True)
        if not found: st.info("表示期間内の試合はありません。")
    else:
        st.error("Webデータの取得に失敗しました。")

# F1 Tab
events = get_racing_events(now_jst.year)
with tab_f1:
    if not events.empty:
        upcoming_f1 = events[events['EventDate'] >= (now_jst.replace(tzinfo=None) - timedelta(days=3))]
        for _, event in upcoming_f1.iterrows():
            sessions = [('FP1', 'Session1DateUtc'), ('Qualifying', 'Session4DateUtc'), ('Sprint', 'Session3DateUtc'), ('Race', 'Session5DateUtc')]
            display = []
            for n, k in sessions:
                if k in event and pd.notna(event[k]):
                    t = event[k].replace(tzinfo=pytz.UTC).astimezone(JST)
                    if start_window <= t <= end_window: display.append((n, t))
            if display:
                st.markdown(f"<div class='event-title'>🏎️ {event['EventName']}</div>", unsafe_allow_html=True)
                cols = st.columns(len(display))
                for i, (n, t) in enumerate(display):
                    with cols[i]:
                        st.markdown(f"<div class='session-card f1-card'><div class='session-name'>{n}</div><div class='time-jst'>{t.strftime('%m/%d %H:%M')}</div></div>", unsafe_allow_html=True)

# F2 Tab
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
        if not found_f2: st.write("直近のF2予定なし")
