import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar
from supabase import create_client

# --- 1. SUPABASE CONNECTION ---
# המערכת שואבת אוטומטית את הפרטים מה-Secrets שהגדרת
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except:
    st.error("Missing Supabase Secrets! Go to Streamlit Settings -> Secrets.")
    st.stop()

# --- 2. DATA FUNCTIONS ---
def load_accounts():
    res = supabase.table("accounts").select("*").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=['account_name', 'target', 'drawdown'])

def load_trades():
    res = supabase.table("trades").select("*").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        df['date'] = pd.to_datetime(df['date']).dt.date
        return df
    return pd.DataFrame(columns=['date', 'account', 'pair', 'side', 'rr', 'poi', 'outcome', 'pnl'])

# --- 3. CONFIG & UI ---
st.set_page_config(page_title="SFX ELITE OS", layout="wide")

# טעינת נתונים
accounts_df = load_accounts()
trades_df = load_trades()

# --- עיצוב וסטייל (כמו שאהבת) ---
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; }
    h1, h2, h3 { color: #FFFFFF !important; }
    .main-header { font-size: 2.5rem; font-weight: 900; background: -webkit-linear-gradient(45deg, #34d399, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- ניווט ---
with st.sidebar:
    st.markdown("<h2 class='main-header'>SFX ELITE</h2>", unsafe_allow_html=True)
    page = st.radio("Menu", ["Account Settings", "Dashboard", "Trade Log"])
    
    if not accounts_df.empty:
        acc_list = accounts_df['account_name'].tolist()
        active_acc = st.selectbox("Active Account", acc_list)
    else:
        active_acc = None

# ================= PAGES =================

if page == "Account Settings":
    st.markdown("<p class='main-header'>Account Settings</p>", unsafe_allow_html=True)
    with st.form("add_acc"):
        name = st.text_input("Account Name")
        c1, c2 = st.columns(2)
        tar = c1.number_input("Target", value=1500)
        drw = c2.number_input("Drawdown", value=750)
        if st.form_submit_button("Create Account"):
            supabase.table("accounts").insert({"account_name": name, "target": tar, "drawdown": drw}).execute()
            st.success("Created!")
            st.rerun()

elif page == "Dashboard" and active_acc:
    st.markdown(f"<p class='main-header'>{active_acc} Dashboard</p>", unsafe_allow_html=True)
    # כאן יבואו המטריקות והיומן (כמו בקוד הקודם)
    st.write("Data is safely stored in Supabase.")

elif page == "Trade Log" and active_acc:
    st.markdown(f"<p class='main-header'>Log Trade: {active_acc}</p>", unsafe_allow_html=True)
    with st.form("log_t"):
        d = st.date_input("Date", date.today())
        p = st.selectbox("Pair", ["NQ", "ES", "BTC"])
        s = st.radio("Side", ["Long", "Short"], horizontal=True)
        o = st.selectbox("Outcome", ["Win", "Loss", "BE"])
        val = st.number_input("PNL ($)")
        if st.form_submit_button("Save Trade"):
            supabase.table("trades").insert({
                "date": str(d), "account": active_acc, "pair": p, 
                "side": s, "outcome": o, "pnl": val
            }).execute()
            st.success("Trade Saved!")
            st.rerun()
