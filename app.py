# app.py — EquiCity AI (English UI, optional LLM analysis, integrated map)
# Structure: complaint analysis (top) -> willingness dashboard (bottom).
# The API key is entered in the sidebar at runtime and is NEVER stored
# in this file or committed to GitHub.

import streamlit as st
from ai_engine import analyse
from map_view import render_map

st.set_page_config(page_title="EquiCity AI", page_icon="\U0001F3D9")

st.title("\U0001F3D9 EquiCity AI — Iskandar Puteri")
st.markdown("### *Bridging the Digital Façade for Urban Justice*")

# --- Sidebar: optional AI key (free key from Google AI Studio) ---
with st.sidebar:
    st.markdown("**AI mode (optional)**")
    api_key = st.text_input("Gemini API key", type="password",
                            help="Leave empty to use transparent rule-based logic.")
    st.caption("Without a key, EquiCity runs its rule-based prototype logic. "
               "With a key, complaints are analysed by Gemini, grounded in the "
               "doctoral survey data below.")

# --- Complaint analysis ---
zone = st.selectbox("Select zone:", ["Medini (Core)", "Skudai / Gelang Patah (Periphery)"])
complaint = st.text_area("Describe the issue (e.g., potholes, unreliable buses, streetlights):")

if st.button("Analyse with EquiCity AI"):
    if complaint.strip():
        with st.spinner("Analysing complaint against the Just Smart Mobility framework..."):
            mode, answer = analyse(zone, complaint, api_key or None)
        st.subheader("Recommendation")
        st.caption(f"Mode: {mode}")
        st.write(answer)
        st.divider()
        st.caption("Framework: Just Smart Mobility (doctoral research, UTM, 2026)")
    else:
        st.warning("Please describe the issue first.")

# --- Willingness dashboard (real survey data, N=734) ---
st.divider()
render_map()
