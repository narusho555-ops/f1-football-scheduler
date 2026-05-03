import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import fastf1
import urllib.request
import re

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

# --- 2. ロジック：サッカー日程（正規表現でHTML解析 - lxml不要） ---
@st.cache_data(ttl=3600)
def get_soccer_schedule_regex():
    all_matches = []
    #######################################
    # ここにグランパスのアドレスを明確に打ち込む！
    #######################################
    url = "https://soccer.yahoo.co.jp/jleague/category/j1/teams/127/info?gk=2"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
        
        # HTMLのテーブル行を強引に抽出
        rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL)
        for row in rows:
            try:
                cells = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 4:
                    date_text = re.sub(r'<.*?>', '', cells[0]).strip() # 5/3(日)
                    time_text = re.sub(r'<.*?>', '', cells[1]).strip() # 17:00
                    opp_text = re.sub(r'<.*?>', '', cells[3]).strip()  # 相手チーム名
                    
                    if '/' in date_text and ':' in time_text:
                        m = int(date_text.split('/')[0])
                        d = int(date_text.split('/')[1].split('(')[0])
                        h = int(time_text.split(':')[0])
                        mn = int(time_text.split(':')[1])
                        
                        match_time = JST.localize(datetime(2026, m, d, h, mn))
                        all_matches.append({"team": "名古屋", "opp": opp_text, "time": match_time})
            except: continue
    except: pass
    return all_matches

# --- 3. ロジック：F1/F2日程 ---
@st.cache_data(ttl=3600)
def get_racing_events(year):
    try:
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

# --- 4. メイン表示 ---
st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Standard: **{now_jst.strftime('%m/%d %H:%M')}** JST")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1", "🏁 F2"])

# --- サッカータブ ---
with tab_fb:
    st.subheader("Web Sync: Nagoya Grampus")
    matches = get_soccer_schedule_regex()
    if matches:
        # 重複を排除して表示
        unique_matches = { (m['time'], m['opp']): m for m in matches }.values()
        found_fb = False
        for m in sorted(unique_matches, key=lambda x: x['time']):
            if start_window <= m['time'] <= end_window:
                found_fb = True
                st.markdown(f"""
                    <div class="session-card">
                        <div class="session-name">【{m['team']}】 vs {m['opp']}</div>
                        <span class="time-jst">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</span>
                    </div>
                """, unsafe_allow_html=True)
        if not found_fb: st.info("直近30日間の試合予定はありません。")
    else:
        st.error("サッカー日程の解析に失敗しました。URLまたはHTML構造を確認してください。")

# --- F1/F2 共通データ取得 ---
events = get_racing_events(now_jst.year)

# --- F1タブ ---
with tab_f1:
    if not events.empty:
        # 過去3日〜未来のイベントを表示
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
