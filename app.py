import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
import urllib.parse

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Digital Treasurer",
    page_icon="bar_chart",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. PROFESSIONAL STYLING & ANIMATIONS ---
st.markdown("""
    <style>
    /* Global Settings */
    .stApp {
        background-color: #F1F5F9; /* Professional Light Slate */
        font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
    }
    
    /* ANIMATIONS */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translate3d(0, 40px, 0); }
        to { opacity: 1; transform: translate3d(0, 0, 0); }
    }
    
    .animate-enter {
        animation: fadeInUp 0.8s ease-out;
    }

    /* LOGIN PAGE STYLING */
    .login-header {
        text-align: center;
        padding: 40px 0 20px 0;
    }
    .login-title {
        font-size: 32px;
        font-weight: 700;
        color: #0F172A;
        margin-top: 10px;
    }
    .login-subtitle {
        color: #64748B;
        font-size: 16px;
    }
    
    /* INPUT FIELDS (Modern Look) */
    div.stTextInput > div > div > input {
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 12px;
        background-color: white;
        font-size: 16px;
    }
    div.stTextInput > div > div > input:focus {
        border-color: #0066CC;
        box-shadow: 0 4px 12px rgba(0, 102, 204, 0.1);
    }
    
    /* BUTTONS */
    div.stButton > button {
        background: linear-gradient(135deg, #0066CC 0%, #004494 100%);
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        height: 50px;
        font-size: 16px;
        box-shadow: 0 4px 6px rgba(0, 102, 204, 0.2);
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 102, 204, 0.3);
    }

    /* DASHBOARD CARDS */
    .metric-card {
        background: linear-gradient(135deg, #0066CC 0%, #0052A3 100%);
        color: white;
        padding: 30px;
        border-radius: 16px;
        box-shadow: 0 10px 25px rgba(0, 86, 179, 0.25);
        text-align: center;
        margin-bottom: 25px;
    }
    .metric-value { font-size: 38px; font-weight: 700; margin-top: 10px; }
    
    /* RESULT CARDS */
    .result-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #0066CC;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .badge-fw {
        display: inline-block;
        font-size: 10px;
        font-weight: 700;
        color: white;
        background-color: #475569;
        padding: 3px 8px;
        border-radius: 4px;
        margin-top: 4px;
    }

    /* HIDE DEFAULT ELEMENTS */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 3. ICONS (SVG) ---
ICON_LOGO = """<svg xmlns="http://www.w3.org/2000/svg" width="60" height="60" viewBox="0 0 24 24" fill="none" stroke="#0066CC" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>"""

# --- 4. BACKEND LOGIC (Unchanged) ---
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
    
    # State Initialization
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if 'flat_rate' not in st.session_state: st.session_state['flat_rate'] = 200.0

    # URL Check
    query_params = st.query_params
    url_group = query_params.get("group", None)
    all_groups = get_all_groups()
    selected_group = "Select Group"
    is_direct_link = False

    if url_group and url_group in all_groups:
        selected_group = url_group
        is_direct_link = True

    # --- SCENARIO 1: LANDING PAGE (Login / Register / Public Select) ---
    if not st.session_state['logged_in'] and not is_direct_link and selected_group == "Select Group":
        
        # 1. Header with Animation Class
        st.markdown(f"""
        <div class="login-header animate-enter">
            <div style="margin-bottom: 15px;">{ICON_LOGO}</div>
            <div class="login-title">Digital Treasurer</div>
            <div class="login-subtitle">Secure Financial Transparency System</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. Main Card using Tabs
        tab_login, tab_register, tab_public = st.tabs(["🔐 Sign In", "➕ Create Account", "🌍 Public View"])
        
        with tab_login:
            st.write("") # Spacer
            with st.form("login_form"):
                u = st.text_input("Username", placeholder="Enter your admin username")
                p = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Sign In")
                
                if submitted:
                    if login_user(u, p):
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error("Incorrect username or password.")

        with tab_register:
            st.write("") # Spacer
            st.info("New to Digital Treasurer? Create an admin account to start managing your group.")
            with st.form("reg_form"):
                new_u = st.text_input("Choose Username")
                new_p = st.text_input("Choose Password", type="password")
                reg_submit = st.form_submit_button("Create Admin Account")
                
                if reg_submit:
                    if new_u and new_p:
                        if add_user(new_u, new_p):
                            st.success("Account created successfully! Go to 'Sign In' tab.")
                        else:
                            st.warning("Username already taken.")
                    else:
                        st.error("Please fill all fields.")

        with tab_public:
            st.write("")
            st.info("Are you a member checking your payment? Select your group below.")
            public_choice = st.selectbox("Select Your Committee", ["Select..."] + all_groups)
            if public_choice != "Select...":
                # Redirect by reloading with query param (Simulated by state in Streamlit)
                # Ideally, we just set the URL, but here we show a link
                safe = urllib.parse.quote(public_choice)
                st.markdown(f"**👉 Click to view:** [{public_choice} Dashboard](/?group={safe})")

        return

    # --- SIDEBAR (Only visible when Logged In or Viewing a Group) ---
    with st.sidebar:
        st.write("### Menu")
        if st.session_state['logged_in']:
            st.success("Admin Active")
            selected_group = st.selectbox("Working On Client:", all_groups if all_groups else ["No Groups"])
            
            if selected_group != "No Groups":
                safe_name = urllib.parse.quote(selected_group)
                st.caption("Link Code:")
                st.code(f"?group={safe_name}", language="text")

            with st.expander("Add Client"):
                new_grp = st.text_input("Name")
                if st.button("Create"):
                    if create_group(new_grp): st.rerun()

            st.divider()
            new_rate = st.number_input("Flat Rate", value=st.session_state['flat_rate'], step=50.0)
            if new_rate != st.session_state['flat_rate']:
                st.session_state['flat_rate'] = new_rate
                st.rerun()

            if st.button("Sign Out"):
                st.session_state['logged_in'] = False
                st.rerun()

        elif is_direct_link:
             if st.button("🏠 Home"):
                st.query_params.clear()
                st.rerun()

    # --- SCENARIO 2: ADMIN DASHBOARD ---
    if st.session_state['logged_in']:
        if not all_groups: st.warning("Please create a client in the sidebar.")
        else:
            st.markdown(f"## {selected_group}")
            
            tab1, tab2, tab3, tab4 = st.tabs(["Contributions", "Logistics", "WhatsApp Tool", "Data Export"])
            
            with tab1:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        name = st.text_input("Name")
                        amt_type = st.radio("Type", [f"Fixed ({st.session_state['flat_rate']})", "Custom"], horizontal=True)
                        amount = st.session_state['flat_rate'] if "Fixed" in amt_type else st.number_input("Amount", min_value=0.0)
                    with c2:
                        pay = st.selectbox("Method", ["M-Pesa", "Cash", "Bank"])
                        evt = st.selectbox("Event", ["Burial", "Wedding", "Hospital"])
                    
                    fw = st.checkbox("Include Logistics (Firewood/Food)", False)
                    code = st.text_input("Ref Code")
                    
                    if st.button("Save Entry"):
                        if name and amount > 0:
                            add_contribution(selected_group, name, amount, pay, code, evt)
                            if fw: add_logistics(selected_group, name, "Logistics")
                            st.success("Entry Saved")

            with tab2:
                with st.form("logistics"):
                    fn = st.text_input("Name (Logistics Only)")
                    if st.form_submit_button("Mark Received"):
                        add_logistics(selected_group, fn, "Logistics")
                        st.success("Saved")

            with tab3:
                df = view_contributions(selected_group)
                if not df.empty:
                    e = st.selectbox("Report Event", df['event_type'].unique())
                    if st.button("Generate Report"):
                        sub = df[df['event_type'] == e]
                        t = sub['amount'].sum()
                        txt = f"REPORT: {selected_group.upper()}\nDATE: {datetime.now().strftime('%d-%b')}\n\nCASH CONTRIBUTIONS:\n"
                        for i, r in sub.reset_index().iterrows(): txt += f"{i+1}. {r['member_name']} : {r['amount']:,.0f}\n"
                        fw_df = view_logistics(selected_group)
                        if not fw_df.empty:
                            txt += "\nLOGISTICS RECEIVED:\n"
                            for n in fw_df['member_name'].unique(): txt += f"- {n}\n"
                        txt += f"\nTOTAL: KES {t:,.0f}\n"
                        st.text_area("Copy Text:", txt, height=300)

            with tab4:
                st.dataframe(view_contributions(selected_group), use_container_width=True)
                csv = view_contributions(selected_group).to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "report.csv", "text/csv")

    # --- SCENARIO 3: PUBLIC DASHBOARD ---
    elif selected_group != "Select Group":
        st.markdown(f"<h3 style='text-align:center; color:#64748B;'>{selected_group}</h3>", unsafe_allow_html=True)
        
        df = view_contributions(selected_group)
        if not df.empty:
            st.markdown(f"""
            <div class="metric-card animate-enter">
                <div style="opacity: 0.7; margin-bottom: 5px;">TOTAL COLLECTED</div>
                <div class="metric-value">KES {df['amount'].sum():,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            search = st.text_input("Search Name", placeholder="Type name...")
            
            if search:
                res = df[df['member_name'].str.contains(search, case=False, na=False)]
                fw_stat = get_firewood_status(selected_group, search)
                
                if not res.empty:
                    st.success(f"Record Found")
                    for i, row in res.iterrows():
                        badge = "<span class='badge-fw'>LOGISTICS RECEIVED</span>" if get_firewood_status(selected_group, row['member_name']) else ""
                        st.markdown(f"""
                        <div class="result-card">
                            <div class="result-info">
                                <h4>{row['member_name']}</h4>
                                <p>{row['date_added'][:10]} • {row['event_type']}</p>
                                {badge}
                            </div>
                            <div class="result-amount">
                                {row['amount']:,.0f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                elif fw_stat:
                    st.success("Record Found")
                    st.markdown(f"""
                    <div class="result-card">
                        <div class="result-info">
                            <h4>{search}</h4>
                            <span class='badge-fw'>LOGISTICS ONLY</span>
                        </div>
                        <div class="result-amount" style="color:#94a3b8;">
                            0.00
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("No record found with that name.")
            
            st.write("---")
            st.markdown("<p style='text-align:center; font-size:12px; color:#94a3b8;'>Recent Updates</p>", unsafe_allow_html=True)
            st.dataframe(df[['member_name', 'amount']].tail(5).iloc[::-1], hide_index=True, use_container_width=True)
        else:
            st.info("No records found.")

if __name__ == '__main__':
    main()
