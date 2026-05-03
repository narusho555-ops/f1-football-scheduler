import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import fastf1

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
    .link-button { 
        display: block; width: 100%; padding: 15px; margin: 10px 0; 
        text-align: center; background-color: #31333F; color: white; 
        text-decoration: none; border-radius: 8px; border: 1px solid #4B4B4B;
        font-weight: bold; transition: 0.3s;
    }
    .link-button:hover { background-color: #FF4B4B; border-color: #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. F1/F2 ロジック ---
@st.cache_data(ttl=3600)
def get_racing_events(year):
    try:
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

# --- 3. メイン表示 ---
st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Standard: **{now_jst.strftime('%m/%d %H:%M')}** JST")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football Links", "🏎️ F1 Schedule", "🏁 F2 Schedule"])

# --- サッカータブ：公式リンク集 ---
with tab_fb:
    st.subheader("Official Match Schedules")
    st.write("最新の試合日程・結果は公式サイトでチェック！")
    
    # 名古屋グランパス
    st.markdown('<a href="https://nagoya-grampus.jp/game/schedule/" target="_blank" class="link-button">🔥 名古屋グランパス 公式日程</a>', unsafe_allow_html=True)
    
    # レアル・ソシエダ（日本語版または公式）
    st.markdown('<a href="https://www.realsociedad.eus/es/equipo/partidos/real-sociedad" target="_blank" class="link-button">🇪🇸 レアル・ソシエダ 公式日程</a>', unsafe_allow_html=True)
    
    # 日本代表（JFA公式）
    st.markdown('<a href="https://www.jfa.jp/samuraiblue/schedule_result/2026.html" target="_blank" class="link-button">🇯🇵 日本代表 (SAMURAI BLUE)</a>', unsafe_allow_html=True)
    
    st.info("※ブラウザの別タブで開きます。")

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
