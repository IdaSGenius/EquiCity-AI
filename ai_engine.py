# ai_engine.py — Complaint analysis engine for EquiCity AI
# Two modes:
#   1) LLM mode  — Google Gemini API, if the user supplies an API key
#   2) Rule mode — transparent rule-based fallback (no key needed)
# The prompt grounds the LLM in REAL survey statistics loaded from data/,
# so answers reflect the doctoral fieldwork rather than generic text.
#
# NOTE: verify model names against current Google docs (ai.google.dev) —
# API details can change. Never hardcode or commit a key.
#
# CHANGELOG (13 Aug 2026):
# - Removed unverified traffic-light rollout figures (junction counts,
#   completion date) from the LLM prompt — could not be confirmed via
#   web search and should not be sent to the model as fact. The system
#   itself (TrafficSens, operated by Southmax Sdn Bhd) IS confirmed real;
#   only the specific numbers were unverifiable.
# - Replaced the "Periphery" substring match (broke as soon as the zone
#   dropdown moved to real mukim names) with a lookup against each
#   mukim's actual survey participation rate vs the citywide average.
# - Prompt now explicitly asks for planning-register vocabulary and a
#   broader complaint taxonomy, and instructs the model not to invent
#   numbers beyond what's provided.

import json
import pandas as pd
import requests

# Candidate model names, tried in order. Google retires model names over
# time, so if all fail, check current names at ai.google.dev and edit this list.
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
GEMINI_URL_TMPL = ("https://generativelanguage.googleapis.com/v1beta/models/"
                   "{model}:generateContent")

# EquiCity AI's actual study-area zones (Just Smart Mobility framework,
# doctoral research) — these are the real units the survey was built
# around. NOT the same as official government mukim boundaries, which
# include neighbouring local authorities (Kulai, Senai) outside MBIP.
STUDY_ZONES = ["Medini", "Skudai", "Gelang Patah", "Tanjung Kupang / Tanjung Pelepas"]


def _normalize(name: str) -> str:
    """Case/punctuation-tolerant key for matching zone names against
    survey data — e.g. 'Tanjung Kupang / Tanjung Pelepas' vs whatever
    exact spelling the geojson uses."""
    return " ".join(str(name).strip().upper().replace("/", " ").split())


def survey_context() -> str:
    """Build a short factual context block from the real survey data,
    so the LLM's answer is grounded in the doctoral fieldwork."""
    with open("data/mukim_willingness.geojson") as f:
        gj = json.load(f)
    lines = []
    for feat in gj["features"]:
        p = feat["properties"]
        if p.get("n_participate"):
            lines.append(
                f"- Mukim {p['MUKIM']}: participate {p.get('pct_participate')}%, "
                f"attend meetings {p.get('pct_attend')}%, "
                f"volunteer {p.get('pct_volunteer')}%, "
                f"financially support {p.get('pct_financial')}% "
                f"(n={p['n_participate']})"
            )
    return "\n".join(lines)


def _mukim_stats():
    """Load per-mukim survey stats keyed by a normalized zone name
    (tolerant of case/punctuation differences), plus the citywide
    average participation rate."""
    with open("data/mukim_willingness.geojson") as f:
        gj = json.load(f)
    stats, values = {}, []
    for feat in gj["features"]:
        p = feat["properties"]
        if p.get("n_participate"):
            stats[_normalize(p["MUKIM"])] = p
            if p.get("pct_participate") is not None:
                values.append(p["pct_participate"])
    citywide_avg = sum(values) / len(values) if values else None
    return stats, citywide_avg


def _find_stats(stats: dict, zone: str):
    """Match a zone name against survey MUKIM keys. Tries an exact
    normalized match first, then falls back to substring matching so
    e.g. 'Tanjung Kupang / Tanjung Pelepas' still finds a record filed
    under just 'Tanjung Kupang'. Confirm your geojson's exact MUKIM
    values match STUDY_ZONES if this fallback keeps firing."""
    key = _normalize(zone)
    if key in stats:
        return stats[key]
    for k, v in stats.items():
        if k in key or key in k:
            return v
    return None


def rule_based(zone: str, complaint: str) -> str:
    """Transparent rule-based prototype logic. Compares this zone's real
    survey participation rate to the citywide average — no invented
    Core/Periphery label."""
    stats, citywide_avg = _mukim_stats()
    p = _find_stats(stats, zone)

    if not p or citywide_avg is None:
        return (f"**Rule-based recommendation (prototype).** Complaint: '{complaint}' "
                f"in **{zone}**.\n\nNo matching survey record was found for this zone, "
                "so no willingness-based recommendation can be given. Default guidance: "
                "assess foundational infrastructure condition before considering any "
                "digital-layer investment.")

    pct = p.get("pct_participate")
    if pct is not None and pct >= citywide_avg:
        comparison = f"above the citywide average ({pct}% vs {citywide_avg:.1f}%)"
        advice = ("higher-order smart-mobility optimisation (e.g., adaptive traffic "
                   "signals, IoT safety monitoring) alongside routine maintenance")
    else:
        comparison = (f"below the citywide average ({pct}% vs {citywide_avg:.1f}%)"
                     if pct is not None else "not available in the survey data")
        advice = ("foundational infrastructure fixes first (road condition, drainage, "
                   "public transport reliability, footpath continuity) before any "
                   "digital-layer investment")

    return (f"**Rule-based recommendation (prototype).** Complaint: '{complaint}' "
            f"in **{zone}**.\n\nCommunity willingness to participate in this mukim is "
            f"{comparison}. Under the *infrastructural justice* principle, EquiCity "
            f"recommends: {advice}.")


def llm_analysis(zone: str, complaint: str, api_key: str) -> str:
    """Ask Gemini for an equity-weighted analysis, grounded in survey data."""
    stats, _ = _mukim_stats()
    p = _find_stats(stats, zone)
    zone_line = (
        f"This zone (mukim {zone}): participate {p.get('pct_participate')}%, "
        f"attend meetings {p.get('pct_attend')}%, volunteer {p.get('pct_volunteer')}%, "
        f"financially support {p.get('pct_financial')}% (n={p['n_participate']})."
        if p else f"No survey record was found for mukim '{zone}' — do not invent "
                  f"figures for it; note the gap instead."
    )

    prompt = f"""You are EquiCity AI, a spatial decision-support tool for
Iskandar Puteri, Malaysia, grounded in doctoral urban and regional planning
research. Core principle (infrastructural justice): where community
willingness or infrastructure condition is low, foundational infrastructure
should be prioritised before any digital/smart-city layer; where it is high
and infrastructure is mature, higher-order digital interventions are
appropriate.

Real doctoral survey findings (N=734, community willingness by mukim):
{survey_context()}

{zone_line}

Known context (verified): MBIP operates a smart-mobility programme
(TrafficSens smart traffic-light system, delivered by Southmax Sdn Bhd, a
subsidiary of ITMAX System Bhd, under a long-term service contract) that is
being expanded across the Iskandar Puteri area, not confined to one zone.
Do NOT state specific junction counts, upgrade counts, or completion dates —
none are confirmed here.

Resident complaint: "{complaint}"
Zone (mukim): {zone}

Respond in English, under 180 words, using proper urban and regional
planning terminology where it genuinely applies (e.g. land-use
compatibility, infrastructure carrying capacity, public realm quality,
transit-oriented development, active mobility, stormwater/drainage
capacity, community facility provision) rather than generic phrasing.
Structure your answer as:
(1) Classify the complaint (e.g. foundational infrastructure / public
    realm / land-use conflict / environmental / digital-layer / governance)
    — do not default to "potholes/buses/streetlights" framing if the
    complaint is something else.
(2) Recommend a budget-priority action consistent with the infrastructural-
    justice principle above.
(3) Reference the survey evidence given above where relevant.
Do not cite any number, date, or statistic not given to you in this prompt."""

    last_err = None
    for model in GEMINI_MODELS:
        resp = requests.post(
            GEMINI_URL_TMPL.format(model=model),
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        if resp.ok:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        # keep the most informative error and try the next model name
        last_err = f"HTTP {resp.status_code} on {model}: {resp.text[:200]}"
    raise RuntimeError(last_err)


def analyse(zone: str, complaint: str, api_key: str | None) -> tuple[str, str]:
    """Returns (mode_label, answer). Falls back to rules if no key or API error."""
    if api_key:
        try:
            return ("Gemini AI analysis (grounded in survey data)",
                     llm_analysis(zone, complaint, api_key))
        except Exception as e:
            return (f"Rule-based fallback (AI call failed: {e})",
                    rule_based(zone, complaint))
    return "Rule-based prototype logic (no API key provided)", rule_based(zone, complaint)
