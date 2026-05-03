import streamlit as st
from datetime import datetime, timedelta
import pytz
import fastf1
import os
import pandas as pd
import feedparser

# --- 1. キャッシュ・環境設定 ---
CACHE_DIR = 'f1_cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)
fastf1.Cache.enable_cache(CACHE_DIR)

# --- 2. 時間軸の設定（日本時間基準） ---
JST = pytz.timezone('Asia/Tokyo')
now_jst = datetime.now(JST)
# 表示範囲：前後数日をしっかりカバー
start_window = now_jst - timedelta(hours=12)
end_window = now_jst + timedelta(days=21)

# --- 3. UI設定 & デザイン ---
st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️", layout="centered")

st.markdown("""
    <style>
    .session-card { padding: 12px; margin-bottom: 8px; border-radius: 4px; background-color: #1E1E1E; }
    .fb-card { border-left: 5px solid #FFFFFF; } 
    .f1-card { border-left: 5px solid #FF1801; } 
    .f2-card { border-left: 5px solid #0090D0; } 
    .session-name { font-size: 15px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 16px; }
    .event-title { background: #262730; padding: 8px 12px; border-radius: 5px; margin-top: 15px; font-weight: bold; color: #EEE; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Current Time: **{now_jst.strftime('%Y/%m/%d %H:%M')}** JST")

# --- 4. ロジック：データ取得 ---

@st.cache_data(ttl=3600)
def get_racing_events(year):
    try:
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_soccer_news():
    """RSSから最新トピックのみを取得"""
    feeds = ["https://news.yahoo.co.jp/rss/topics/soccer.xml"]
    targets = ["名古屋", "グランパス", "ソシエダ", "日本代表"]
    news_list = []
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries:
                if any(t in entry.title for t in targets):
                    news_list.append({"title": entry.title, "link": entry.link})
        except: continue
    return news_list

# --- 5. メイン表示エリア ---
tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1", "🏁 F2"])

with tab_fb:
    st.subheader("Match Schedule (Confirmed)")
    
    # 【重要】成瀬さんから頂いた正しい情報を反映
    # RSSは「ニュース」として使い、日程は確実なこのリストを優先します
    confirmed_matches = [
        {"team": "名古屋グランパス", "opp": "V・ファーレン長崎", "time": JST.localize(datetime(2026, 5, 3, 17, 0)), "tz": "Asia/Tokyo"},
        {"team": "名古屋グランパス", "opp": "ガンバ大阪", "time": JST.localize(datetime(2026, 5, 6, 14, 0)), "tz": "Asia/Tokyo"},
        {"team": "レアル・ソシエダ", "opp": "ラス・パルマス", "time": JST.localize(datetime(2026, 5, 5, 4, 0)), "tz": "Europe/Madrid"},
        {"team": "レアル・ソシエダ", "opp": "バルセロナ", "time": JST.localize(datetime(2026, 5, 14, 4, 0)), "tz": "Europe/Madrid"},
    ]

    for m in confirmed_matches:
        if start_window <= m['time'] <= end_window:
            st.markdown(f"""
                <div class="session-card fb-card">
                    <div class="session-name">{m['team']} vs {m['opp']}</div>
                    <span class="time-jst">🇯🇵 {m['time'].strftime('%m/%d %H:%M')} JST</span>
                </div>
                """, unsafe_allow_html=True)

    # RSSニュース
    st.markdown("---")
    st.caption("Latest Topics")
    for news in get_soccer_news()[:3]:
        st.markdown(f"🔹 [{news['title']}]({news['link']})")

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
