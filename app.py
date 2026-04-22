import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

# --- הגדרות דף ---
st.set_page_config(page_title="SFX ELITE OS", layout="wide", initial_sidebar_state="expanded")

# --- חיבור ל-DATABASE ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("Missing Secrets! Check Streamlit Settings -> Secrets")
    st.stop()

# --- עיצוב CSS מורחב ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; }
    .main-header { font-size: 3.5rem; font-weight: 900; background: linear-gradient(45deg, #34d399, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; padding: 20px; }
    .card { background: #1A1F26; padding: 25px; border-radius: 15px; border: 1px solid #2D3748; margin-bottom: 20px; }
    .metric-val { font-size: 2rem; font-weight: bold; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>SFX ELITE OS</h1>", unsafe_allow_html=True)

# --- פונקציות נתונים ---
def get_data(table_name):
    try:
        res = supabase.table(table_name).select("*").execute()
        return res.data if res.data else []
    except:
        return []

accounts = get_data("accounts")
trades = get_data("trades")

# --- תפריט ניווט ---
page = st.sidebar.radio("ניווט במערכת", ["📊 Dashboard", "📝 Trade Log", "⚙️ Account Settings"])

# ================= PAGE: SETTINGS =================
if page == "⚙️ Account Settings":
    st.markdown("<div class='card'><h2>ניהול חשבונות מסחר</h2></div>", unsafe_allow_html=True)
    
    with st.form("new_account"):
        col1, col2, col3 = st.columns(3)
        name = col1.text_input("שם החשבון")
        target = col2.number_input("יעד רווח ($)", value=1500)
        drawdown = col3.number_input("מקסימום הפסד ($)", value=750)
        
        if st.form_submit_button("צור חשבון"):
            if name:
                supabase.table("accounts").insert({"account_name": name, "target": target, "drawdown": drawdown}).execute()
                st.success(f"החשבון {name} נוצר בהצלחה!")
                st.rerun()

# ================= PAGE: TRADE LOG =================
elif page == "📝 Trade Log":
    if not accounts:
        st.warning("עליך ליצור חשבון תחילה בהגדרות.")
    else:
        st.markdown("<div class='card'><h2>תיעוד עסקה חדשה</h2></div>", unsafe_allow_html=True)
        acc_names = [a['account_name'] for a in accounts]
        
        with st.form("log_trade"):
            c1, c2, c3 = st.columns(3)
            acc = c1.selectbox("חשבון", acc_names)
            pair = c2.selectbox("צמד", ["NQ", "ES", "BTC", "ETH"])
            side = c3.radio("Side", ["Long", "Short"], horizontal=True)
            
            c4, c5, c6 = st.columns(3)
            outcome = c4.selectbox("תוצאה", ["Win", "Loss", "BE"])
            pnl = c5.number_input("PNL ($)", step=10.0)
            d = c6.date_input("תאריך", date.today())
            
            if st.form_submit_button("שמור טרייד"):
                supabase.table("trades").insert({
                    "account": acc, "pair": pair, "side": side, 
                    "outcome": outcome, "pnl": pnl, "date": str(d)
                }).execute()
                st.success("הטרייד נשמר!")
                st.rerun()

# ================= PAGE: DASHBOARD =================
elif page == "📊 Dashboard":
    if not accounts:
        st.info("אין חשבונות פעילים.")
    else:
        for acc in accounts:
            acc_trades = [t for t in trades if t['account'] == acc['account_name']]
            total_pnl = sum([t['pnl'] for t in acc_trades])
            
            st.markdown(f"### 🏦 חשבון: {acc['account_name']}")
            m1, m2, m3 = st.columns(3)
            m1.metric("PNL כולל", f"${total_pnl}", delta=f"{total_pnl}")
            m2.metric("יעד (Target)", f"${acc['target']}")
            m3.metric("Drawdown", f"${acc['drawdown']}", delta_color="inverse")
            
            if acc_trades:
                df = pd.DataFrame(acc_trades)
                st.dataframe(df[['date', 'pair', 'side', 'outcome', 'pnl']], use_container_width=True)
            st.divider()
