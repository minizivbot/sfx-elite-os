import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date
import calendar

# --- הגדרות דף ---
st.set_page_config(page_title="SFX ELITE OS", layout="wide", initial_sidebar_state="expanded")

# --- חיבור ל-Google Sheets ---
# החיבור מתבצע דרך ה-Secrets שהגדרת ב-Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data():
    try:
        # קריאת הנתונים מהגיליון ללא שמירה במטמון (ttl=0) כדי לראות עדכונים מיד
        df = conn.read(ttl="0")
        if df.empty:
            return pd.DataFrame(columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])
        return df
    except:
        # במקרה של שגיאה או גיליון ריק לגמרי
        return pd.DataFrame(columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])

def save_data(df):
    # שמירת הנתונים המעודכנים חזרה ל-Google Sheets
    conn.update(data=df)
    st.cache_data.clear()

# טעינת נתונים והכנה בסיסית
trades_df = load_data()
if not trades_df.empty:
    # המרת עמודת התאריך לפורמט תקין
    trades_df['Date'] = pd.to_datetime(trades_df['Date']).dt.date
    # חישוב PNL ריאלי לשימוש פנימי בדאשבורד
    trades_df['Real_PNL'] = trades_df.apply(
        lambda r: -abs(r['PNL']) if r['Outcome'] == 'Loss' else (abs(r['PNL']) if r['Outcome'] == 'Win' else 0), 
        axis=1
    )

# --- ניהול ניווט (כולל תיקון לשגיאת ה-ValueError שראית) ---
main_nav = ["Dashboard", "Trade Log", "Analytics"]
if 'page' not in st.session_state or st.session_state.page not in main_nav:
    st.session_state.page = "Dashboard"

if 'cal_month' not in st.session_state: st.session_state.cal_month = datetime.now().month
if 'cal_year' not in st.session_state: st.session_state.cal_year = datetime.now().year

# --- עיצוב CSS מותאם אישית ---
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
    
    # בחירת עמוד בטוחה
    current_index = main_nav.index(st.session_state.page)
    st.session_state.page = st.radio("Navigation", main_nav, index=current_index)

    if not trades_df.empty:
        available_accounts = trades_df['Account'].unique().tolist()
        selected_acc = st.selectbox("Active Account", available_accounts) if available_accounts else None
        if selected_acc:
            acc_trades = trades_df[trades_df['Account'] == selected_acc]
            net_pnl = acc_trades['Real_PNL'].sum()
            st.metric("Total Net PNL", f"${net_pnl:,.2f}")
    else:
        selected_acc = None

# --- Dashboard ---
if st.session_state.page == "Dashboard":
    if not selected_acc:
        st.info("Log your first trade in 'Trade Log' to see the dashboard!")
    else:
        st.markdown(f"<p class='main-header'>{selected_acc} Overview</p>", unsafe_allow_html=True)
        
        # מדדים מהירים (Metrics)
        m1, m2, m3, m4 = st.columns(4)
        total = len(acc_trades)
        wins = len(acc_trades[acc_trades['Outcome'] == 'Win'])
        m1.metric("Win Rate", f"{(wins/total*100 if total>0 else 0):.1f}%")
        m2.metric("Net PNL", f"${net_pnl:,.2f}")
        m3.metric("Avg Risk %", f"{acc_trades['Risk_Percent'].mean():.2f}%" if total > 0 else "0%")
        m4.metric("Total Trades", total)

        st.write("---")
        
        # לוח שנה אינטראקטיבי
        st.subheader("📅 Trading Calendar")
        c1, c2, c3 = st.columns([6, 1, 1])
        with c1: st.write(f"**{calendar.month_name[st.session_state.cal_month]} {st.session_state.cal_year}**")
        if c2.button("⬅️"): 
            st.session_state.cal_month = 12 if st.session_state.cal_month == 1 else st.session_state.cal_month - 1
            st.rerun()
        if c3.button("➡️"): 
            st.session_state.cal_month = 1 if st.session_state.cal_month == 12 else st.session_state.cal_month + 1
            st.rerun()

        cal = calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
        cols = st.columns(7)
        days_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, d_n in enumerate(days_labels): 
            cols[i].markdown(f"<p style='text-align:center; color:#888;'>{d_n}</p>", unsafe_allow_html=True)
        
        for week in cal:
            cols = st.columns(7)
            for i, day in enumerate(week):
                if day != 0:
                    curr_date = date(st.session_state.cal_year, st.session_state.cal_month, day)
                    day_trades = acc_trades[acc_trades['Date'] == curr_date]
                    if not day_trades.empty:
                        day_pnl = day_trades['Real_PNL'].sum()
                        cls = "cal-win" if day_pnl >= 0 else "cal-loss"
                        cols[i].markdown(f'<div class="cal-card {cls}"><b>{day}</b><br>${day_pnl:,.0f}</div>', unsafe_allow_html=True)
                    else:
                        cols[i].markdown(f'<div class="cal-card"><b>{day}</b></div>', unsafe_allow_html=True)

        # סיכום ביצועים חודשי
        st.write("---")
        st.subheader("📈 Weekly Breakdown")
        acc_trades['Week'] = acc_trades.apply(lambda x: (x['Date'].day - 1) // 7 + 1 if x['Date'].month == st.session_state.cal_month else 0, axis=1)
        weekly_stats = acc_trades[acc_trades['Week'] > 0].groupby('Week')['Real_PNL'].sum()
        w_cols = st.columns(4)
        for i in range(1, 5):
            val = weekly_stats.get(i, 0)
            color = accent if val >= 0 else loss_color
            w_cols[i-1].markdown(f'<div style="background:#0d0d0d; padding:15px; border-radius:10px; border-left:4px solid {color}"><small style="color:#888">Week {i}</small><br><b style="font-size:1.2rem; color:{color}">${val:,.0f}</b></div>', unsafe_allow_html=True)

# --- Trade Log (הזנה ישירה ל-Cloud) ---
elif st.session_state.page == "Trade Log":
    st.markdown("<p class='main-header'>📜 Trade Log</p>", unsafe_allow_html=True)
    
    with st.expander("➕ LOG NEW TRADE", expanded=True):
        with st.form("new_trade_form"):
            c1, c2 = st.columns(2)
            # אם אין חשבון קיים, ברירת המחדל היא LUCIDFLEX 25K
            acc_name = c1.text_input("Account Name", value=selected_acc if selected_acc else "LUCIDFLEX 25K")
            d = c1.date_input("Date", date.today())
            pair = c1.selectbox("Pair", ["NQ", "ES"])
            side = c1.radio("Side", ["Long", "Short"], horizontal=True)
            
            risk_p = c2.number_input("Risk %", value=1.0, step=0.1)
            rr = c2.number_input("RR", value=0.0, step=0.1)
            out = c2.selectbox("Outcome", ["Win", "Loss", "BE"])
            pnl = c2.number_input("PNL ($)", min_value=0.0, step=10.0)
            poi = st.multiselect("POI", ["IFVG", "FVG", "MSS", "SMT", "LQ", "OB", "AMD"])
            
            if st.form_submit_button("SAVE TO GOOGLE SHEETS"):
                new_row = pd.DataFrame([[
                    d, acc_name, pair, side, rr, ", ".join(poi), out, pnl, risk_p
                ]], columns=['Date', 'Account', 'Pair', 'Side', 'RR', 'POI', 'Outcome', 'PNL', 'Risk_Percent'])
                
                # הסרת עמודות עזר לפני השמירה לגיליון
                clean_df = trades_df.drop(columns=['Real_PNL', 'Week'], errors='ignore')
                updated_df = pd.concat([clean_df, new_row], ignore_index=True)
                
                save_data(updated_df)
                st.success("Trade synced successfully!")
                st.rerun()

    if not trades_df.empty:
        st.subheader("Recent History")
        # הצגת הטבלה ללא עמודות החישוב הפנימיות
        view_df = trades_df.sort_values(by='Date', ascending=False).drop(columns=['Real_PNL', 'Week'], errors='ignore')
        st.dataframe(view_df, use_container_width=True, hide_index=True)
        
        if st.button("❌ Remove Last Entry"):
            clean_df = trades_df.drop(columns=['Real_PNL', 'Week'], errors='ignore')
            save_data(clean_df[:-1])
            st.rerun()

# --- Analytics ---
elif st.session_state.page == "Analytics":
    st.markdown("<p class='main-header'>📊 Analytics</p>", unsafe_allow_html=True)
    if not trades_df.empty:
        # ניתוח לפי POI
        st.subheader("Performance by POI")
        poi_df = trades_df.assign(POI=trades_df['POI'].str.split(', ')).explode('POI')
        poi_stats = poi_df.groupby('POI').agg(Trades=('Outcome', 'count'), PNL=('Real_PNL', 'sum'))
        st.table(poi_stats.sort_values(by='PNL', ascending=False))
        
        # ניתוח לפי צד (Long/Short)
        st.subheader("Side Analysis")
        side_stats = trades_df.groupby('Side').agg(Trades=('Outcome', 'count'), PNL=('Real_PNL', 'sum'))
        st.table(side_stats)
    else:
        st.info("No trades found to analyze.")
