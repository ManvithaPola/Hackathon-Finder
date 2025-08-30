import streamlit as st
import pandas as pd
from datetime import datetime

# --- Load dataset ---
df = pd.read_csv("hackathons_final.csv")

# Ensure proper datetime
df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month_name()
df["DaysLeft"] = (df["Date"] - datetime.now()).dt.days
df["Mode"] = df["Mode"].fillna("Unknown")

# --- Page config ---
st.set_page_config(page_title="Hackathon Dashboard", layout="wide")
st.title("🚀 Hackathon Dashboard")

# --- Sidebar Filters ---
st.sidebar.header("Filters")

# Sources: all 5 websites
all_sources = ["Devpost", "MLH", "Hackathon.com", "Eventbrite", "AngelHack"]
selected_sources = st.sidebar.multiselect(
    "Select Sources", options=all_sources, default=all_sources
)

# Mode: Online, Offline, Unknown
all_modes = ["Online", "Offline", "Unknown"]
selected_modes = st.sidebar.multiselect(
    "Select Mode", options=all_modes, default=all_modes
)

# Year filter
years = sorted(df["Year"].dropna().unique())
selected_years = st.sidebar.multiselect("Select Year", options=years, default=years)

# Month filter
months = df["Month"].dropna().unique().tolist()
selected_months = st.sidebar.multiselect("Select Month", options=months, default=months)

# --- Apply filters ---
filtered = df[
    (df["Source"].isin(selected_sources)) &
    (df["Mode"].isin(selected_modes)) &
    (df["Year"].isin(selected_years)) &
    (df["Month"].isin(selected_months))
].sort_values("Date")

# --- Table with clickable links ---
st.subheader(f"📅 Upcoming Hackathons ({len(filtered)})")

# Create a copy to safely modify Link column
table = filtered[["Title", "Date", "Location", "Mode", "Source", "Link"]].copy()
table["Link"] = table["Link"].apply(lambda x: f"[Open Link]({x})")

# Render HTML table with clickable links
st.markdown(table.to_html(escape=False, index=False), unsafe_allow_html=True)

# Display last updated timestamp
if "ScrapedAt" in df.columns:
    last_update = pd.to_datetime(df["ScrapedAt"].max(), errors="coerce")
    if pd.notna(last_update):
        st.markdown(f"**Last Updated:** {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
