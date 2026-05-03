import streamlit as st
from datetime import datetime, timedelta
import pytz

# --- 設定 ---
st.set_page_config(page_title="Paddock & Pitch Schedule", page_icon="🏎️", layout="centered")

# カスタムCSSでデザインを調整（文字サイズなど）
st.markdown("""
    <style>
    .big-font { font-size:20px !important; font-weight: bold; }
    .local-time { color: #888; font-size: 14px; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("🏎️⚽ Paddock & Pitch")
st.caption("F1/F2/Football 直近スケジュール（日本時間・現地時間）")

# 時間軸の設定（現在からマイナス6時間〜1ヶ月）
JST = pytz.timezone('Asia/Tokyo')
now = datetime.now(JST)
start_window = now - timedelta(hours=6)
end_window = now + timedelta(days=30)

# --- タブ分けでスッキリ見せる ---
tab1, tab2, tab3 = st.tabs(["🏎️ F1", "🏁 F2", "⚽ Football"])

with tab1:
    st.subheader("F1 Session Schedule")
    # ここにFastF1等の取得ロジックを入れる
    # デザイン例:
    st.info("🇦🇺 オーストラリアGP (Melbourne)")
    col1, col2 = st.columns(2)
    with col1:
        st.write("🏁 **Race (JST)**")
        st.write("03/22 13:00")
    with col2:
        st.write("📍 **Local**")
        st.write("03/22 15:00")

with tab3:
    st.subheader("Target Teams Matches")
    # 名古屋グランパス、ソシエダ、日本代表の表示
    teams = {
        "名古屋グランパス": "🇯🇵 J1 League",
        "レアル・ソシエダ": "🇪🇸 La Liga",
        "男子日本代表": "🌏 International",
        "U23日本代表": "🌏 U23"
    }
    
    for team, category in teams.items():
        with st.expander(f"{team} ({category})", expanded=True):
            # サンプルの表示形式
            st.markdown(f'<p class="big-font">vs 対戦相手チーム名</p>', unsafe_allow_stdio=True)
            st.write(f"📅 **{(now + timedelta(days=2)).strftime('%m/%d %H:%M')} JST**")
            st.markdown(f'<p class="local-time">📍 現地時間: 03/24 21:00</p>', unsafe_allow_stdio=True)
