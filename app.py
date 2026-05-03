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

st.set_page_config(page_title="Debug Mode: Paddock & Pitch", page_icon="🔧")

# --- 2. 【デバッグ版】サッカー日程取得ロジック ---
@st.cache_data(ttl=600)
def get_web_soccer_schedule_debug():
    debug_info = []
    all_matches = []
    url = "https://soccer.yahoo.co.jp/jleague/teams/schedule/95"
    
    try:
        debug_info.append(f"🔍 Accessing URL: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req) as response:
            html = response.read()
            debug_info.append("✅ HTML source retrieved successfully.")
        
        # HTML内に 'table' という文字列があるかチェック
        if b'<table' in html:
            debug_info.append("✅ Table tag found in HTML.")
        else:
            debug_info.append("❌ No table tag found in HTML source.")

        tables = pd.read_html(html)
        debug_info.append(f"✅ Found {len(tables)} tables on the page.")
        
        if len(tables) > 0:
            df = tables[0]
            debug_info.append(f"📊 Columns in Table 0: {list(df.columns)}")
            # 最初の1行をサンプル表示用に保持
            debug_info.append(f"📝 Sample Data (Row 0): {df.iloc[0].values.tolist()}")
            
            for _, row in df.iterrows():
                try:
                    # ここの列インデックスがサイト改修でズレている可能性アリ
                    date_part = str(row[0]) 
                    time_part = str(row[1]) 
                    opp = str(row[3])       
                    
                    m = int(date_part.split('/')[0])
                    d = int(date_part.split('/')[1].split('（')[0])
                    h = int(time_part.split(':')[0])
                    mn = int(time_part.split(':')[1])
                    
                    match_time = JST.localize(datetime(2026, m, d, h, mn))
                    all_matches.append({"team": "名古屋", "opp": opp, "time": match_time})
                except Exception as row_e:
                    continue
        else:
            debug_info.append("❌ Tables list is empty.")

    except Exception as e:
        debug_info.append(f"🔥 CRITICAL ERROR: {str(e)}")
    
    return all_matches, debug_info

# --- 3. メイン表示 ---
st.title("🔧 Paddock & Pitch (Debug Mode)")

# デバッグ情報の表示用エキスパンダー
with st.expander("🛠️ Debug Logs (エンジニア用ログ)"):
    matches, logs = get_web_soccer_schedule_debug()
    for log in logs:
        st.code(log)

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1", "🏁 F2"])

with tab_fb:
    if matches:
        for m in matches:
            if start_window <= m['time'] <= end_window:
                st.success(f"【{m['team']}】 vs {m['opp']} | 🕒 {m['time'].strftime('%m/%d %H:%M')}")
    else:
        st.error("試合日程を表示できません。上のDebug Logsを確認してください。")

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
