import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="SFX ELITE OS", layout="wide", initial_sidebar_state="expanded")

conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        df = conn.read(ttl="0")
        if df.empty or 'Date' not in df.columns:
            return pd.DataFrame(columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])
        return df
    except:
        return pd.DataFrame(columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])

def save_data(df):
    conn.update(data=df)
    st.cache_data.clear()

trades_df = load_data()
if not trades_df.empty:
    trades_df['Date'] = pd.to_datetime(trades_df['Date']).dt.date
    trades_df['PNL'] = pd.to_numeric(trades_df['PNL'], errors='coerce').fillna(0)
    # חישוב לוגיקה לדאשבורד בלבד
    trades_df['Real_PNL'] = trades_df.apply(lambda r: -abs(r['PNL']) if r['Outcome'] == 'Loss' else (abs(r['PNL']) if r['Outcome'] == 'Win' else 0), axis=1)

# --- 2. STATE MANAGEMENT (הבסיס המקורי) ---
main_nav = ["Dashboard", "Trade Log", "Analytics", "Account Settings"]
if 'page' not in st.session_state: st.session_state.page = "Dashboard"
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year

# --- 3. PREMIUM UI / CSS (פי 10 יותר יפה) ---
accent = "#34d399" 
loss_color = "#f87171" 
bg_color = "#0B0E14" 
panel_color = "#151A23" 
border_color = "#1E293B"

st.markdown(f"""
    <style>
    /* רקע כללי */
    .stApp {{ background-color: {bg_color}; color: #E2E8F0; font-family: 'Inter', sans-serif; }}
    
    /* כותרות */
    h1, h2, h3 {{ color: #FFFFFF !important; font-weight: 800 !important; }}
    .main-header {{ font-size: 2.5rem; font-weight: 900; background: -webkit-linear-gradient(45deg, {accent}, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }}
    
    /* קוביות מדדים */
    div[data-testid="stMetric"] {{ 
        background-color: {panel_color}; 
        border: 1px solid {border_color}; 
        border-radius: 16px; 
        padding: 20px; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.4); 
    }}
    div[data-testid="stMetricValue"] {{ font-size: 2.2rem !important; color: #FFFFFF !important; }}
    
    /* לוח שנה */
    .cal-card {{ padding: 12px; border-radius: 12px; margin-bottom: 10px; text-align: center; min-height: 90px; font-size: 0.9rem; font-weight: 700; transition: transform 0.2s ease; }}
    .cal-card:hover {{ transform: translateY(-3px); }}
    .cal-win {{ background-color: rgba(52, 211, 153, 0.05); border: 1px solid {accent}; color: {accent}; box-shadow: 0 0 15px rgba(52, 211, 153, 0.1); }}
    .cal-loss {{ background-color: rgba(248, 113, 113, 0.05); border: 1px solid {loss_color}; color: {loss_color}; box-shadow: 0 0 15px rgba(248, 113, 113, 0.1); }}
    .cal-neutral {{ background-color: {panel_color}; border: 1px solid {border_color}; color: #64748B; }}
    
    /* טבלאות */
    .stDataFrame {{ border-radius: 12px; overflow: hidden; border: 1px solid {border_color}; }}
    
    /* כפתורים */
    .stButton>button {{ background-color: {panel_color}; border: 1px solid {border_color}; border-radius: 8px; color: #FFFFFF; font-weight: 600; padding: 10px 20px; border-color: transparent; }}
    .stButton>button:hover {{ border-color: {accent}; color: {accent}; }}
    
    /* סרגל צד */
    [data-testid="stSidebar"] {{ background-color: {panel_color}; border-right: 1px solid {border_color}; }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; font-size: 2rem; color:{accent}; margin-bottom: 30px;'>SFX ELITE OS</h1>", unsafe_allow_html=True)
    
    # ניווט קשיח ובטוח ללא באגים
    for nav_item in main_nav:
        if st.button(f"{nav_item}", use_container_width=True):
            st.session_state.page = nav_item
            st.rerun()

    st.write("---")
    
    # בחירת חשבון ישירות בסרגל
    if not trades_df.empty:
        available_accounts = trades_df['Account'].unique().tolist()
        if 'active_account' not in st.session_state and available_accounts:
            st.session_state.active_account = available_accounts[0]
            
        if available_accounts:
            idx = available_accounts.index(st.session_state.active_account) if st.session_state.active_account in available_accounts else 0
            st.session_state.active_account = st.selectbox("Active Account", available_accounts, index=idx)
        else:
            st.session_state.active_account = "LUCIDFLEX 25K"
    else:
        st.session_state.active_account = "LUCIDFLEX 25K"

acc_trades = trades_df[trades_df['Account'] == st.session_state.active_account].copy() if not trades_df.empty else pd.DataFrame()

# --- 5. PAGES ---

if st.session_state.page == "Dashboard":
    st.markdown(f"<p class='main-header'>Dashboard: {st.session_state.active_account}</p>", unsafe_allow_html=True)
    
    if acc_trades.empty:
        st.info("No trades logged for this account yet. Go to Trade Log to start.")
    else:
        total = len(acc_trades)
        wins = len(acc_trades[acc_trades['Outcome'] == 'Win'])
        net_pnl = acc_trades['Real_PNL'].sum()
        win_rate = (wins/total*100) if total > 0 else 0
        avg_risk = acc_trades['Risk_Percent'].mean() if total > 0 else 0
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Win Rate", f"{win_rate:.1f}%")
        m2.metric("Net PNL", f"${net_pnl:,.2f}")
        m3.metric("Avg Risk", f"{avg_risk:.2f}%")
        m4.metric("Total Trades", total)
        
        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("📅 Trading Calendar")
        c1, c2, c3 = st.columns([8, 1, 1])
        with c1: st.markdown(f"<h3 style='color:#94A3B8;'>{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h3>", unsafe_allow_html=True)
        if c2.button("◀"): 
            st.session_state.cal_month = 12 if st.session_state.cal_month == 1 else st.session_state.cal_month - 1
            st.session_state.cal_year = st.session_state.cal_year - 1 if st.session_state.cal_month == 12 else st.session_state.cal_year
            st.rerun()
        if c3.button("▶"): 
            st.session_state.cal_month = 1 if st.session_state.cal_month == 12 else st.session_state.cal_month + 1
            st.session_state.cal_year = st.session_state.cal_year + 1 if st.session_state.cal_month == 1 else st.session_state.cal_year
            st.rerun()

        cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
        cols = st.columns(7)
        days_labels = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for i, d_n in enumerate(days_labels): 
            cols[i].markdown(f"<p style='text-align:center; color:#64748B; font-weight:bold; font-size:0.85rem;'>{d_n}</p>", unsafe_allow_html=True)
        
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    curr_date = date(st.session_state.cal_year, st.session_state.cal_month, day)
                    day_trades = acc_trades[acc_trades['Date'] == curr_date]
                    if not day_trades.empty:
                        day_pnl = day_trades['Real_PNL'].sum()
                        cls = "cal-win" if day_pnl >= 0 else "cal-loss"
                        cols[i].markdown(f'<div class="cal-card {cls}">{day}<br><span style="font-size:1.1rem">${day_pnl:,.0f}</span></div>', unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f'<div class="cal-card cal-neutral">{day}</div>', unsafe_allow_html=True)

elif st.session_state.page == "Trade Log":
    st.markdown("<p class='main-header'>Trade Log</p>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown(f"<h3 style='color:{accent}'>➕ Execute New Log</h3>", unsafe_allow_html=True)
        with st.form("new_trade_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            acc_name = c1.text_input("Account", value=st.session_state.active_account)
            d = c1.date_input("Date", date.today())
            pair = c1.selectbox("Pair", ["NQ", "ES", "BTC", "ETH"])
            
            side = c2.radio("Side", ["Long", "Short"], horizontal=True)
            risk_p = c2.number_input("Risk %", value=1.0, step=0.1)
            rr = c2.number_input("Reward/Risk (RR)", value=0.0, step=0.1)
            
            out = c3.selectbox("Outcome", ["Win", "Loss", "BE"])
            pnl = c3.number_input("PNL ($)", value=0.0, step=10.0)
            poi = st.multiselect("POI / Setup", ["IFVG", "FVG", "MSS", "SMT", "LQ Sweep", "OB", "AMD"])
            
            submit = st.form_submit_button("🔥 PUSH TO CLOUD", use_container_width=True)
            if submit:
                new_row = pd.DataFrame([[d, acc_name, pair, side, rr, ", ".join(poi), out, pnl, risk_p]], 
                                     columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])
                
                clean_df = trades_df.drop(columns=['Real_PNL'], errors='ignore')
                updated_df = pd.concat([clean_df, new_row], ignore_index=True)
                save_data(updated_df)
                st.success("Trade securely logged to Google Sheets!")
                st.rerun()

    st.write("---")
    st.subheader("Recent Execution History")
    if not trades_df.empty:
        view_df = trades_df.sort_values(by='Date', ascending=False).drop(columns=['Real_PNL'], errors='ignore')
        st.dataframe(view_df, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Delete Last Trade Entry", use_container_width=False):
            clean_df = trades_df.drop(columns=['Real_PNL'], errors='ignore')
            save_data(clean_df[:-1])
            st.rerun()
    else:
        st.info("No trades logged yet.")

elif st.session_state.page == "Analytics":
    st.markdown("<p class='main-header'>Performance Analytics</p>", unsafe_allow_html=True)
    if acc_trades.empty:
        st.info("Not enough data to analyze for this account.")
    else:
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown(f"<div style='background:{panel_color}; padding:20px; border-radius:12px; border:1px solid {border_color};'>", unsafe_allow_html=True)
            st.subheader("🎯 Setup (POI) Performance")
            poi_df = acc_trades.assign(POI=acc_trades['POI'].str.split(', ')).explode('POI')
            poi_stats = poi_df.groupby('POI').agg(Trades=('Outcome', 'count'), Net_PNL=('Real_PNL', 'sum'))
            st.dataframe(poi_stats.sort_values(by='Net_PNL', ascending=False), use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"<div style='background:{panel_color}; padding:20px; border-radius:12px; border:1px solid {border_color};'>", unsafe_allow_html=True)
            st.subheader("⚖️ Long vs Short")
            side_stats = acc_trades.groupby('Side').agg(Trades=('Outcome', 'count'), Net_PNL=('Real_PNL', 'sum'))
            st.dataframe(side_stats, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "Account Settings":
    st.markdown("<p class='main-header'>Account Settings</p>", unsafe_allow_html=True)
    st.info("Your active account is selected in the Sidebar.")
    
    st.subheader("Create / Manage Accounts")
    st.write("To add a new account, simply go to the **Trade Log**, type a new name in the 'Account' field, and save a trade. The system will automatically register the new account and it will appear in the sidebar.")
