import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from hlc_parser import parse_log

from views.parcel_search import parcel_search_view
from views.all_parcels import all_parcels_view

st.set_page_config(page_title="Vanderlande Parcel Dashboard", layout="wide")
st.title("📦 Vanderlande Parcel Dashboard")

uploaded = st.file_uploader("Upload raw Log File in .txt format", type="txt")

if not uploaded:
    st.info("Upload Raw Log file.")
    st.stop()

text = uploaded.read().decode("utf-8")
with st.spinner("Parsing log…"):
    lifecycles = parse_log(text)
    df = pd.DataFrame(lifecycles)

# ── Metrics ─────────────────────────────────────────────────────
total = len(df)
sorted_cnt = (df.lifeCycle.apply(lambda x: x["status"]) == "sorted").sum()
dereg_cnt  = (df.lifeCycle.apply(lambda x: x["status"]) == "deregistered").sum()
barcode_err= df.barcodeErr.sum()

def cycle_s(lc):
    if isinstance(lc["registeredAt"], str) and isinstance(lc["closedAt"], str):
        return (datetime.fromisoformat(lc["closedAt"]) -
                datetime.fromisoformat(lc["registeredAt"])).total_seconds()
    return None

cycle_vals = df.lifeCycle.map(cycle_s).dropna()
avg_cycle = sum(cycle_vals) / len(cycle_vals) if len(cycle_vals) else 0

# ── Fixed: Handle None values in timestamps ─────────────────────
registered_times = [
    datetime.fromisoformat(l["registeredAt"])
    for l in df.lifeCycle
    if isinstance(l["registeredAt"], str)
]

closed_or_registered_times = [
    datetime.fromisoformat(l["closedAt"]) if isinstance(l["closedAt"], str)
    else datetime.fromisoformat(l["registeredAt"]) if isinstance(l["registeredAt"], str)
    else None
    for l in df.lifeCycle
]
closed_or_registered_times = [dt for dt in closed_or_registered_times if dt]

if registered_times and closed_or_registered_times:
    first_ts = min(registered_times)
    last_ts = max(closed_or_registered_times)
    tph = total / ((last_ts - first_ts).total_seconds() / 3600 or 1)
else:
    tph = 0

# ── Dashboard Metrics ───────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Parcels", total)
    st.metric("% Sorted", f"{sorted_cnt / total * 100:.1f}%" if total else "0%")
with c2:
    st.metric("% Barcode Err", f"{barcode_err / total * 100:.1f}%" if total else "0%")
    st.metric("% Deregistered", f"{dereg_cnt / total * 100:.1f}%" if total else "0%")
with c3:
    st.metric("Avg Cycle (s)", f"{avg_cycle:.1f}")
    st.metric("Throughput (tph)", f"{tph:.1f}")

st.divider()

# ── Two Tabs Only ───────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔍 Parcel Search", "📦 All Parcels"])

with tab1:
    parcel_search_view(df)
with tab2:
    all_parcels_view(df)
