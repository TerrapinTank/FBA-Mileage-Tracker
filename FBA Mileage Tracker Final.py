import streamlit as st
import pandas as pd
import datetime
import json
import os
import altair as alt

# --- UI Setup ---
st.set_page_config(page_title="FBA Mileage Tracker", layout="wide", page_icon="🚚")

# --- USER INITIALIZATION & PERSISTENCE ---
st.title("📦 Amazon FBA: Mileage Tracker")

# 1. Check if User ID is in the URL (so it remembers the user)
query_params = st.query_params
default_user = query_params.get("user", "Default_User")

# 2. User ID Input
user_id_input = st.text_input("Enter your unique User ID:", value=default_user).strip().lower().replace(" ", "_")

# 3. Update the URL so they can bookmark it
st.query_params["user"] = user_id_input

# --- PERSISTENCE BANNER ---
st.info(f"✨ **Persistence Active:** To automatically load your data next time, **bookmark this page now**. "
        f"Your unique URL contains your ID (`?user={user_id_input}`), so you won't have to re-type it later!")

# Dynamic File paths based on User ID
LOG_FILE = f"{user_id_input}_mileage_log.csv"
ROUTES_FILE = f"{user_id_input}_premade_routes.json"

# --- Data Initialization ---
def init_files():
    if not os.path.exists(ROUTES_FILE):
        with open(ROUTES_FILE, "w") as f:
            json.dump({"House -> UPS -> PO -> Home": 8.5}, f)
    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=["Date", "Trip Name", "Miles", "Purpose", "Type"]).to_csv(LOG_FILE, index=False)

init_files()

def load_routes():
    with open(ROUTES_FILE, "r") as f:
        return json.load(f)

def save_routes(routes):
    with open(ROUTES_FILE, "w") as f:
        json.dump(routes, f)

# --- DONATION BANNER ---
st.success("🙏 **Enjoying the tool?** Support development by sending donations to Venmo: **@TEST-VENMO6**")

# --- CUSTOM BUTTON NAVIGATION ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🛣️ Log Mileage"

nav_col1, nav_col2, nav_col3 = st.columns(3)

if nav_col1.button("🛣️ Log Mileage", use_container_width=True):
    st.session_state.current_page = "🛣️ Log Mileage"
if nav_col2.button("📍 Manage Routes", use_container_width=True):
    st.session_state.current_page = "📍 Manage Routes"
if nav_col3.button("📊 Audit History", use_container_width=True):
    st.session_state.current_page = "📊 Audit History"

st.divider()

# --- PAGE LOGIC ---

# 1. LOG MILEAGE
if st.session_state.current_page == "🛣️ Log Mileage":
    st.header(f"Record Trip for: {user_id_input.upper()}")
    col1, col2 = st.columns(2)
    
    with col1:
        m_date = st.date_input("Trip Date", datetime.date.today())
        m_type = st.radio("Trip Category", ["Premade Route", "Custom Trip"])
        
    with col2:
        premade_routes = load_routes()
        if m_type == "Premade Route":
            if not premade_routes:
                st.warning("No routes saved. Go to 'Manage Routes' to add one.")
            else:
                route_sel = st.selectbox("Select Route", list(premade_routes.keys()))
                m_miles = premade_routes[route_sel]
                m_purpose = st.text_input("Purpose", value="FBA Inventory Drop-off")
                m_name = route_sel
        else:
            m_name = st.text_input("Trip Name", placeholder="e.g., Estate Sale Sourcing")
            m_miles = st.number_input("Total Miles", min_value=0.1, step=0.1)
            m_purpose = st.text_input("Purpose", placeholder="e.g., Sourcing Inventory")

    if st.button("Save Trip", use_container_width=True):
        new_trip = pd.DataFrame([[m_date, m_name, m_miles, m_purpose, m_type]], 
                                columns=["Date", "Trip Name", "Miles", "Purpose", "Type"])
        new_trip.to_csv(LOG_FILE, mode='a', header=False, index=False)
        st.success(f"Logged {m_miles} miles to {user_id_input}'s file!")

# 2. MANAGE ROUTES
elif st.session_state.current_page == "📍 Manage Routes":
    st.header(f"Routes for: {user_id_input.upper()}")
    
    with st.expander("➕ Add New Route"):
        nr_name = st.text_input("Route Name (e.g. House to UPS)")
        nr_miles = st.number_input("Miles", min_value=0.0, step=0.1, key="nr_miles")
        if st.button("Save New Route"):
            routes = load_routes()
            routes[nr_name] = nr_miles
            save_routes(routes)
            st.rerun()

    st.subheader("Current Saved Routes")
    routes = load_routes()
    for name, dist in list(routes.items()):
        c1, c2 = st.columns([0.8, 0.2])
        c1.write(f"📍 **{name}**: {dist} miles")
        if c2.button("Delete", key=f"del_{name}"):
            del routes[name]
            save_routes(routes)
            st.rerun()

# 3. AUDIT HISTORY
elif st.session_state.current_page == "📊 Audit History":
    st.header(f"Audit Log for: {user_id_input.upper()}")
    
    m_data = pd.read_csv(LOG_FILE)
    m_data['Date'] = pd.to_datetime(m_data['Date'])
    
    if not m_data.empty:
        # --- Date Range Search ---
        st.subheader("🔍 Date Range Search")
        min_date = m_data['Date'].min().date()
        max_date = m_data['Date'].max().date()
        
        date_range = st.date_input(
            "Select range to filter table and dashboard:",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
            m_filtered = m_data[(m_data['Date'].dt.date >= start_date) & (m_data['Date'].dt.date <= end_date)]
        else:
            m_filtered = m_data

        # --- High Level Metrics ---
        current_year = datetime.date.today().year
        irs_rate = 0.67
        ytd_miles = m_data[m_data['Date'].dt.year == current_year]["Miles"].sum()
        ytd_deduction = ytd_miles * irs_rate
        
        total_m_filtered = m_filtered["Miles"].sum()
        est_deduction_filtered = total_m_filtered * irs_rate
        
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Filtered Miles", f"{total_m_filtered:,.1f}")
        col_b.metric("Filtered Deduction", f"${est_deduction_filtered:,.2f}")
        col_c.metric(f"YTD Miles ({current_year})", f"{ytd_miles:,.1f}")

        st.divider()

        # --- Visual Representations ---
        st.subheader("📈 Visual Analytics")
        m_viz = m_data.copy()
        m_viz['Month_Year_Label'] = m_viz['Date'].dt.strftime('%b %Y')
        m_viz['Month_Sort'] = m_viz['Date'].dt.to_period('M').astype(str)
        m_viz['Deduction'] = m_viz['Miles'] * irs_rate
        
        monthly_chart_data = (
            m_viz.groupby(['Month_Sort', 'Month_Year_Label'])[['Miles', 'Deduction']]
            .sum()
            .reset_index()
            .sort_values('Month_Sort')
        )
        
        viz_col1, viz_col2 = st.columns(2)
        with viz_col1:
            st.write("**Miles Driven per Month**")
            mile_chart = alt.Chart(monthly_chart_data).mark_bar().encode(
                x=alt.X('Month_Year_Label:N', sort=alt.SortField('Month_Sort'), title='Month'),
                y='Miles:Q',
                tooltip=[
                    alt.Tooltip('Month_Year_Label', title='Month'), 
                    alt.Tooltip('Miles', title='Miles', format='.1f')
                ]
            ).interactive()
            st.altair_chart(mile_chart, use_container_width=True)
            
        with viz_col2:
            st.write("**IRS Deduction ($) per Month**")
            deduction_chart = alt.Chart(monthly_chart_data).mark_bar(color='#28a745').encode(
                x=alt.X('Month_Year_Label:N', sort=alt.SortField('Month_Sort'), title='Month'),
                y=alt.Y('Deduction:Q', title='Deduction ($)'),
                tooltip=[
                    alt.Tooltip('Month_Year_Label', title='Month'), 
                    alt.Tooltip('Deduction', title='Deduction', format='$.2f')
                ]
            ).interactive()
            st.altair_chart(deduction_chart, use_container_width=True)
            
            st.markdown(f"### 💰 Total YTD Deduction: `${ytd_deduction:,.2f}`")

        st.divider()

        # --- Detailed Log ---
        st.subheader("📋 Detailed Log")
        m_display = m_filtered.sort_values("Date", ascending=False).copy()
        m_display['Date'] = m_display['Date'].dt.strftime('%B %d, %Y')
        st.dataframe(m_display, use_container_width=True)

        st.download_button("Export CSV", m_filtered.to_csv(index=False), "audit_log.csv")
    else:
        st.info(f"No trips logged yet for {user_id_input}.")