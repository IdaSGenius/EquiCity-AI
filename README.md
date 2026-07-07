# EquiCity AI: Bridging the Digital Façade in Urban Governance 🏙️

**Track:** Green Horizon (Smart Cities & Mobility)
**Solo Participant:** Ida Shaheera Bakhtiar
**Hackathon:** Project 2030: MyAI Future Hackathon by GDG On Campus UTM

## 📌 Project Overview

EquiCity AI is a spatial decision-making engine grounded in the **Just Smart Mobility** framework. It addresses a critical issue in urban planning: the **Digital Façade** — where cities deploy superficial smart applications while foundational infrastructure remains broken.

This prototype evaluates civic complaints through a geospatial lens, actively differentiating between **Core** economic zones and **Periphery** areas to prioritize municipal budget allocation and act as a fiscal safeguard for local authorities.

## 🚀 The Solution

Unlike conventional routing algorithms, EquiCity AI does not just process data — it processes **equity**.

- **Core Zones (e.g., Medini):** Recommends higher-order digital interventions when foundational infrastructure is already mature.
- **Periphery Zones (e.g., Skudai):** Prioritizes basic infrastructural fixes (e.g., potholes, public transport) before proposing any digital layer.

The app runs in transparent **rule-based mode by default**; supply a Gemini API key in the sidebar for AI-powered analysis grounded in the doctoral survey data.

## 🛠️ Tech Stack

- **Frontend & Logic:** Python, Streamlit
- **AI analysis (optional):** Google Gemini API, prompt-grounded in survey statistics
- **Geospatial visualisation:** pydeck choropleth and point map of doctoral survey data (N=734, 61 places, mukim-level aggregation); transport context layers © OpenStreetMap contributors
- **Core Framework:** Just Smart Mobility Model (academic research)

## 💻 How to Run Locally

1. Clone this repository:

```bash
git clone https://github.com/IdaSGenius/EquiCity-AI.git
```

2. Navigate to the project directory:

```bash
cd EquiCity-AI
```

3. Install required dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
py -m streamlit run app.py
```

(On macOS/Linux use `python -m streamlit run app.py`.)

## 👩‍🎓 Author

Ida Shaheera Bakhtiar — PhD candidate, Urban & Regional Planning (UTM). Research focus: smart-city governance, community acceptance, and spatial equity in Iskandar Malaysia.
