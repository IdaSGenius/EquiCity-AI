"""
mbip_layers.py — MBIP OneMap (ArcGIS REST) integration for EquiCity-AI
=======================================================================
Pulls official Majlis Bandaraya Iskandar Puteri geospatial layers:

  1. Gunatanah Semasa (current land use, parcel-level, 12 classes)
  2. Sempadan Warta MBIP (gazetted municipal boundary)
  3. Sempadan Taman (residential neighbourhood boundaries)
  4. Zon Ahli Majlis (councillor zone boundaries)

Design principles
-----------------
- Land-use layer has ~10k+ parcels and MaxRecordCount=1000, so we DO NOT
  download parcel geometry wholesale. Instead:
    * server-side statistics (sum of hectares grouped by mukim x land-use
      class) -> a small tidy DataFrame, no geometry transfer
    * boundary layers (few features each) fetched fully as GeoJSON
    * optional parcel fetch is filtered (per-mukim / per-class) and capped
- Everything cached (st.cache_data) + optional disk snapshot so the demo
  survives a slow/offline government server on showcase day.
- Field names verified against the live service metadata on 13 Aug 2026.
  If MBIP restructures the service, discover_layer() re-reads metadata.

Usage in your Streamlit app:
    from mbip_layers import (landuse_by_mukim, get_boundary_geojson,
                             boundary_pydeck_layer, MBIP_SERVICES)
"""

from __future__ import annotations
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests

try:
    import streamlit as st
    _cache = st.cache_data(ttl=24 * 3600, show_spinner=False)
except Exception:                       # allows CLI use outside Streamlit
    def _cache(fn):
        return fn

BASE = "https://onemap.mbip.gov.my/arcgis/rest/services/MBIP"

MBIP_SERVICES = {
    "gunatanah":      f"{BASE}/GTSemasa/MapServer",
    "sempadan_mbip":  f"{BASE}/Sempadan_Warta/MapServer",
    "sempadan_taman": f"{BASE}/Sempadan_Taman/MapServer",
    "zon_ahli_majlis": f"{BASE}/Zon_AM/MapServer",
}

SNAPSHOT_DIR = Path(__file__).parent / "data" / "mbip_snapshot"
TIMEOUT = 30
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "EquiCity-AI/1.0 (research; UTM)"})


# ---------------------------------------------------------------- helpers
def _get_json(url: str, params: dict) -> dict:
    params = {**params, "f": params.get("f", "json")}
    r = SESSION.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(f"ArcGIS error from {url}: {data['error']}")
    return data


@_cache
def discover_layer(service_url: str) -> int:
    """Return the id of the first layer in a MapServer (metadata-driven,
    so the code keeps working if MBIP renames/reorders layers)."""
    meta = _get_json(service_url, {})
    layers = meta.get("layers") or []
    if not layers:
        raise RuntimeError(f"No layers published at {service_url}")
    return layers[0]["id"]


@_cache
def field_domain_map(service_url: str, field_name: str) -> dict:
    """Build code->name mapping from a field's coded-value domain
    (e.g. mukim_id 010201 -> JELUTONG) straight from service metadata,
    so nothing is hard-coded or guessed."""
    lid = discover_layer(service_url)
    meta = _get_json(f"{service_url}/{lid}", {})
    for f in meta.get("fields", []):
        if f["name"] == field_name and f.get("domain", {}).get("codedValues"):
            return {cv["code"]: cv["name"] for cv in f["domain"]["codedValues"]}
    return {}


# ------------------------------------------------- 1) land-use statistics
@_cache
def landuse_by_mukim() -> pd.DataFrame:
    """Official land-use composition per mukim: total hectares grouped by
    (mukim, land-use class). Server-side aggregation — fast, no geometry.

    Returns columns: mukim_code, mukim, landuse, hectares, pct_of_mukim
    """
    svc = MBIP_SERVICES["gunatanah"]
    lid = discover_layer(svc)
    stats = [{
        "statisticType": "sum",
        "onStatisticField": "luas_h",
        "outStatisticFieldName": "hectares",
    }]
    data = _get_json(f"{svc}/{lid}/query", {
        "where": "1=1",
        "groupByFieldsForStatistics": "mukim_id,gtn1",
        "outStatistics": json.dumps(stats),
        "returnGeometry": "false",
    })
    rows = [feat["attributes"] for feat in data.get("features", [])]
    df = pd.DataFrame(rows).rename(columns={"mukim_id": "mukim_code",
                                            "gtn1": "landuse"})
    if df.empty:
        return df
    mukim_names = field_domain_map(svc, "mukim_id")
    df["mukim"] = df["mukim_code"].map(mukim_names).fillna(df["mukim_code"])
    df["hectares"] = pd.to_numeric(df["hectares"], errors="coerce")
    df = df.dropna(subset=["hectares"])
    totals = df.groupby("mukim")["hectares"].transform("sum")
    df["pct_of_mukim"] = (df["hectares"] / totals * 100).round(2)
    return df.sort_values(["mukim", "hectares"], ascending=[True, False])


# ------------------------------------------------- 2) boundary GeoJSON
def _snapshot_path(name: str) -> Path:
    return SNAPSHOT_DIR / f"{name}.geojson"


@_cache
def get_boundary_geojson(name: str, out_fields: str = "*") -> dict:
    """Fetch a full boundary layer as GeoJSON in WGS84 (EPSG:4326), with
    resultOffset pagination and a disk-snapshot fallback for demo day.
    Valid names: sempadan_mbip, sempadan_taman, zon_ahli_majlis.
    """
    svc = MBIP_SERVICES[name]
    try:
        lid = discover_layer(svc)
        features, offset = [], 0
        while True:
            data = _get_json(f"{svc}/{lid}/query", {
                "where": "1=1",
                "outFields": out_fields,
                "returnGeometry": "true",
                "outSR": 4326,
                "resultOffset": offset,
                "resultRecordCount": 1000,
                "f": "geojson",
            })
            batch = data.get("features", [])
            features.extend(batch)
            if len(batch) < 1000:
                break
            offset += 1000
        gj = {"type": "FeatureCollection", "features": features}
        # refresh snapshot for offline fallback
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        _snapshot_path(name).write_text(json.dumps(gj))
        return gj
    except Exception as exc:
        snap = _snapshot_path(name)
        if snap.exists():
            return json.loads(snap.read_text())
        raise RuntimeError(
            f"MBIP OneMap unreachable and no local snapshot for '{name}'. "
            f"Run `python mbip_layers.py --snapshot` while online. ({exc})"
        )


# ------------------------------------- 3) filtered parcel fetch (optional)
@_cache
def get_parcels(mukim_code: str | None = None,
                landuse: str | None = None,
                cap: int = 1500) -> dict:
    """Fetch a FILTERED subset of land-use parcels as GeoJSON. Never call
    without a filter in production — the full layer is too large for a
    Streamlit session. Example: get_parcels(landuse='TANAH LAPANG DAN REKREASI')
    """
    svc = MBIP_SERVICES["gunatanah"]
    lid = discover_layer(svc)
    clauses = []
    if mukim_code:
        clauses.append(f"mukim_id='{mukim_code}'")
    if landuse:
        clauses.append(f"gtn1='{landuse}'")
    where = " AND ".join(clauses) if clauses else "1=1"
    features, offset = [], 0
    while len(features) < cap:
        data = _get_json(f"{svc}/{lid}/query", {
            "where": where,
            "outFields": "gtn1,gtn3,mukim_id,luas_h,nama_tmn,status_sem",
            "returnGeometry": "true",
            "outSR": 4326,
            "geometryPrecision": 5,
            "resultOffset": offset,
            "resultRecordCount": min(1000, cap - len(features)),
            "f": "geojson",
        })
        batch = data.get("features", [])
        features.extend(batch)
        if len(batch) < 1000:
            break
        offset += 1000
    return {"type": "FeatureCollection", "features": features}


# ------------------------------------------------- 4) pydeck convenience
def boundary_pydeck_layer(name: str, rgba=(255, 255, 255, 200), width=2):
    """Outline-only pydeck GeoJsonLayer for a boundary service."""
    import pydeck as pdk
    return pdk.Layer(
        "GeoJsonLayer",
        data=get_boundary_geojson(name),
        stroked=True,
        filled=False,
        get_line_color=list(rgba),
        line_width_min_pixels=width,
        pickable=True,
    )


# ------------------------------------------------------------- CLI
if __name__ == "__main__":
    import sys
    if "--snapshot" in sys.argv:
        for key in ("sempadan_mbip", "sempadan_taman", "zon_ahli_majlis"):
            gj = get_boundary_geojson(key)
            print(f"{key}: {len(gj['features'])} features -> "
                  f"{_snapshot_path(key)}")
        df = landuse_by_mukim()
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        df.to_csv(SNAPSHOT_DIR / "landuse_by_mukim.csv", index=False)
        print(f"landuse_by_mukim: {len(df)} rows -> landuse_by_mukim.csv")
    else:
        print(landuse_by_mukim().head(20).to_string())

