import streamlit as st
import sqlite3
import hashlib
from datetime import datetime
import pandas as pd
import urllib.parse

# --- 1. APP CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Digital Treasurer",
    page_icon="💼",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for the "Pro App" look
st.markdown("""
    <style>
    .stApp { background-color: #F0F2F6; }
    
    /* Metrics */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        margin-bottom: 20px;
        border-left: 5px solid #2E86C1;
    }
    .metric-value { font-size: 28px; font-weight: bold; color: #2E86C1; }
    .metric-label { font-size: 14px; color: #666; }
    
    /* Search Results */
    .success-box {
        padding: 15px;
        background-color: #ffffff;
        border-left: 5px solid #28a745;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    
    /* Badges */
    .badge-fw {
        background-color: #8B4513;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
    }
    .badge-date {
        color: #888;
        font-size: 12px;
    }

    /* Buttons */
    div.stButton > button { 
        width: 100%; 
        border-radius: 8px; 
        height: 45px; 
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE MANAGEMENT ---
def init_db():
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    # Create Tables
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS groups (group_name TEXT PRIMARY KEY, created_at TIMESTAMP)')
    c.execute('''CREATE TABLE IF NOT EXISTS contributions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, member_name TEXT, 
                  amount REAL, payment_mode TEXT, transaction_code TEXT, event_type TEXT, date_added TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS logistics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, group_name TEXT, member_name TEXT, 
                  item_type TEXT, date_added TIMESTAMP)''')
    conn.commit()
    conn.close()

# Security Functions
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_hashes(password, hashed_text):
    if make_hashes(password) == hashed_text: return True
    return False

def add_user(username, password):
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', (username, make_hashes(password)))
        conn.commit()
        return True
    except: return False

def login_user(username, password):
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    data = c.fetchall()
    conn.close()
    if data and check_hashes(password, data[0][1]): return True
    return False

# Group Functions
def create_group(name):
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO groups(group_name, created_at) VALUES (?,?)', (name, datetime.now()))
        conn.commit()
        return True
    except: return False

def get_all_groups():
    conn = sqlite3.connect('contributions.db')
    df = pd.read_sql_query("SELECT group_name FROM groups", conn)
    conn.close()
    return df['group_name'].tolist()

# Data Entry Functions
def add_contribution(group, name, amount, mode, code, event):
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    c.execute('INSERT INTO contributions(group_name, member_name, amount, payment_mode, transaction_code, event_type, date_added) VALUES (?,?,?,?,?,?,?)',
              (group, name, amount, mode, code, event, datetime.now()))
    conn.commit()
    conn.close()

def add_logistics(group, name, item):
    conn = sqlite3.connect('contributions.db')
    c = conn.cursor()
    # Avoid duplicates
    c.execute("SELECT * FROM logistics WHERE group_name = ? AND member_name = ? AND item_type = ?", (group, name, item))
    if not c.fetchall():
        c.execute('INSERT INTO logistics(group_name, member_name, item_type, date_added) VALUES (?,?,?,?)',
                  (group, name, item, datetime.now()))
        conn.commit()
    conn.close()

# Data Viewing Functions
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
    c = conn.cursor()
    c.execute("SELECT item_type FROM logistics WHERE group_name = ? AND member_name LIKE ?", (group, '%'+name+'%',))
    data = c.fetchall()
    conn.close()
    return len(data) > 0

# --- 3. MAIN APPLICATION LOGIC ---
def main():
    init_db()

    # Session State
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if 'flat_rate' not in st.session_state: st.session_state['flat_rate'] = 200.0

    # URL Logic (Magic Link)
    query_params = st.query_params
    url_group = query_params.get("group", None)
    
    all_groups = get_all_groups()
    selected_group = "Select Group..."
    is_direct_link = False

    # Check if user came from a specific link
    if url_group and url_group in all_groups:
        selected_group = url_group
        is_direct_link = True

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.title("⚙️ Menu")
        
        # ADMIN VIEW
        if st.session_state['logged_in']:
            st.success("Admin Mode: Active")
            
            # 1. Select Client to Manage
            selected_group = st.selectbox("Working On Client:", all_groups if all_groups else ["No Groups"])
            
            # 2. Generate Link for Client
            if selected_group != "No Groups":
                st.caption("🔗 Client Link Generator")
                safe_name = urllib.parse.quote(selected_group)
                link_suffix = f"?group={safe_name}"
                st.code(link_suffix, language="text")
                st.info("Add this code to your website URL to send users directly to this group.")

            # 3. Create New Client
            with st.expander("➕ Add New Client"):
                new_grp = st.text_input("Client Name (e.g. Njeri Wedding)")
                if st.button("Create Client"):
                    if create_group(new_grp):
                        st.success("Client Created!")
                        st.rerun()
                    else:
                        st.error("Client already exists")

            # 4. Settings
            st.divider()
            new_rate = st.number_input("Set Flat Rate (KES)", value=st.session_state['flat_rate'], step=50.0)
            if new_rate != st.session_state['flat_rate']:
                st.session_state['flat_rate'] = new_rate
                st.rerun()

            if st.button("🚪 Log Out"):
                st.session_state['logged_in'] = False
                st.rerun()

        # PUBLIC VIEW (Selector)
        elif not is_direct_link:
            st.info("Select your committee:")
            selected_group = st.selectbox("Group Name", ["Select Group..."] + all_groups)
        
        # PUBLIC VIEW (Direct Link)
        else:
            st.info(f"Viewing: {selected_group}")
            if st.button("⬅️ View Different Group"):
                st.query_params.clear()
                st.rerun()

    # --- MAIN CONTENT AREA ---

    # CASE 1: Welcome / Login Screen
    if not st.session_state['logged_in'] and selected_group == "Select Group...":
        st.markdown("<h1 style='text-align: center;'>Digital Treasurer 🛡️</h1>", unsafe_allow_html=True)
        st.write("---")
        st.info("👈 **Members:** Please select your group from the sidebar menu to view records.")
        
        st.write("")
        st.write("")
        with st.expander("🔐 Admin Login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("Login"):
                if login_user(u, p):
                    st.session_state['logged_in'] = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
            
            st.write("---")
            nu = st.text_input("New Admin User")
            np = st.text_input("New Admin Pass", type="password")
            if st.button("Create Admin Account"):
                if add_user(nu, np): st.success("Account Created. Please Login.")
        return

    # CASE 2: Admin Dashboard (Managing a Client)
    if st.session_state['logged_in']:
        if not all_groups:
            st.warning("⚠️ No clients found. Use the sidebar to create one.")
        else:
            st.title(f"📂 {selected_group}")
            
            tab1, tab2, tab3, tab4 = st.tabs(["💰 Add Money", "🪵 Firewood", "📲 WhatsApp", "💾 Data"])
            
            # Tab 1: Money Entry
            with tab1:
                with st.container(border=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        name = st.text_input("Member Name")
                        mode = st.radio("Amount Type", [f"Flat ({st.session_state['flat_rate']})", "Custom"], horizontal=True)
                        amount = st.session_state['flat_rate'] if "Flat" in mode else st.number_input("Amount", min_value=0.0)
                    with c2:
                        pay_mode = st.selectbox("Payment", ["M-Pesa", "Cash", "Bank"])
                        event = st.selectbox("Event", ["Burial", "Wedding", "Hospital", "Other"])
                    
                    st.write("---")
                    fw_check = st.checkbox("🪵 Also brought Firewood?", False)
                    code = st.text_input("Transaction Code (Optional)")
                    
                    if st.button("Save Transaction", type="primary"):
                        if name and amount > 0:
                            add_contribution(selected_group, name, amount, pay_mode, code, event)
                            if fw_check: add_logistics(selected_group, name, "Firewood")
                            st.success(f"Saved: {name} - {amount}")
                        else: st.error("Enter Name and Amount")

            # Tab 2: Firewood Only
            with tab2:
                st.write("Record Firewood (No Money)")
                with st.form("fw_form"):
                    fn = st.text_input("Member Name")
                    if st.form_submit_button("Mark Received"):
                        if fn:
                            add_logistics(selected_group, fn, "Firewood")
                            st.success(f"Firewood marked for {fn}")

            # Tab 3: WhatsApp Reports
            with tab3:
                df = view_contributions(selected_group)
                if not df.empty:
                    evt = st.selectbox("Select Event for Report", df['event_type'].unique())
                    if st.button("Generate WhatsApp List"):
                        sub_df = df[df['event_type'] == evt]
                        total = sub_df['amount'].sum()
                        
                        txt = f"📢 *UPDATE: {selected_group.upper()}*\n"
                        txt += f"📅 {datetime.now().strftime('%d-%b-%Y')} | Event: {evt}\n\n"
                        txt += "*--- 💰 CONTRIBUTIONS ---*\n"
                        for i, r in sub_df.reset_index().iterrows():
                            txt += f"{i+1}. {r['member_name']} : {r['amount']:,.0f}\n"
                        
                        fw_df = view_logistics(selected_group)
                        if not fw_df.empty:
                            txt += "\n*--- 🪵 FIREWOOD ---*\n"
                            for n in fw_df['member_name'].unique(): txt += f"✅ {n}\n"
                        
                        txt += f"\n💰 *TOTAL: KES {total:,.0f}*\n"
                        txt += "------------------\n"
                        txt += "Verify here: [Link]"
                        st.text_area("Copy and Paste:", txt, height=300)

            # Tab 4: Database Export
            with tab4:
                st.dataframe(view_contributions(selected_group), use_container_width=True)
                st.write("---")
                csv = view_contributions(selected_group).to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"⬇️ Download {selected_group} Records (CSV)",
                    data=csv,
                    file_name=f"{selected_group}_data.csv",
                    mime='text/csv'
                )

    # CASE 3: Public Dashboard (Client View)
    elif selected_group != "Select Group...":
        st.markdown(f"<h2 style='text-align: center;'>{selected_group}</h2>", unsafe_allow_html=True)
        
        df = view_contributions(selected_group)
        if not df.empty:
            # Metric
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Total Collections</div>
                <div class="metric-value">KES {df['amount'].sum():,.0f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Search
            search = st.text_input("🔍 Search Your Name", placeholder="Type name here...")
            if search:
                res = df[df['member_name'].str.contains(search, case=False, na=False)]
                fw_stat = get_firewood_status(selected_group, search)
                
                if not res.empty:
                    st.success(f"✅ Found {len(res)} record(s)")
                    for i, row in res.iterrows():
                        fw_badge = "<span class='badge-fw'>🪵 Firewood</span>" if get_firewood_status(selected_group, row['member_name']) else ""
                        st.markdown(f"""
                        <div class="success-box">
                            <b>{row['member_name']}</b><br>
                            KES {row['amount']:,.0f}<br>
                            <span class='badge-date'>{row['date_added'][:10]} • {row['event_type']}</span><br>
                            {fw_badge}
                        </div>
                        """, unsafe_allow_html=True)
                elif fw_stat:
                    st.success("✅ Found Firewood Record")
                    st.markdown(f"""
                    <div class="success-box">
                        <b>{search}</b><br>
                        Amount: Pending<br>
                        <span class='badge-fw'>🪵 Firewood Only</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("❌ Name not found. Please check spelling.")
            
            st.caption("Recent Updates")
            st.dataframe(df[['member_name', 'amount']].tail(5).iloc[::-1], hide_index=True, use_container_width=True)
        else:
            st.info("No records found for this group.")

if __name__ == '__main__':
    main()
