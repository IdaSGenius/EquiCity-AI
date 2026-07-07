# map_view.py — Community Willingness Map for EquiCity AI
# Reference implementation prepared with assistance; read the comments,
# adapt, and be able to explain every block before committing.
#
# Data (./data/): willingness_points.csv, mukim_willingness.geojson,
#                 mbip_boundary.geojson, expressway.geojson, railway.geojson
# Survey: doctoral fieldwork, Iskandar Puteri, N=734 (61 places, 4 mukims).
# Transport context layers derived from OpenStreetMap (© OSM contributors).

import json
import pandas as pd
import pydeck as pdk
import streamlit as st

INDICATORS = {
    "Participate in Smart City Initiatives": "participate",
    "Attend Smart City Meetings": "attend",
    "Volunteer for Smart City Initiatives": "volunteer",
    "Financially Support Smart City": "financial",
    "Belief in Citizen Participation": "belief",
}

@st.cache_data
def load(path, is_json=True):
    if is_json:
        with open(path) as f:
            return json.load(f)
    return pd.read_csv(path)

def render_map():
    st.subheader("Community Willingness Across Iskandar Puteri (Survey N=734)")

    pts = load("data/willingness_points.csv", is_json=False)
    mukims = load("data/mukim_willingness.geojson")
    boundary = load("data/mbip_boundary.geojson")

    c1, c2 = st.columns([2, 1])
    label = c1.selectbox("Indicator", list(INDICATORS))
    key = INDICATORS[label]
    show_transport = c2.checkbox("Transport context (OSM)", value=False)

    # --- Choropleth: mukim polygons coloured by % agreement ---
    # Colour computed here (not in pydeck expressions) for clarity:
    for feat in mukims["features"]:
        p = feat["properties"]
        v = p.get(f"pct_{key}")
        if v is None:                    # mukim with no survey responses
            p["fill"] = [200, 200, 200, 60]
            p["label_pct"] = "no data"
        else:                            # red (low) -> green (high)
            p["fill"] = [int(255 * (1 - v / 100)), int(190 * v / 100), 60, 120]
            p["label_pct"] = f"{v}%"
        p["label_n"] = p.get(f"n_{key}", 0)

    mukim_layer = pdk.Layer(
        "GeoJsonLayer", data=mukims, stroked=True, filled=True,
        get_fill_color="properties.fill",
        get_line_color=[90, 90, 90], line_width_min_pixels=1, pickable=True,
    )

    # --- Survey places: size = responses (sqrt so area tracks count) ---
    d = pts[pts["indicator"] == label].copy()
    d["radius"] = (d["Total"] ** 0.5) * 180
    d["r"] = (255 * (1 - d["pct_agree"] / 100)).astype(int)
    d["g"] = (200 * (d["pct_agree"] / 100)).astype(int)
    point_layer = pdk.Layer(
        "ScatterplotLayer", data=d, get_position="[lon, lat]",
        get_radius="radius", get_fill_color="[r, g, 60, 200]", pickable=True,
    )

    boundary_layer = pdk.Layer(
        "GeoJsonLayer", data=boundary, stroked=True, filled=False,
        get_line_color=[30, 30, 30], line_width_min_pixels=2,
    )

    layers = [mukim_layer, boundary_layer, point_layer]
    if show_transport:
        for f, colour in [("data/expressway.geojson", [120, 60, 160]),
                          ("data/railway.geojson", [40, 90, 200])]:
            layers.insert(1, pdk.Layer(
                "GeoJsonLayer", data=load(f), stroked=True, filled=False,
                get_line_color=colour, line_width_min_pixels=1,
            ))

    tooltip = {"html": "<b>{MUKIM}{PLACE}</b><br/>"
                       "Agreement: {label_pct}{pct_agree}<br/>"
                       "Responses: {label_n}{Total}"}

    st.pydeck_chart(pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(latitude=d["lat"].mean(),
                                         longitude=d["lon"].mean(), zoom=10.2),
        map_style=None, tooltip=tooltip,
    ))

    m1, m2, m3 = st.columns(3)
    m1.metric("Survey places", f"{d['PLACE'].nunique()}")
    m2.metric("Responses", f"{int(d['Total'].sum())}")
    m3.metric("Overall agreement",
              f"{(d['Agree'].sum() + d['Strongly_A'].sum()) / d['Total'].sum() * 100:.1f}%")
    st.caption("Mukim shading = share agreeing/strongly agreeing (grey = no responses). "
               "Points = surveyed places, sized by responses. "
               "Doctoral survey, Iskandar Puteri (2023-24); transport layers © OpenStreetMap contributors.")

# In app.py:  from map_view import render_map ; render_map()
# requirements.txt: streamlit, pandas, pydeck
