# ai_engine.py — Complaint analysis engine for EquiCity AI
# Two modes:
#   1) LLM mode  — Google Gemini API, if the user supplies an API key
#   2) Rule mode — transparent rule-based fallback (no key needed)
# The prompt grounds the LLM in REAL survey statistics loaded from data/,
# so answers reflect the doctoral fieldwork rather than generic text.
#
# NOTE: verify the Gemini endpoint/model name against current Google docs
# (ai.google.dev) — API details can change. Never hardcode or commit a key.

import json
import pandas as pd
import requests

GEMINI_URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
              "gemini-1.5-flash:generateContent")

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

def rule_based(zone: str, complaint: str) -> str:
    """Transparent rule-based prototype logic (Just Smart Mobility framework)."""
    if "Periphery" in zone:
        return (f"**Rule-based recommendation (prototype).** Complaint: '{complaint}' "
                f"in **{zone}**.\n\nUnder the *infrastructural justice* principle, "
                "digital-layer investment should be **deferred**: budget priority goes "
                "to foundational fixes first (road resurfacing, public transport "
                "reliability). Residents in peripheral zones resist a 'digital façade'; "
                "they need functioning basics first.")
    return (f"**Rule-based recommendation (prototype).** Complaint: '{complaint}' "
            f"in **{zone}**.\n\nFoundational infrastructure in this zone is mature, "
            "so EquiCity recommends higher-order smart optimisation (e.g., AI parking "
            "management, IoT safety monitoring) alongside routine maintenance.")

def llm_analysis(zone: str, complaint: str, api_key: str) -> str:
    """Ask Gemini for an equity-weighted analysis, grounded in survey data."""
    prompt = f"""You are EquiCity AI, a spatial decision-support engine for
Iskandar Puteri, Malaysia, built on the 'Just Smart Mobility' framework from
doctoral research. Core principle: in PERIPHERY zones, prioritise foundational
infrastructure (roads, transit, safety) BEFORE any digital/smart-city layer;
in CORE zones with mature infrastructure, higher-order digital interventions
are appropriate.

Real doctoral survey findings (N=734, community willingness by mukim):
{survey_context()}

Current policy context (source: MBIP public announcement via official
Facebook, 2026 — user should verify current status): MBIP, via contractor
Southmax Sdn. Bhd., is upgrading 39 junctions in Medini (core zone) with the
TrafficSens smart traffic-light system; 30 upgraded, integration with the
Iskandar Puteri Command Centre (IPCC) was expected by end-April 2026. Note
the core-periphery pattern: smart-mobility investment is concentrating in
Medini while survey data documents foundational infrastructure concerns in
peripheral zones.

Resident complaint: "{complaint}"
Zone: {zone}

In under 150 words, in English: (1) classify the complaint (foundational vs
digital-layer), (2) recommend a budget-priority action consistent with the
framework, (3) reference the survey evidence where relevant. Be concrete and
policy-oriented. Do not invent statistics beyond those provided."""
    resp = requests.post(
        GEMINI_URL,
        params={"key": api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]

def analyse(zone: str, complaint: str, api_key: str | None) -> tuple[str, str]:
    """Returns (mode_label, answer). Falls back to rules if no key or API error."""
    if api_key:
        try:
            return "Gemini AI analysis (grounded in survey data)", llm_analysis(zone, complaint, api_key)
        except Exception as e:
            return (f"Rule-based fallback (AI call failed: {type(e).__name__})",
                    rule_based(zone, complaint))
    return "Rule-based prototype logic (no API key provided)", rule_based(zone, complaint)
