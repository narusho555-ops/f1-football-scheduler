import streamlit as st
from datetime import datetime, timedelta
import pytz
import fastf1
import os
import pandas as pd

# --- 1. キャッシュ・環境設定 ---
CACHE_DIR = 'f1_cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

# --- 2. 時間軸の設定（日本時間基準） ---
JST = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(JST)

# 【重要】成瀬さんの要件：表示は「現在からマイナス6時間」から
start_window = now_jst - timedelta(hours=6)
end_window = now_jst + timedelta(days=30)

# --- 3. UI設定 & デザイン ---
st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️", layout="centered")

st.markdown("""
    <style>
    .session-card {
        padding: 10px;
        border-left: 5px solid #FF1801;
        background-color: #1E1E1E;
        margin-bottom: 5px;
        border-radius: 4px;
    }
    .session-name { font-size: 14px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 15px; }
    .time-local { color: #888; font-size: 12px; }
    .event-title { 
        background: #262730; 
        padding: 8px 12px; 
        border-radius: 5px; 
        margin-top: 20px; 
        border-bottom: 2px solid #FF1801;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Standard Time: **{now_jst.strftime('%m/%d %H:%M')}** JST")
st.caption(f"Showing schedules from {start_window.strftime('%m/%d %H:%M')} (Now -6h)")

# --- 4. ロジック：F1/F2 スケジュール取得 ---
@st.cache_data(ttl=3600)
def get_f1_events(year):
    try:
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

# --- 5. メイン表示エリア ---
tab1, tab2, tab3 = st.tabs(["🏎️ F1 / F2", "⚽ Football", "⚙️ Status"])

with tab1:
    events = get_f1_events(now_jst.year)
    if not events.empty:
        # イベント単位でのフィルタリング
        # セッションのいずれかが start_window 以降にあるイベントを抽出
        upcoming_events = events[events['EventDate'] >= (start_window.replace(tzinfo=None) - timedelta(days=3))]
        
        found_any = False
        for _, event in upcoming_events.iterrows():
            # 表示対象セッションの定義
            sessions = [
                ('FP1', 'Session1DateUtc'),
                ('Qualifying', 'Session4DateUtc'),
                ('Sprint', 'Session3DateUtc'),
                ('Race', 'Session5DateUtc')
            ]
            
            # このイベント内に表示対象のセッションがあるかチェック
            display_sessions = []
            for s_name, s_key in sessions:
                if s_key in event and pd.notna(event[s_key]):
                    jst_time = event[s_key].replace(tzinfo=pytz.UTC).astimezone(JST)
                    if start_window <= jst_time <= end_window:
                        display_sessions.append((s_name, jst_time))
            
            if display_sessions:
                found_any = True
                st.markdown(f"<div class='event-title'>🚩 {event['EventName']} ({event['Location']})</div>", unsafe_allow_html=True)
                cols = st.columns(len(display_sessions))
                for i, (name, time) in enumerate(display_sessions):
                    with cols[i]:
                        st.markdown(f"""
                            <div class="session-card">
                                <div class="session-name">{name}</div>
                                <div class="time-jst">{time.strftime('%m/%d %H:%M')}</div>
                            </div>
                            """, unsafe_allow_html=True)
        if not found_any:
            st.write("直近のレース予定はありません。")

with tab2:
    st.subheader("Target Teams Matches")
    # 名古屋グランパス(5/3 17:00)等を含むダミーデータ
    # ※ここは次のステップでAPI化します
    teams_data = [
        {"team": "名古屋グランパス", "opp": "横浜F・マリノス", "time": JST.localize(datetime(2026, 5, 3, 17, 0)), "tz": "Asia/Tokyo"},
        {"team": "名古屋グランパス", "opp": "次の相手", "time": JST.localize(datetime(2026, 5, 6, 13, 0)), "tz": "Asia/Tokyo"},
        {"team": "レアル・ソシエダ", "opp": "Barcelona", "time": now_jst + timedelta(days=7), "tz": "Europe/Madrid"},
    ]

    for m in teams_data:
        if start_window <= m['time'] <= end_window:
            local_time = m['time'].astimezone(pytz.timezone(m['tz']))
            st.markdown(f"""
                <div class="session-card">
                    <div class="session-name">{m['team']} vs {m['opp']}</div>
                    <span class="time-jst">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</span><br>
                    <span class="time-local">📍 Local: {local_time.strftime('%m/%d %H:%M')}</span>
                </div>
                """, unsafe_allow_html=True)

with tab3:
    st.write("### Debug Info")
    st.write(f"Filter Start: {start_window}")
    st.write(f"Filter End: {end_window}")
