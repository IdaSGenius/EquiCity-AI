# app.py — EquiCity AI (English UI, optional LLM analysis, integrated map)
# Structure: complaint analysis (top) -> willingness dashboard (bottom).
# The API key is entered in the sidebar at runtime and is NEVER stored
# in this file or committed to GitHub.
import streamlit as st
from ai_engine import analyse
from map_view import render_map
from mbip_layers import available_zones

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
zone = st.selectbox("Select mukim:", available_zones())
complaint = st.text_area("Describe the issue (e.g., potholes, drainage/flooding, "
                          "park maintenance, unreliable buses, unsafe walkways, "
                          "land-use conflicts, waste collection):")

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

# --- Official MBIP OneMap boundary layers (added for MJIIX 2026) ---
import pydeck as pdk
from mbip_layers import get_boundary_geojson

st.divider()
st.subheader("🗺️ Official MBIP boundaries (OneMap)")
st.caption("Live from Majlis Bandaraya Iskandar Puteri's OneMap GIS portal.")

show_warta = st.checkbox("Show gazetted MBIP boundary", value=True)
show_zonam = st.checkbox("Show councillor zones (Zon Ahli Majlis)")

mbip_layers_list = []
try:
    if show_warta:
        mbip_layers_list.append(pdk.Layer(
            "GeoJsonLayer",
            data=get_boundary_geojson("sempadan_mbip"),
            stroked=True, filled=False,
            get_line_color=[255, 215, 0, 230],
            line_width_min_pixels=3,
        ))
    if show_zonam:
        mbip_layers_list.append(pdk.Layer(
            "GeoJsonLayer",
            data=get_boundary_geojson("zon_ahli_majlis"),
            stroked=True, filled=False,
            get_line_color=[0, 200, 255, 200],
            line_width_min_pixels=2,
        ))
    if mbip_layers_list:
        st.pydeck_chart(pdk.Deck(
            layers=mbip_layers_list,
            initial_view_state=pdk.ViewState(
                latitude=1.45, longitude=103.63, zoom=10.5, pitch=0,
            ),
            map_style=None,
        ))
except Exception as e:
    st.warning(f"MBIP OneMap layer unavailable right now: {e}")
