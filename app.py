import streamlit as st
import pandas as pd
import os
from datetime import datetime, date
import calendar

# --- הגדרות נתונים ---
DATA_DIR = 'data'
TRADES_FILE = os.path.join(DATA_DIR, 'trades.csv')
ACCOUNTS_FILE = os.path.join(DATA_DIR, 'accounts.json')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

st.set_page_config(page_title="SFX ELITE OS", layout="wide", initial_sidebar_state="expanded")

def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        try:
            return pd.read_json(ACCOUNTS_FILE, typ='series').to_dict()
        except: return {}
    return {}

def save_accounts(acc_dict):
    pd.Series(acc_dict).to_json(ACCOUNTS_FILE)

def load_trades():
    if os.path.exists(TRADES_FILE):
        df = pd.read_csv(TRADES_FILE)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        # וידוא שכל העמודות קיימות (כולל Risk_Percent החדש)
        for col in ['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent']:
            if col not in df.columns:
                df[col] = 0.0 if col in ['RR', 'PNL', 'Risk_Percent'] else ""
        return df
    return pd.DataFrame(columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])

accounts = load_accounts()
trades_df = load_trades()

# --- ניהול ניווט ---
main_nav = ["Dashboard", "Trade Log", "Analytics", "Account Settings"]
if 'page' not in st.session_state or st.session_state.page not in main_nav:
    st.session_state.page = "Dashboard"
if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year

# --- עיצוב CSS ---
accent = "#34d399" 
loss_color = "#f87171"
st.markdown(f"""
    <style>
    .stApp {{ background-color: #050505; color: #e2e8f0; }}
    div[data-testid="stMetric"] {{ background-color: #0d0d0d; border: 1px solid #1e1e1e; border-radius: 12px; padding: 15px; }}
    .cal-card {{ padding: 8px; border-radius: 8px; margin-bottom: 8px; text-align: center; min-height: 80px; border: 1px solid #1e1e1e; font-size: 0.8rem; }}
    .cal-win {{ background-color: rgba(52, 211, 153, 0.15); border: 1px solid {accent}; color: {accent}; }}
    .cal-loss {{ background-color: rgba(248, 113, 113, 0.15); border: 1px solid {loss_color}; color: {loss_color}; }}
    .main-header {{ font-size: 2.2rem; font-weight: 800; color: {accent}; margin-bottom: 20px; }}
    </style>
    """, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color:{accent}'>SFX ELITE</h1>", unsafe_allow_html=True)
    current_idx = main_nav.index(st.session_state.page) if st.session_state.page in main_nav else 0
    chosen = st.radio("Navigation", main_nav, index=current_idx)
    st.session_state.page = chosen

    if accounts:
        selected_acc = st.selectbox("Active Account", list(accounts.keys()))
        acc_info = accounts[selected_acc]
        acc_trades = trades_df[trades_df['Account'] == selected_acc].copy()
        acc_trades['Real_PNL'] = acc_trades.apply(lambda r: -abs(r['PNL']) if r['Outcome'] == 'Loss' else (abs(r['PNL']) if r['Outcome'] == 'Win' else 0), axis=1)
        
        net_pnl = acc_trades['Real_PNL'].sum()
        current_balance = acc_info['initial_balance'] + net_pnl
        st.metric("Balance", f"${current_balance:,.0f}", f"{net_pnl:,.0f}")
        
        if acc_info.get('type') == "Evaluation":
            progress = (net_pnl / acc_info['target']) if acc_info.get('target', 0) > 0 else 0
            st.write(f"🎯 Target: ${acc_info.get('target', 0):,}")
            st.progress(min(max(progress, 0.0), 1.0))
    else: selected_acc = None

# --- Dashboard ---
if st.session_state.page == "Dashboard":
    if not selected_acc:
        st.warning("Go to 'Account Settings' to create your first account.")
    else:
        st.markdown(f"<p class='main-header'>{selected_acc}</p>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        wins = len(acc_trades[acc_trades['Outcome'] == 'Win'])
        total = len(acc_trades)
        m1.metric("Win Rate", f"{(wins/total*100 if total>0 else 0):.1f}%")
        m2.metric("Net PNL", f"${net_pnl:,.2f}")
        m3.metric("Avg Risk %", f"{acc_trades['Risk_Percent'].mean():.2f}%" if total > 0 else "0%")
        m4.metric("Total Trades", total)

        st.write("---")
        # לוח שנה
        c1, c2, c3 = st.columns([6, 1, 1])
        with c1: st.subheader(f"📅 {calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}")
        if c2.button("⬅️"): st.session_state.cal_month = 12 if st.session_state.cal_month == 1 else st.session_state.cal_month - 1; st.rerun()
        if c3.button("➡️"): st.session_state.cal_month = 1 if st.session_state.cal_month == 12 else st.session_state.cal_month + 1; st.rerun()

        cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
        cols = st.columns(7)
        for i, d_n in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]): cols[i].markdown(f"<p style='text-align:center;'><b>{d_n}</b></p>", unsafe_allow_html=True)
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    curr_date = date(st.session_state.cal_year, st.session_state.cal_month, day)
                    day_pnl = acc_trades[acc_trades['Date'] == curr_date]['Real_PNL'].sum()
                    if any(acc_trades['Date'] == curr_date):
                        cls = "cal-win" if day_pnl >= 0 else "cal-loss"
                        cols[i].markdown(f'<div class="cal-card {cls}"><b>{day}</b><br>${day_pnl:,.0f}</div>', unsafe_allow_html=True)
                    else: cols[i].markdown(f'<div class="cal-card"><b>{day}</b></div>', unsafe_allow_html=True)

        # סיכום שבועי
        st.write("---")
        st.subheader("📈 Weekly Performance (Current Month)")
        acc_trades['Week'] = acc_trades.apply(lambda x: (x['Date'].day - 1) // 7 + 1 if x['Date'].month == st.session_state.cal_month else 0, axis=1)
        weekly_stats = acc_trades[acc_trades['Week'] > 0].groupby('Week')['Real_PNL'].sum()
        w_cols = st.columns(4)
        for i in range(1, 5):
            w_pnl = weekly_stats.get(i, 0)
            color = accent if w_pnl >= 0 else loss_color
            w_cols[i-1].markdown(f'<div style="border-left: 4px solid {color}; padding-left:10px; background:#0d0d0d; border-radius:5px;"><p style="margin:0; font-size:0.8rem; color:#888;">Week {i}</p><p style="margin:0; font-size:1.1rem; color:{color}; font-weight:bold;">${w_pnl:,.0f}</p></div>', unsafe_allow_html=True)

# --- Trade Log ---
elif st.session_state.page == "Trade Log":
    st.markdown("<p class='main-header'>📜 Trade Log</p>", unsafe_allow_html=True)
    if selected_acc:
        with st.expander("🔍 Filter Trades", expanded=False):
            f1, f2 = st.columns(2)
            pair_filter = f1.multiselect("Pair", options=["NQ", "ES"], default=["NQ", "ES"])
            outcome_filter = f2.multiselect("Outcome", options=acc_trades['Outcome'].unique(), default=acc_trades['Outcome'].unique())
            
        filtered_df = acc_trades[(acc_trades['Pair'].isin(pair_filter)) & (acc_trades['Outcome'].isin(outcome_filter))]

        if st.button("➕ LOG NEW TRADE"):
            st.session_state.log_mode = True
        
        if st.session_state.get('log_mode', False):
            with st.form("new_t_form"):
                c1, c2 = st.columns(2)
                d = c1.date_input("Date", date.today())
                pair = c1.selectbox("Pair", ["NQ", "ES"])
                side = c1.radio("Side", ["Long", "Short"], horizontal=True)
                risk_p = c2.number_input("Risk %", value=1.0, step=0.1)
                rr = c2.number_input("RR", value=0.0, step=0.1)
                out = c2.selectbox("Outcome", ["Win", "Loss", "BE"])
                pnl = c2.number_input("PNL ($)", min_value=0.0)
                poi = st.multiselect("POI", ["IFVG", "FVG", "MSS", "SMT", "LQ", "OB", "AMD"])
                if st.form_submit_button("SAVE"):
                    new_row = pd.DataFrame([[d, selected_acc, pair, side, rr, ", ".join(poi), out, pnl, risk_p]], 
                                         columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])
                    pd.concat([trades_df, new_row], ignore_index=True).to_csv(TRADES_FILE, index=False)
                    st.session_state.log_mode = False
                    st.rerun()
            if st.button("Cancel"):
                st.session_state.log_mode = False
                st.rerun()

        display_df = filtered_df.drop(columns=['Account', 'Real_PNL']).sort_values(by='Date', ascending=False)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.write("---")
        with st.expander("🗑️ Delete Trades"):
            if not display_df.empty:
                to_delete = st.multiselect("Select trades to remove", filtered_df.index, format_func=lambda x: f"{filtered_df.loc[x, 'Date']} | {filtered_df.loc[x, 'Pair']}")
                if st.button("❌ Confirm Delete Selected", type="primary"):
                    trades_df = trades_df.drop(to_delete)
                    trades_df.to_csv(TRADES_FILE, index=False)
                    st.rerun()

# --- Analytics ---
elif st.session_state.page == "Analytics":
    st.markdown("<p class='main-header'>📊 Analytics</p>", unsafe_allow_html=True)
    if not acc_trades.empty:
        st.subheader("POI Breakdown")
        poi_expanded = acc_trades.assign(POI=acc_trades['POI'].str.split(', ')).explode('POI')
        poi_stats = poi_expanded.groupby('POI').agg(Trades=('Outcome', 'count'), Wins=('Outcome', lambda x: (x == 'Win').sum()), PNL=('Real_PNL', 'sum'))
        poi_stats['Win Rate'] = (poi_stats['Wins'] / poi_stats['Trades'] * 100).map('{:.1f}%'.format)
        st.table(poi_stats[['Trades', 'Win Rate', 'PNL']].sort_values(by='PNL', ascending=False))
    else: st.info("No data yet.")

# --- Account Settings ---
elif st.session_state.page == "Account Settings":
    st.markdown("<p class='main-header'>⚙️ Settings</p>", unsafe_allow_html=True)
    with st.expander("➕ Add New Account"):
        with st.form("new_acc"):
            name = st.text_input("Account Name")
            a_type = st.selectbox("Type", ["Evaluation", "Live", "Demo"])
            bal = st.number_input("Starting Balance", value=50000)
            target = st.number_input("Profit Target ($)", value=3000) if a_type == "Evaluation" else 0
            if st.form_submit_button("Create"):
                accounts[name] = {"type": a_type, "initial_balance": bal, "target": target}
                save_accounts(accounts)
                st.rerun()
    if accounts:
        for a_name in list(accounts.keys()):
            col1, col2 = st.columns([8, 2])
            col1.write(f"**{a_name}** ({accounts[a_name].get('type')})")
            if col2.button(f"🗑️ Delete {a_name}", key=f"del_{a_name}"):
                trades_df = trades_df[trades_df['Account'] != a_name]
                trades_df.to_csv(TRADES_FILE, index=False)
                del accounts[a_name]
                save_accounts(accounts)
                st.rerun()