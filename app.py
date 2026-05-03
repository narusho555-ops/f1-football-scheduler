import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import fastf1
import os

# --- 1. 設定 ---
JST = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(JST)
start_window = now_jst - timedelta(hours=12)
end_window = now_jst + timedelta(days=30)

st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️", layout="centered")

# CSSスタイル（成瀬さんの好みのデザインを維持）
st.markdown("""
    <style>
    .session-card { padding: 12px; margin-bottom: 8px; border-radius: 4px; background-color: #1E1E1E; border-left: 5px solid #FFFFFF; }
    .f1-card { border-left-color: #FF1801; }
    .f2-card { border-left-color: #0090D0; }
    .session-name { font-size: 15px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. Webから直接データを「抜く」関数 ---
@st.cache_data(ttl=3600)
def get_web_soccer_schedule():
    """
    特定のスポーツサイトの日程表ページ（HTMLのtableタグ）を
    Pandasで直接読み込んで解析します。
    """
    all_matches = []
    
    # 名古屋グランパスの日程ページ（一例としてYahoo!スポーツのチームID: 95）
    try:
        # read_htmlはページ内のテーブルをすべてリストとして取得します
        url = "https://soccer.yahoo.co.jp/jleague/teams/schedule/95"
        tables = pd.read_html(url)
        df = tables[0] # 通常、最初の日程テーブルを取得
        
        # テーブルの各行をループして試合情報を抽出
        for _, row in df.iterrows():
            try:
                # サイトの構造に合わせて列（日時、対戦相手）を抽出
                # ※ここは実際のサイトの列名に合わせて調整されます
                date_str = str(row[0]) # 例: "5/3（日）"
                time_str = str(row[1]) # 例: "17:00"
                opponent = str(row[3]) # 対戦相手
                
                # 日時文字列をdatetimeに変換するロジック（簡易版）
                month = int(date_str.split('/')[0])
                day = int(date_str.split('/')[1].split('（')[0])
                hour = int(time_str.split(':')[0])
                minute = int(time_str.split(':')[1])
                
                match_time = JST.localize(datetime(2026, month, day, hour, minute))
                all_matches.append({"team": "名古屋", "opp": opponent, "time": match_time})
            except:
                continue
    except Exception as e:
        # Web取得に失敗した際の最低限の表示（またはエラーログ）
        pass

    return all_matches

# --- 3. メイン表示 ---
st.title("🏎️⚽ Paddock & Pitch")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football (Web Auto)", "🏎️ F1", "🏁 F2"])

with tab_fb:
    st.subheader("Detected Web Schedule")
    # ここで実際にWebサイトの表を読みに行きます
    with st.spinner('Fetching latest match data...'):
        matches = get_web_soccer_schedule()
    
    if matches:
        for m in matches:
            if start_window <= m['time'] <= end_window:
                st.markdown(f"""
                    <div class="session-card">
                        <div class="session-name">【{m['team']}】 vs {m['opp']}</div>
                        <span class="time-jst">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</span>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("Webから試合日程を取得できませんでした。サイト構成を確認してください。")

# --- F1/F2 Tab ---
# (F1/F2のロジックは正常に動いているため維持)
with tab_f1:
    events = get_racing_events(now_jst.year)
    if not events.empty:
        upcoming_f1 = events[events['EventDate'] >= (now_jst.replace(tzinfo=None) - timedelta(days=2))]
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
