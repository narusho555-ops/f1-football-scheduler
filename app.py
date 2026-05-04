import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import fastf1
import requests

# --- 1. 設定 ---
API_KEY = "42b577d5380e44d38221b7d4986521ca"
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
    .fb-card { border-left-color: #4CAF50; }
    .session-name { font-size: 15px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 16px; }
    .event-title { background: #262730; padding: 8px 12px; border-radius: 5px; margin-top: 15px; font-weight: bold; color: #EEE; }
    .link-button { 
        display: block; width: 100%; padding: 10px; margin: 5px 0; 
        text-align: center; background-color: #31333F; color: white; 
        text-decoration: none; border-radius: 8px; border: 1px solid #4B4B4B;
        font-weight: bold; font-size: 14px;
    }
    .link-button:hover { background-color: #FF4B4B; border-color: #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. データ取得ロジック ---

@st.cache_data(ttl=3600)
def get_racing_events(year):
    try:
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def get_fb_matches(team_id):
    url = f"https://api.football-data.org/v4/teams/{team_id}/matches?status=SCHEDULED"
    headers = {'X-Auth-Token': API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('matches', [])
    except:
        pass
    return []

# --- 3. メイン表示 ---
st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Standard: **{now_jst.strftime('%m/%d %H:%M')}** JST")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1 Schedule", "🏁 F2 Schedule"])

# --- サッカータブ：API ＋ リンク集 ---
with tab_fb:
    st.subheader("Upcoming Matches (API)")
    
    # チームID設定: ソシエダ(92), 日本代表(773)
    teams = [("Real Sociedad", 92), ("Japan", 773)]
    found_any_match = False
    
    for team_name, team_id in teams:
        matches = get_fb_matches(team_id)
        for m in matches:
            # UTC文字列をdatetimeに変換しJSTへ
            utc_time = datetime.strptime(m['utcDate'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=pytz.UTC)
            jst_time = utc_time.astimezone(JST)
            
            if start_window <= jst_time <= end_window:
                found_any_match = True
                home = m['homeTeam']['shortName']
                away = m['awayTeam']['shortName']
                st.markdown(f"""
                <div class="session-card fb-card">
                    <div class="session-name">🏆 {team_name}: {home} vs {away}</div>
                    <div class="time-jst">🇯🇵 {jst_time.strftime('%m/%d %H:%M')} JST</div>
                </div>
                """, unsafe_allow_html=True)
                
    if not found_any_match:
        st.info("直近30日間にAPI取得可能な試合はありません。")

    st.markdown("---")
    st.subheader("Official Quick Links")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<a href="https://nagoya-grampus.jp/game/schedule/" target="_blank" class="link-button">名古屋</a>', unsafe_allow_html=True)
    with col2:
        st.markdown('<a href="https://www.realsociedad.eus/es/equipo/partidos/real-sociedad" target="_blank" class="link-button">Sociedad</a>', unsafe_allow_html=True)
    with col3:
        st.markdown('<a href="https://www.jfa.jp/samuraiblue/schedule_result/2026.html" target="_blank" class="link-button">日本代表</a>', unsafe_allow_html=True)

# --- F1/F2 データ取得 ---
events = get_racing_events(now_jst.year)

# --- F1タブ ---
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
