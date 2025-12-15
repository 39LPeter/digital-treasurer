import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
import urllib.parse

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Digital Treasurer",
    page_icon="static/favicon.png", # You can replace this if you have a file, otherwise it defaults
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. HIGH-END UI STYLING (CSS) ---
st.markdown("""
    <style>
    /* IMPORT MODERN FONT - INTER */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');

    /* GLOBAL RESET */
    .stApp {
        background-color: #F8FAFC; /* Slate-50: Very subtle grey-blue */
        font-family: 'Inter', sans-serif;
    }

    /* TYPOGRAPHY */
    h1, h2, h3, h4, .app-title {
        color: #0F172A; /* Slate-900 */
        font-family: 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    p, label, .stMarkdown, .caption {
        color: #64748B; /* Slate-500 */
        font-size: 14px;
    }

    /* BUTTONS - GRADIENT & SHADOW */
    div.stButton > button {
        background: linear-gradient(180deg, #3B82F6 0%, #2563EB 100%); /* Corporate Blue */
        color: white;
        border: 1px solid #2563EB;
        padding: 12px 24px;
        border-radius: 8px; /* Slightly tighter radius for pro look */
        font-weight: 600;
        font-size: 15px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: all 0.2s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(180deg, #2563EB 0%, #1D4ED8 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    /* INPUT FIELDS - CLEAN & MINIMAL */
    div.stTextInput > div > div > input, 
    div.stNumberInput > div > div > input,
    div.stSelectbox > div > div > div {
        border-radius: 8px;
        border: 1px solid #E2E8F0; /* Slate-200 */
        padding: 10px 15px;
        font-size: 15px;
        color: #1E293B;
        background-color: #FFFFFF;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    div.stTextInput > div > div > input:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }

    /* LOGIN CONTAINER */
    .login-container {
        background: white;
        padding: 48px 32px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.025);
        text-align: center;
        margin-top: 40px;
        border: 1px solid #F1F5F9;
        animation: fadeIn 0.8s ease-out;
    }

    /* METRIC CARD */
    .metric-card {
        background: white;
        border: 1px solid #E2E8F0;
        padding: 24px;
        border-radius: 12px;
        text-align: left; /* Aligned left looks more pro */
        margin-bottom: 24px;
        border-left: 4px solid #3B82F6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .metric-label {
        color: #64748B;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        color: #0F172A;
        font-size: 36px;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin-top: 4px;
    }

    /* SEARCH RESULTS */
    .result-card {
        background: white;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: border-color 0.2s;
    }
    .result-card:hover {
        border-color: #3B82F6;
    }

    /* LOGO ICON STYLING */
    .logo-icon {
        width: 48px;
        height: 48px;
        color: #2563EB;
        margin-bottom: 16px;
    }

    /* HIDE DEFAULT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MODERN ICONS (SVG PATHS) ---
# These are "Heroicons" style - clean, outline, stroke-based.

# A modern abstract logo (Hexagon + Check) implies security & accuracy
ICON_LOGO_SVG = """
<svg class="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
<path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

# --- 4. BACKEND LOGIC ---
def init_db():
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS groups (group_name TEXT PRIMARY KEY, created_at TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS contributions (id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, member_name TEXT, amount REAL, payment_mode TEXT, transaction_code TEXT, event_type TEXT, date_added TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS logistics (id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, member_name TEXT, item_type TEXT, date_added TIMESTAMP)')
    conn.commit()
    conn.close()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

def add_user(username, password):
    conn = sqlite3.connect('contributions.db')
    try:
        conn.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def login_user(username, password):
    conn = sqlite3.connect('contributions.db')
    data = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchall()
    conn.close()
    if data and check_hashes(password, data[0][1]): return True
    return False

def create_group(name):
    conn = sqlite3.connect('contributions.db')
    try:
        conn.execute('INSERT INTO groups(group_name, created_at) VALUES (?,?)', (name, datetime.now()))
        conn.commit()
        return True
    except: return False
    finally: conn.close()

def get_all_groups():
    conn = sqlite3.connect('contributions.db')
    df = pd.read_sql_query("SELECT group_name FROM groups", conn)
    conn.close()
    return df['group_name'].tolist()

def add_contribution(group, name, amount, mode, code, event):
    conn = sqlite3.connect('contributions.db')
    conn.execute('INSERT INTO contributions(group_name, member_name, amount, payment_mode, transaction_code, event_type, date_added) VALUES (?,?,?,?,?,?,?)',
                 (group, name, amount, mode, code, event, datetime.now()))
    conn.commit()
    conn.close()

def add_logistics(group, name, item):
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    c.execute("SELECT * FROM logistics WHERE group_name = ? AND member_name = ? AND item_type = ?", (group, name, item))
    if not c.fetchall():
        c.execute('INSERT INTO logistics(group_name, member_name, item_type, date_added) VALUES (?,?,?,?)', (group, name, item, datetime.now()))
        conn.commit()
    conn.close()

def view_contributions(group):
    conn = sqlite3.connect('contributions.db')
    df = pd.read_sql_query("SELECT member_name, amount, payment_mode, transaction_code, event_type, date_added FROM contributions WHERE group_name = ?", conn, params=(group,))
    conn.close()
    return df

def view_logistics(group):
    conn = sqlite3.connect('contributions.db')
    df = pd.read_sql_query("SELECT member_name, item_type, date_added FROM logistics WHERE group_name = ?", conn, params=(group,))
    conn.close()
    return df

def get_firewood_status(group, name):
    conn = sqlite3.connect('contributions.db')
    data = conn.execute("SELECT item_type FROM logistics WHERE group_name = ? AND member_name LIKE ?", (group, '%'+name+'%',)).fetchall()
    conn.close()
    return len(data) > 0

# --- 5. UI FLOW ---
def main():
    init_db()
    
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if 'flat_rate' not in st.session_state: st.session_state['flat_rate'] = 200.0

    query_params = st.query_params
    url_group = query_params.get("group", None)
    all_groups = get_all_groups()
    selected_group = "Select Group"
    is_direct_link = False

    if url_group and url_group in all_groups:
        selected_group = url_group
        is_direct_link = True

    # ------------------------------------
    # LANDING PAGE
    # ------------------------------------
    if not st.session_state['logged_in'] and not is_direct_link and selected_group == "Select Group":
        
        # Professional Login Card
        st.markdown(f"""
        <div class="login-container">
            {ICON_LOGO_SVG}
            <h1 style="margin-bottom: 8px;">Digital Treasurer</h1>
            <p style="margin-bottom: 32px;">Secure Financial Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Clean Tabs (No Emojis)
        tab_login, tab_register, tab_public = st.tabs(["SIGN IN", "REGISTER", "FIND GROUP"])
        
        with tab_login:
            st.write("")
            with st.form("login_form"):
                u = st.text_input("Username", placeholder="Enter admin ID")
                p = st.text_input("Password", type="password", placeholder="Enter password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("LOGIN"):
                    if login_user(u, p):
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else: st.error("Access Denied")

        with tab_register:
            st.write("")
            st.info("Create a new organization account.")
            with st.form("reg_form"):
                nu = st.text_input("New Username")
                np = st.text_input("New Password", type="password")
                st.markdown("<br>", unsafe_allow_html=True)
                if st.form_submit_button("CREATE ACCOUNT"):
                    if add_user(nu, np): st.success("Account Created.")

        with tab_public:
            st.write("")
            st.caption("Select your organization to view records.")
            choice = st.selectbox("Select Organization", ["Choose..."] + all_groups)
            if choice != "Choose...":
                safe = urllib.parse.quote(choice)
                st.markdown(f"**👉 [OPEN PORTAL](/?group={safe})**")
        return

    # ------------------------------------
    # SIDEBAR
    # ------------------------------------
    with st.sidebar:
        st.markdown("### SETTINGS")
        if st.session_state['logged_in']:
            st.success("ADMIN: ACTIVE")
            selected_group = st.selectbox("ACTIVE CLIENT", all_groups if all_groups else ["No Groups"])
            
            if selected_group != "No Groups":
                safe_name = urllib.parse.quote(selected_group)
                st.caption("CLIENT LINK CODE")
                st.code(f"?group={safe_name}", language="text")

            with st.expander("NEW CLIENT"):
                new_grp = st.text_input("Client Name")
                if st.button("ADD"):
                    if create_group(new_grp): st.rerun()

            st.divider()
            new_rate = st.number_input("FLAT RATE (KES)", value=st.session_state['flat_rate'], step=50.0)
            if new_rate != st.session_state['flat_rate']:
                st.session_state['flat_rate'] = new_rate
                st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("LOGOUT"):
                st.session_state['logged_in'] = False
                st.rerun()
        
        elif is_direct_link:
             if st.button("← HOME"):
                st.query_params.clear()
                st.rerun()

    # ------------------------------------
    # ADMIN DASHBOARD
    # ------------------------------------
    if st.session_state['logged_in']:
        if not all_groups: st.warning("Please create a client in the sidebar.")
        else:
            st.markdown(f"### 📂 {selected_group}")
            
            # Text-Only Tabs for Professionalism
            tab1, tab2, tab3, tab4 = st.tabs(["ENTRY", "LOGISTICS", "WHATSAPP", "DATA"])
            
            with tab1:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        name = st.text_input("Member Name")
                        amt_type = st.radio("Amount", [f"Fixed ({st.session_state['flat_rate']})", "Custom"], horizontal=True)
                        amount = st.session_state['flat_rate'] if "Fixed" in amt_type else st.number_input("Value", min_value=0.0)
                    with c2:
                        pay = st.selectbox("Method", ["M-Pesa", "Cash", "Bank"])
                        evt = st.selectbox("Event", ["Burial", "Wedding", "Hospital"])
                    
                    fw = st.checkbox("Include Logistics?", False)
                    code = st.text_input("Reference")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("SAVE RECORD"):
                        if name and amount > 0:
                            add_contribution(selected_group, name, amount, pay, code, evt)
                            if fw: add_logistics(selected_group, name, "Logistics")
                            st.success("Record Saved")

            with tab2:
                with st.form("logistics"):
                    fn = st.text_input("Name (Logistics Only)")
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("MARK RECEIVED"):
                        add_logistics(selected_group, fn, "Logistics")
                        st.success("Saved")

            with tab3:
                df = view_contributions(selected_group)
                if not df.empty:
                    e = st.selectbox("Event Context", df['event_type'].unique())
                    if st.button("GENERATE REPORT"):
                        sub = df[df['event_type'] == e]
                        t = sub['amount'].sum()
                        txt = f"📢 *UPDATE: {selected_group.upper()}*\n📅 {datetime.now().strftime('%d-%b-%Y')}\n\n*CONTRIBUTIONS:*\n"
                        for i, r in sub.reset_index().iterrows(): txt += f"{i+1}. {r['member_name']} : {r['amount']:,.0f}\n"
                        fw_df = view_logistics(selected_group)
                        if not fw_df.empty:
                            txt += "\n*LOGISTICS RECEIVED:*\n"
                            for n in fw_df['member_name'].unique(): txt += f"✅ {n}\n"
                        txt += f"\n💰 *TOTAL: KES {t:,.0f}*\n"
                        st.text_area("Copy Text:", txt, height=300)

            with tab4:
                st.dataframe(view_contributions(selected_group), use_container_width=True)
                csv = view_contributions(selected_group).to_csv(index=False).encode('utf-8')
                st.download_button("DOWNLOAD CSV", csv, "data.csv", "text/csv")

    # ------------------------------------
    # PUBLIC DASHBOARD
    # ------------------------------------
    elif selected_group != "Select Group":
        # Minimal Header
        st.markdown(f"<div style='text-align:center; font-weight:600; color:#94A3B8; margin-bottom:16px; letter-spacing:1px;'>{selected_group.upper()}</div>", unsafe_allow_html=True)
        
        df = view_contributions(selected_group)
        if not df.empty:
            # Clean Metric Card
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Collections</div>
                <div class="metric-value">KES {df['amount'].sum():,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Search Input
            search = st.text_input("Search", placeholder="Search by name...", label_visibility="collapsed")
            
            if search:
                res = df[df['member_name'].str.contains(search, case=False, na=False)]
                fw_stat = get_firewood_status(selected_group, search)
                
                if not res.empty:
                    st.success("Verified")
                    for i, row in res.iterrows():
                        badge = "<span style='background:#F1F5F9; color:#475569; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600;'>Logistics Received</span>" if get_firewood_status(selected_group, row['member_name']) else ""
                        st.markdown(f"""
                        <div class="result-card">
                            <div>
                                <div style="font-weight:600; color:#1E293B; font-size:16px;">{row['member_name']}</div>
                                <div style="font-size:13px; color:#64748B;">{row['date_added'][:10]} • {row['event_type']}</div>
                                {badge}
                            </div>
                            <div style="font-weight:700; color:#0F172A; font-size:18px;">
                                {row['amount']:,.0f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                elif fw_stat:
                    st.success("Verified")
                    st.markdown(f"""
                    <div class="result-card">
                        <div>
                            <div style="font-weight:600; color:#1E293B;">{search}</div>
                            <span style='background:#F1F5F9; color:#475569; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600;'>Logistics Only</span>
                        </div>
                        <div style="color:#CBD5E1; font-size:18px;">—</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No records found.")
            
            # Recent List
            st.write("")
            st.markdown("<div style='text-align:center; font-size:12px; color:#94A3B8; margin-top:24px; text-transform:uppercase; letter-spacing:1px;'>Recent Transactions</div>", unsafe_allow_html=True)
            st.dataframe(df[['member_name', 'amount']].tail(5).iloc[::-1], hide_index=True, use_container_width=True)
        else:
            st.info("No records found for this group.")

if __name__ == '__main__':
    main()
