import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import date

# --- חיבור לבסיס הנתונים (חייב להגדיר ב-Secrets) ---
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("שגיאת חיבור: וודא שהגדרת את ה-Secrets ב-Streamlit")
    st.stop()

# --- הגדרות דף ועיצוב ---
st.set_page_config(page_title="SFX ELITE OS", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; }
    .main-header { font-size: 3rem; font-weight: 900; background: -webkit-linear-gradient(45deg, #34d399, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 30px; }
    .metric-card { background: #1A1F26; padding: 20px; border-radius: 15px; border: 1px solid #2D3748; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>SFX ELITE OS</h1>", unsafe_allow_html=True)

# --- טעינת נתונים מ-Supabase ---
def get_accounts():
    res = supabase.table("accounts").select("*").execute()
    return res.data if res.data else []

def get_trades():
    res = supabase.table("trades").select("*").execute()
    return res.data if res.data else []

accounts = get_accounts()
trades = get_trades()

# --- תפריט צדדי ---
with st.sidebar:
    st.title("Navigation")
    menu = st.radio("בחר עמוד:", ["Dashboard", "Trade Log", "Account Settings"])

# ================= 1. ACCOUNT SETTINGS =================
if menu == "Account Settings":
    st.subheader("ניהול חשבונות מסחר")
    
    with st.form("add_account_form"):
        col1, col2, col3 = st.columns(3)
        acc_name = col1.text_input("שם החשבון (למשל: My 25K Challenge)")
        acc_target = col2.number_input("יעד רווח ($)", value=1500)
        acc_drawdown = col3.number_input("מקסימום דראודאון ($)", value=750)
        
        if st.form_submit_button("צור חשבון חדש"):
            if acc_name:
                supabase.table("accounts").insert({
                    "account_name": acc_name, 
                    "target": acc_target, 
                    "drawdown": acc_drawdown
                }).execute()
                st.success(f"חשבון '{acc_name}' נוצר!")
                st.rerun()
            else:
                st.error("חייב להזין שם חשבון")

# ================= 2. TRADE LOG =================
elif menu == "Trade Log":
    if not accounts:
        st.warning("עבור ל-Account Settings וצור חשבון קודם.")
    else:
        st.subheader("תיעוד טרייד חדש")
        acc_names = [a['account_name'] for a in accounts]
        
        with st.form("log_trade"):
            c1, c2, c3 = st.columns(3)
            selected_acc = c1.selectbox("בחר חשבון", acc_names)
            pair = c2.selectbox("צמד", ["NQ", "ES", "BTC", "ETH", "Gold"])
            side = c3.selectbox("Side", ["Long", "Short"])
            
            c4, c5, c6 = st.columns(3)
            outcome = c4.selectbox("תוצאה", ["Win", "Loss", "BE"])
            pnl = c5.number_input("PNL ($)", step=10.0)
            trade_date = c6.date_input("תאריך", date.today())
            
            if st.form_submit_button("שמור עסקאות"):
                supabase.table("trades").insert({
                    "account": selected_acc,
                    "pair": pair,
                    "side": side,
                    "outcome": outcome,
                    "pnl": pnl,
                    "date": str(trade_date)
                }).execute()
                st.success("הטרייד נשמר בהצלחה!")
                st.rerun()

# ================= 3. DASHBOARD =================
elif menu == "Dashboard":
    if not accounts:
        st.info("אין נתונים להצגה. התחל ביצירת חשבון.")
    else:
        for acc in accounts:
            acc_trades = [t for t in trades if t['account'] == acc['account_name']]
            total_pnl = sum([t['pnl'] for t in acc_trades])
            
            st.markdown(f"### חשבון: {acc['account_name']}")
            m1, m2, m3 = st.columns(3)
            
            with m1:
                st.markdown(f"<div class='metric-card'><h4>PNL נוכחי</h4><h2 style='color:#34d399;'>${total_pnl}</h2></div>", unsafe_allow_html=True)
            with m2:
                st.markdown(f"<div class='metric-card'><h4>יעד (Target)</h4><h2>${acc['target']}</h2></div>", unsafe_allow_html=True)
            with m3:
                st.markdown(f"<div class='metric-card'><h4>Drawdown</h4><h2 style='color:#f87171;'>${acc['drawdown']}</h2></div>", unsafe_allow_html=True)
            
            if acc_trades:
                st.write("#### עסקאות אחרונות")
                st.table(pd.DataFrame(acc_trades)[['date', 'pair', 'side', 'outcome', 'pnl']].tail(5))
            st.divider()
