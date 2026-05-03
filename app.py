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
start_window = now_jst - timedelta(hours=6)
end_window = now_jst + timedelta(days=30)

# --- 3. UI設定 & デザイン ---
st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️", layout="centered")

st.markdown("""
    <style>
    .session-card {
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 4px;
        background-color: #1E1E1E;
    }
    .fb-card { border-left: 5px solid #FFFFFF; } /* サッカー：白 */
    .f1-card { border-left: 5px solid #FF1801; } /* F1：赤 */
    .f2-card { border-left: 5px solid #0090D0; } /* F2：青 */
    
    .session-name { font-size: 14px; font-weight: bold; color: #FAFAFA; }
    .time-jst { color: #FF4B4B; font-weight: bold; font-size: 15px; }
    .time-local { color: #888; font-size: 12px; }
    .rss-info { font-size: 11px; color: #aaa; margin-top: 4px; }
    .event-title { 
        background: #262730; padding: 8px 12px; border-radius: 5px; 
        margin-top: 15px; font-weight: bold; color: #EEE;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏎️⚽ Paddock & Pitch")
st.write(f"Last Update: **{now_jst.strftime('%m/%d %H:%M')}** JST")

# --- 4. ロジック：データ取得 ---

@st.cache_data(ttl=3600)
def get_racing_events(year):
    try:
        return fastf1.get_event_schedule(year)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=1800)
def get_soccer_updates():
    """RSSから最新ニュースと試合情報を抽出"""
    feeds = [
        "https://news.yahoo.co.jp/rss/topics/soccer.xml",
        "https://news.yahoo.co.jp/rss/categories/sports.xml"
    ]
    targets = ["名古屋", "グランパス", "ソシエダ", "日本代表"]
    updates = []
    
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries:
                if any(t in entry.title for t in targets):
                    updates.append({"title": entry.title, "link": entry.link})
        except:
            continue
    return updates

# --- 5. メイン表示エリア ---
tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football", "🏎️ F1", "🏁 F2"])

# --- Soccer Tab ---
with tab_fb:
    st.subheader("Target Teams Schedule & News")
    
    # A. 確定スケジュール（バックアップ用：RSS解析が完璧でない場合に備える）
    real_matches = [
        {"team": "名古屋グランパス", "opp": "ヴィッセル神戸", "time": JST.localize(datetime(2026, 5, 3, 19, 0)), "tz": "Asia/Tokyo"},
        {"team": "名古屋グランパス", "opp": "サンフレッチェ広島", "time": JST.localize(datetime(2026, 5, 6, 15, 0)), "tz": "Asia/Tokyo"},
        {"team": "レアル・ソシエダ", "opp": "Las Palmas", "time": JST.localize(datetime(2026, 5, 5, 4, 0)), "tz": "Europe/Madrid"},
        {"team": "レアル・ソシエダ", "opp": "Barcelona", "time": JST.localize(datetime(2026, 5, 14, 4, 0)), "tz": "Europe/Madrid"},
        {"team": "男子日本代表", "opp": "TBD", "time": JST.localize(datetime(2026, 6, 1, 19, 0)), "tz": "Asia/Tokyo"},
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

    # B. RSSからの最新トピック表示
    rss_news = get_soccer_updates()
    if rss_news:
        st.write("---")
        st.caption("Latest Topics from RSS")
        for news in rss_news[:5]: # 最新5件を表示
            st.markdown(f"🔹 [{news['title']}]({news['link']})")

# --- F1 Tab ---
with tab_f1:
    events = get_racing_events(now_jst.year)
    if not events.empty:
        upcoming_f1 = events[events['EventDate'] >= (now_jst.replace(tzinfo=None) - timedelta(days=3))]
        for _, event in upcoming_f1.iterrows():
            sessions = [
                ('FP1', 'Session1DateUtc'), ('Qualifying', 'Session4DateUtc'),
                ('Sprint', 'Session3DateUtc'), ('Race', 'Session5DateUtc'),
            ]
            display_sessions = []
            for s_name, s_key in sessions:
                if s_key in event and pd.notna(event[s_key]):
                    jst_time = event[s_key].replace(tzinfo=pytz.UTC).astimezone(JST)
                    if start_window <= jst_time <= end_window:
                        display_sessions.append((s_name, jst_time))
            
            if display_sessions:
                st.markdown(f"<div class='event-title'>🏎️ {event['EventName']}</div>", unsafe_allow_html=True)
                cols = st.columns(len(display_sessions))
                for i, (name, time) in enumerate(display_sessions):
                    with cols[i]:
                        st.markdown(f"""
                            <div class="session-card f1-card">
                                <div class="session-name">{name}</div>
                                <div class="time-jst">{time.strftime('%m/%d %H:%M')}</div>
                            </div>
                            """, unsafe_allow_html=True)

# --- F2 Tab ---
with tab_f2:
    if not events.empty:
        found_f2 = False
        for _, event in events.iterrows():
            f2_sessions = [
                ('F2 Practice', 'Session1DateUtc'), ('F2 Qualifying', 'Session2DateUtc'),
                ('F2 Sprint', 'Session3DateUtc'), ('F2 Feature', 'Session5DateUtc')
            ]
            display_f2 = []
            for s_name, s_key in f2_sessions:
                if s_key in event and pd.notna(event[s_key]):
                    jst_time = event[s_key].replace(tzinfo=pytz.UTC).astimezone(JST)
                    if start_window <= jst_time <= end_window:
                        display_f2.append((s_name, jst_time))
            
            if display_f2:
                found_f2 = True
                st.markdown(f"<div class='event-title'>🏁 {event['EventName']} (F2)</div>", unsafe_allow_html=True)
                cols = st.columns(len(display_f2))
                for i, (name, time) in enumerate(display_f2):
                    with cols[i]:
                        st.markdown(f"""
                            <div class="session-card f2-card">
                                <div class="session-name">{name}</div>
                                <div class="time-jst">{time.strftime('%m/%d %H:%M')}</div>
                            </div>
                            """, unsafe_allow_html=True)
        if not found_f2:
            st.write("直近のF2セッションはありません。")
