import streamlit as st
import feedparser
import re
from datetime import datetime
import pytz
import fastf1
import os
import pandas as pd

# --- 1. 設定 ---
JST = pytz.timezone('Asia/Tokyo')
now = datetime.now(JST)

st.set_page_config(page_title="Paddock & Pitch", page_icon="🏎️")

# --- 2. RSSから試合日程を抽出する関数 ---
@st.cache_data(ttl=1800)
def get_auto_soccer_schedule():
    # サッカー関連の複数のRSSを利用
    rss_urls = [
        "https://news.yahoo.co.jp/rss/topics/soccer.xml",
        "https://news.yahoo.co.jp/rss/categories/sports.xml"
    ]
    
    targets = ["名古屋", "グランパス", "ソシエダ", "日本代表"]
    matches = []
    
    for url in rss_urls:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title
            # 対象チームが含まれているか確認
            if any(t in title for t in targets):
                # タイトルから日時（例: 5/3 17:00）を正規表現で探す
                time_match = re.search(r'(\d{1,2})/(\d{1,2}).*?(\d{1,2}):(\d{2})', title)
                
                if time_match:
                    month, day, hour, minute = map(int, time_match.groups())
                    # 今年の日付としてdatetimeオブジェクトを作成
                    match_time = JST.localize(datetime(now.year, month, day, hour, minute))
                    
                    # 重複を避けてリストに追加
                    match_info = {
                        "display": title,
                        "time": match_time,
                        "link": entry.link
                    }
                    if match_info not in matches:
                        matches.append(match_info)
    
    # 時間順に並び替え
    return sorted(matches, key=lambda x: x['time'])

# --- 3. UI表示 ---
st.title("🏎️⚽ Paddock & Pitch (Full Auto)")

tab_fb, tab_f1, tab_f2 = st.tabs(["⚽ Football (RSS Auto)", "🏎️ F1", "🏁 F2"])

with tab_fb:
    st.subheader("Auto-Detected from RSS")
    auto_matches = get_auto_soccer_schedule()
    
    if auto_matches:
        for m in auto_matches:
            # 未来の試合または直近の試合のみ表示
            if m['time'] > now - pd.Timedelta(hours=3):
                with st.container():
                    st.markdown(f"""
                    <div style="padding:10px; border-left:5px solid #FFF; background:#1E1E1E; margin-bottom:10px;">
                        <div style="font-size:14px; font-weight:bold;">{m['display']}</div>
                        <div style="color:#FF4B4B; font-weight:bold;">🕒 {m['time'].strftime('%m/%d %H:%M')} JST</div>
                        <a href="{m['link']}" style="font-size:12px; color:#888;">Source Link</a>
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.write("現在、RSSから自動抽出できる試合情報は見つかりませんでした。")

# --- 4. F1 / F2 ロジック (FastF1を使用) ---
@st.cache_data(ttl=3600)
def get_f1_data():
    return fastf1.get_event_schedule(now.year)

events = get_f1_data()

with tab_f1:
    # 以前のF1表示ロジック（FastF1から自動取得）をここに維持
    st.info("F1日程はFastF1ライブラリから自動取得しています。")
    # ... (省略: 以前のF1描画コード)

with tab_f2:
    # 以前のF2表示ロジックをここに維持
    st.info("F2日程はFastF1ライブラリから自動取得しています。")
    # ... (省略: 以前のF2描画コード)
