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
start_window = now_jst - timedelta(hours=6)
end_window = now_jst + timedelta(days=30)

# --- 3. UI設定 & デザイン ---
st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️", layout="centered")

st.markdown("""
    <style>
    .session-card {
        padding: 12px;
        border-left: 5px solid #FF1801;
        background-color: #1E1E1E;
        margin-bottom: 8px;
        border-radius: 4px;
    }
    .f2-card { border-left: 5px solid #0090D0; } /* F2は青 */
    .fb-card { border-left: 5px solid #FFD700; } /* サッカーはゴールド */
    
    .session-name { font-size: 14px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 15px; }
    .event-title { 
        background: #262730; padding: 8px 12px; border-radius: 5px; 
        margin-top: 20px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Standard: **{now_jst.strftime('%m/%d %H:%M')}** JST")

# --- 4. ロジック：F1/F2 スケジュール取得 ---
@st.cache_data(ttl=3600)
def get_racing_events(year):
    try:
        # FastF1でF1/F2両方のスケジュールが含まれるか確認
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

# --- 5. メイン表示エリア ---
tab1, tab2, tab3 = st.tabs(["🏎️ F1 / 🏁 F2", "⚽ Football", "⚙️ Status"])

with tab1:
    events = get_racing_events(now_jst.year)
    if not events.empty:
        # F1とF2を抽出
        upcoming_events = events[events['EventDate'] >= (start_window.replace(tzinfo=None) - timedelta(days=5))]
        
        for _, event in upcoming_events.iterrows():
            # セッション定義（F2はSprint/Feature Race等が含まれる）
            sessions = [
                ('F1 FP1', 'Session1DateUtc'),
                ('F1 Qualifying', 'Session4DateUtc'),
                ('F1 Sprint', 'Session3DateUtc'),
                ('F1 Race', 'Session5DateUtc'),
                ('F2 Qualifying', 'Session2DateUtc'), # F2の予選
                ('F2 Sprint', 'Session3DateUtc'),    # F2のスプリント
                ('F2 Feature', 'Session5DateUtc')     # F2のフィーチャーレース
            ]
            
            display_sessions = []
            for s_name, s_key in sessions:
                if s_key in event and pd.notna(event[s_key]):
                    jst_time = event[s_key].replace(tzinfo=pytz.UTC).astimezone(JST)
                    if start_window <= jst_time <= end_window:
                        display_sessions.append((s_name, jst_time))
            
            if display_sessions:
                # F2が含まれる場合はタイトルを変える
                is_f2 = any("F2" in s[0] for s in display_sessions)
                color_class = "f2-card" if is_f2 else ""
                
                st.markdown(f"<div class='event-title'>🚩 {event['EventName']}</div>", unsafe_allow_html=True)
                cols = st.columns(len(display_sessions))
                for i, (name, time) in enumerate(display_sessions):
                    with cols[i]:
                        st.markdown(f"""
                            <div class="session-card {color_class}">
                                <div class="session-name">{name}</div>
                                <div class="time-jst">{time.strftime('%m/%d %H:%M')}</div>
                            </div>
                            """, unsafe_allow_html=True)

with tab2:
    st.subheader("Football Real Schedule")
    # 【成瀬さん専用】現在の正しい日程を反映
    # 今後はここをAPI自動取得に差し替えます
    real_matches = [
        {"team": "名古屋グランパス", "opp": "ヴィッセル神戸", "time": JST.localize(datetime(2026, 5, 3, 19, 0)), "tz": "Asia/Tokyo"},
        {"team": "名古屋グランパス", "opp": "サンフレッチェ広島", "time": JST.localize(datetime(2026, 5, 6, 15, 0)), "tz": "Asia/Tokyo"},
        {"team": "レアル・ソシエダ", "opp": "Las Palmas", "time": JST.localize(datetime(2026, 5, 5, 4, 0)), "tz": "Europe/Madrid"},
    ]

    for m in real_matches:
        if start_window <= m['time'] <= end_window:
            local_time = m['time'].astimezone(pytz.timezone(m['tz']))
            st.markdown(f"""
                <div class="session-card fb-card">
                    <div class="session-name">{m['team']} vs {m['opp']}</div>
                    <span class="time-jst">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</span><br>
                    <span class="time-local">📍 Local: {local_time.strftime('%m/%d %H:%M')}</span>
                </div>
                """, unsafe_allow_html=True)

with tab3:
    st.write("### Filter Status")
    st.write(f"Window Start: {start_window.strftime('%Y-%m-%d %H:%M')}")
    st.write("F1/F2 data source: FastF1")
    st.write("Football source: Manual Overwrite (API pending)")
