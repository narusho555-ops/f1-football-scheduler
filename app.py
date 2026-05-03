import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz
import fastf1
import urllib.request
import re # 正規表現を使用

# --- 1. 設定 ---
JST = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(JST)
start_window = now_jst - timedelta(hours=12)
end_window = now_jst + timedelta(days=30)

st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️")

# --- 2. サッカー日程取得（lxmlに依存しない正規表現解析） ---
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
        
        # HTMLから「日付」「時間」「対戦相手」を抽出するための強引な解析
        # サイトのHTML構造（<td>など）に合わせたパターンマッチ
        # 注意：サイト構成に極めて依存しますが、lxmlエラーは回避できます
        
        # 簡易的にテーブルの行を分割
        rows = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL)
        
        for row in rows:
            try:
                # <td>内のテキストを抽出
                cells = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                if len(cells) >= 4:
                    # タグを除去してテキストのみにする
                    date_str = re.sub(r'<.*?>', '', cells[0]).strip() # "5/3(日)"
                    time_str = re.sub(r'<.*?>', '', cells[1]).strip() # "17:00"
                    opp = re.sub(r'<.*?>', '', cells[3]).strip()      # "長崎"
                    
                    if '/' in date_str and ':' in time_str:
                        m = int(date_str.split('/')[0])
                        d = int(date_str.split('/')[1].split('(')[0])
                        h = int(time_str.split(':')[0])
                        mn = int(time_str.split(':')[1])
                        
                        match_time = JST.localize(datetime(2026, m, d, h, mn))
                        all_matches.append({"team": "名古屋", "opp": opp, "time": match_time})
            except: continue
            
    except Exception as e:
        st.error(f"Regex Error: {e}")
        
    return all_matches

# --- 3. UI表示 ---
st.title("🏎️⚽ Paddock & Pitch")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1", "🏁 F2"])

with tab_fb:
    st.subheader("Web Sync (No-lxml Mode)")
    matches = get_soccer_schedule_regex()
    
    if matches:
        # 重複削除
        unique_matches = { (m['time'], m['opp']): m for m in matches }.values()
        for m in sorted(unique_matches, key=lambda x: x['time']):
            if start_window <= m['time'] <= end_window:
                st.markdown(f"""
                <div style="padding:12px; margin-bottom:8px; border-radius:4px; background-color:#1E1E1E; border-left:5px solid #FFF;">
                    <div style="font-size:15px; font-weight:bold; color:#FAFAFA;">【{m['team']}】 vs {m['opp']}</div>
                    <div style="color:#FF4B4B; font-weight:bold; font-size:16px;">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("解析可能な試合データが見つかりませんでした。")

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
