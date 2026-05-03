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
    .reportview-container { background: #0e1117; }
    .session-card {
        padding: 12px;
        border-left: 5px solid #FF1801;
        background-color: #1E1E1E;
        margin-bottom: 8px;
        border-radius: 4px;
    }
    .session-name { font-size: 16px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 15px; }
    .time-local { color: #888; font-size: 13px; }
    .event-title { background: #262730; padding: 5px 10px; border-radius: 5px; margin-top: 15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Now: **{now_jst.strftime('%m/%d %H:%M')}** JST")

# --- 4. ロジック：F1/F2 スケジュール取得 ---
@st.cache_data(ttl=3600)
def get_f1_events(year):
    try:
        schedule = fastf1.get_event_schedule(year)
        # 必要な列だけ抽出し、フィルタリング
        # セッションごとの時間はUTCなのでJSTに変換が必要
        return schedule
    except:
        return pd.DataFrame()

# --- 5. メイン表示エリア ---
tab1, tab2, tab3 = st.tabs(["🏎️ F1 / F2", "⚽ Football", "⚙️ Status"])

# F1 / F2 ブロック
with tab1:
    events = get_f1_events(now_jst.year)
    if not events.empty:
        # 直近1ヶ月のイベントを抽出
        upcoming_events = events[(events['EventDate'] >= start_window.replace(tzinfo=None)) & 
                                 (events['EventDate'] <= end_window.replace(tzinfo=None))]
        
        if upcoming_events.empty:
            st.write("直近1ヶ月のレース予定はありません。")
        else:
            for _, event in upcoming_events.iterrows():
                st.markdown(f"<div class='event-title'>🚩 {event['EventName']} ({event['Location']})</div>", unsafe_allow_html=True)
                
                # 主要セッションのリスト
                sessions = [
                    ('FP1', 'Session1DateUtc'),
                    ('Qualifying', 'Session4DateUtc'),
                    ('Race', 'Session5DateUtc')
                ]
                
                cols = st.columns(len(sessions))
                for i, (s_name, s_key) in enumerate(sessions):
                    if s_key in event and pd.notna(event[s_key]):
                        utc_time = event[s_key].replace(tzinfo=pytz.UTC)
                        jst_time = utc_time.astimezone(JST)
                        
                        # 表示期間内のセッションのみ出力
                        if start_window <= jst_time <= end_window:
                            with cols[i]:
                                st.markdown(f"""
                                    <div class="session-card">
                                        <div class="session-name">{s_name}</div>
                                        <div class="time-jst">{jst_time.strftime('%m/%d %H:%M')}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
    else:
        st.error("F1スケジュールが取得できませんでした。")

# サッカーブロック
with tab3:
    st.subheader("Target Teams Matches")
    # ここは今後、football-data.org などのAPIを追加する部分です
    # 現状はフィルタリングが機能しているか確認するためのサンプルを表示
    st.caption("※サッカーの自動取得ロジックは次のステップで実装します")
    
    teams_data = [
        {"team": "名古屋グランパス", "opp": "横浜F・マリノス", "time": now_jst + timedelta(days=3), "tz": "Asia/Tokyo"},
        {"team": "レアル・ソシエダ", "opp": "Barcelona", "time": now_jst + timedelta(days=7), "tz": "Europe/Madrid"},
        {"team": "男子日本代表", "opp": "TBD", "time": now_jst + timedelta(days=14), "tz": "Asia/Tokyo"},
    ]

    for m in teams_data:
        local_time = m['time'].astimezone(pytz.timezone(m['tz']))
        st.markdown(f"""
            <div class="session-card">
                <div class="session-name">{m['team']} vs {m['opp']}</div>
                <span class="time-jst">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</span><br>
                <span class="time-local">📍 Local: {local_time.strftime('%m/%d %H:%M')}</span>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    st.info("F2のスケジュールはFastF1のサポート状況に応じて自動表示されます。")
