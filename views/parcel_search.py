import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

def parcel_search_view(df):
    search_mode = st.radio("Search by", ["Host ID", "Barcode"], horizontal=True)
    search_input = st.text_input(f"Enter {search_mode}")
    if not search_input:
        return

    try:
        if search_mode == "Host ID":
            result = df[df.hostId == search_input]
        elif search_mode == "Barcode":
            result = df[df.barcodes.apply(lambda barcodes: search_input in (barcodes or []))]

        if result.empty:
            st.warning(f"{search_mode} not found.")
            return

        for idx, parcel in result.iterrows():
            volume = parcel.volume_data or {}

            volume_info = {
                "Length (cm)": volume.get("length") or "—",
                "Width (cm)": volume.get("width") or "—",
                "Height (cm)": volume.get("height") or "—",
                "Box Volume (cm³)": volume.get("box_volume") or "—",
                "Real Volume (cm³)": volume.get("real_volume") or "—"
            }

            parcel_summary = {
                "PIC": parcel.pic,
                "Host ID": parcel.hostId,
                "Barcodes": parcel.barcodes,
                "Location": parcel.location,
                "Destination": parcel.destination,
                "Volume Data": volume_info,
                "Lifecycle": parcel.lifeCycle,
                "Barcode Error": parcel.barcodeErr,
            }

            st.subheader("📦 Parcel Information")
            st.json(parcel_summary)

            # ── Event timeline ──
            ev = pd.DataFrame(parcel.events)

            if not ev.empty:
                ev = ev[ev["type"] != "Lifecycle"]
                ev["ts"] = pd.to_datetime(ev.ts)
                ev = ev.sort_values("ts")

                closed_at = parcel.lifeCycle.get("closedAt")
                close_time = pd.to_datetime(closed_at) if closed_at else ev["ts"].iloc[-1]

                # Updated logic to add small duration to last event
                buffer_sec = 2
                ev["finish"] = ev["ts"].shift(-1)
                ev["finish"] = ev["finish"].fillna(ev["ts"] + pd.Timedelta(seconds=buffer_sec))
                ev["duration_s"] = (ev["finish"] - ev["ts"]).dt.total_seconds().clip(lower=0)

                ev["time"] = ev["ts"].dt.strftime("%H:%M:%S")

                st.subheader("📋 Event Log")
                st.dataframe(
                    ev[["time", "type", "duration_s"]].rename(columns={
                        "time": "Time",
                        "type": "Type",
                        "duration_s": "Duration (s)"
                    }),
                    use_container_width=True,
                    hide_index=True,
                )

                fig = px.timeline(
                    ev,
                    x_start="ts",
                    x_end="finish",
                    y=["Parcel"] * len(ev),
                    color="type",
                    hover_data=["type", "ts", "duration_s"]
                )
                fig.update_layout(
                    title="Parcel Event Timeline",
                    xaxis_title="Time",
                    yaxis_title="",
                    height=300,
                    showlegend=True
                )
                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
