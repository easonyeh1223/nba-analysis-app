import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import time
from nba_api.stats.static import players
from nba_api.stats.endpoints import playercareerstats, shotchartdetail

# --- 1. 網頁基本設定 ---
st.set_page_config(
    page_title="NBA Stats",
    page_icon="🏀",
    layout="wide"
)

# 設定畫圖風格
plt.style.use('ggplot')

# --- 2. 定義後端函數 ---
@st.cache_data
def get_player_id(name):
    all_players = players.get_players()
    for p in all_players:
        if p["full_name"].lower() == name.lower():
            return p["id"]
    return None

@st.cache_data
def get_career_data(pid):
    try:
        time.sleep(0.6)
        career = playercareerstats.PlayerCareerStats(player_id=pid, timeout=30)
        return career.get_data_frames()[0]
    except Exception as e:
        st.error(f"資料抓取失敗: {e}")
        return None

@st.cache_data
def get_shot_data(pid):
    try:
        time.sleep(0.6)
        shot = shotchartdetail.ShotChartDetail(
            player_id=pid,
            team_id=0,
            season_nullable='2023-24',
            context_measure_simple='FGA',
            timeout=30
        )
        return shot.get_data_frames()[0]
    except:
        return None

# --- 3. 側邊欄設計 ---
with st.sidebar:
    st.header("球員搜尋")
    st.write("請輸入 NBA 球員的英文全名")
    player_input = st.text_input("球員姓名", "Stephen Curry")
    if st.button("開始分析"):
        st.session_state['search_clicked'] = True

# --- 4. 主畫面邏輯 ---
st.title("NBA 球員表現數據視覺化系統")
st.markdown("### 進階程式設計期末專題報告 - 306 25 葉宇森")
st.markdown("---")

if st.session_state.get('search_clicked'):
    with st.spinner(f"正在連線 NBA 資料庫搜尋 {player_input} ..."):
        pid = get_player_id(player_input)
        
        if not pid:
            st.error(f"找不到球員：{player_input}，請確認拼字。")
        else:
            df_career = get_career_data(pid)
            
            if df_career is not None:
                st.success(f"成功取得 {player_input} 的數據！")
                
                # --- 第一區：關鍵數據儀表板 (Metrics) ---
                col1, col2, col3, col4 = st.columns(4)
                
                total_pts = df_career['PTS'].sum()
                total_gp = df_career['GP'].sum()
                total_ast = df_career['AST'].sum()
                
                # 修正：計算生涯場均得分 (PPG)
                if total_gp > 0:
                    career_ppg = round(total_pts / total_gp, 1)
                else:
                    career_ppg = 0
                
                col1.metric("生涯總得分", f"{total_pts:,}")
                col2.metric("生涯場均得分", career_ppg)  # 這裡修好了！
                col3.metric("總出賽場次", f"{total_gp:,}")
                col4.metric("生涯總助攻", f"{total_ast:,}")
                
                st.markdown("---")

                # --- 第二區：圖表切換 ---
                tab1, tab2, tab3 = st.tabs(["得分趨勢圖", "投籃熱點分析", "詳細數據表"])
                
                with tab1:
                    st.subheader(f"{player_input} 生涯得分變化")
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(df_career['SEASON_ID'], df_career['PTS'], marker='o', linewidth=2, color='#E03A3E')
                    ax.set_title("Career Points Trend", fontsize=15)
                    ax.set_ylabel("Total Points")
                    ax.set_xlabel("Season")
                    plt.xticks(rotation=45)
                    ax.grid(True, linestyle='--', alpha=0.5)
                    st.pyplot(fig)

                with tab2:
                    st.subheader(f"{player_input} (2023-24) 投籃熱點")
                    df_shot = get_shot_data(pid)
                    if df_shot is not None:
                        fig2, ax2 = plt.subplots(figsize=(8, 6))
                        made = df_shot[df_shot['SHOT_MADE_FLAG'] == 1]
                        missed = df_shot[df_shot['SHOT_MADE_FLAG'] == 0]
                        ax2.scatter(missed['LOC_X'], missed['LOC_Y'], c='#FF6B6B', alpha=0.3, s=10, label='Miss')
                        ax2.scatter(made['LOC_X'], made['LOC_Y'], c='#4ECDC4', alpha=0.3, s=10, label='Made')
                        ax2.set_title("Shot Chart Distribution", fontsize=15)
                        ax2.legend()
                        ax2.set_xticks([])
                        ax2.set_yticks([])
                        st.pyplot(fig2)
                    else:
                        st.warning("查無投籃資料。")

                with tab3:
                    st.dataframe(df_career)

else:
    st.info("👈 請在左側輸入球員名字並按下按鈕。")