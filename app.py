
import os
import json
import requests
import trafilatura
import streamlit as st
import folium
from streamlit_folium import st_folium
from bs4 import BeautifulSoup
import google.generativeai as genai
from urllib.parse import urlparse
from dotenv import load_dotenv

# --- Config ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")
# model = genai.GenerativeModel("gemini-1.5-pro")

# --- Helpers ---
def extract_article_text_from_url(url: str) -> str:
    """Fetch and extract the main article text from a URL using trafilatura."""
    try:
        html = requests.get(url, timeout=10).text
        text = trafilatura.extract(html)
        if not text:
            print("Could not extract article body with trafilatura")
            return ""
        return text
    except Exception as e:
        print(f"Error fetching article text: {e}")
        return ""

def extract_locations(article_text: str):    
    """
    Extract locations (city, state, country, landmark) from article text
    and generate a one- or two-sentence summary of events at each location.
    Returns a list of dicts with fields: name, type, confidence, summary.
    """
    prompt = f"""
    You are an assistant that extracts structured information from news text.

    Task:
    Identify all real-world locations mentioned (cities, states, countries, landmarks).
    For each location, provide:
    - name (string)
    - type (city, state, country, landmark, etc.)
    - confidence (float between 0.0 and 1.0)

    Confidence should reflect how certain you are that the text refers to this location specifically:
    - Very clear, unambiguous references → 0.9–1.0
    - Likely correct but could have alternatives (e.g., multiple cities with same name) → 0.6–0.89
    - Mention is vague or indirect → 0.3–0.59
    - Very uncertain → below 0.3

    - summary (1–2 sentences summarizing what the article says happened at that location)

    Rules:
    - Keep the summary concise (max 40 words).
    - If the article does not clearly describe events at a location, set summary to "No specific events described."
    - Return ONLY valid JSON (no extra commentary).
    - Do not include ```json, ``` or any other Markdown formatting.

    Input text:
    {article_text}
    """

    response = model.generate_content(prompt)

    raw = response.text.strip()

    # Strip possible markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.lower().startswith("json"):
            raw = raw[len("json"):].strip()
        raw = raw.strip("` \n")

    # Parse JSON safely
    try:
        print(raw)
        print('******************')
        locations = json.loads(raw)
        if not isinstance(locations, list):
            locations = locations.get("locations", 0)
            
        print(locations)
        return locations
    except Exception as e:
        print("Error parsing Gemini response:", e)
        print("Raw response:", raw)
        return []


def geocode_location(name: str):
    """Geocode a location name with OpenStreetMap Nominatim."""
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={name}&limit=1"
    res = requests.get(url, headers={"User-Agent": "planet-challenge"})
    data = res.json()
    if len(data) > 0:
        return {
            "name": name,
            "lat": float(data[0]["lat"]),
            "lon": float(data[0]["lon"]),
            "display_name": data[0]["display_name"],
        }
    return None

# --- Streamlit UI ---
st.set_page_config(page_title="News Location Mapper", layout="wide")
st.title("🌍 NewsMap - News Article Location Mapper")

url_input = st.text_input("Paste a news article URL:")
text_input = st.text_area("Or paste article text here:")

if st.button("Extract & Map Locations"):
    with st.spinner("Processing..."):
        # 1. Get text (from URL or textarea)
        article_text = text_input
        if url_input and not text_input:
            article_text = extract_article_text_from_url(url_input)

        if not article_text or len(article_text) < 50:
            st.error("No valid article text found")
        else:
            # 2. Extract locations with Gemini
            locations = extract_locations(article_text)

            # Filter out low-confidence results
            filtered = [loc for loc in locations if loc.get("confidence", 0) >= 0.90]

            if not filtered:
                st.warning("No high-confidence locations found (≥ 0.90).")
            else:
                # 3. Geocode unique location names
                unique_names = {loc["name"] for loc in filtered}
                geocoded = [
                    geocode_location(name) for name in unique_names
                ]
                geocoded = [g for g in geocoded if g]

                # 4. Plot on map
                if geocoded:
                    # --- Initialize map ---
                    if len(geocoded) == 1:
                        loc = geocoded[0]
                        m = folium.Map(
                            location=[loc["lat"], loc["lon"]],
                            zoom_start=7,
                            crs="EPSG3857",
                            tiles=None  # Start with no default tiles
                        )
                    else:
                        # Multiple locations → initialize with rough center
                        avg_lat = sum(loc["lat"] for loc in geocoded) / len(geocoded)
                        avg_lon = sum(loc["lon"] for loc in geocoded) / len(geocoded)
                        m = folium.Map(
                            location=[avg_lat, avg_lon],
                            zoom_start=2,
                            crs="EPSG3857",
                            tiles=None  # Start with no default tiles
                        )

                    # Add clean Carto Light tiles (English labels, minimal water borders)
                    folium.TileLayer(
                        tiles='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>',
                        name='Light',
                        subdomains='abcd',
                        max_zoom=20
                    ).add_to(m)

                    # --- Add markers ---
                    for loc in geocoded:
                        # Match with filtered + disambiguated data
                        match = next((l for l in filtered if l["name"] == loc["name"]), None)
                        if not match:
                            continue

                        folium.Marker(
                            [loc["lat"], loc["lon"]],
                            icon=folium.Icon(icon="newspaper", prefix="fa", color="blue"),
                            popup=folium.Popup(
                                f"<b>{match['name']}</b><br>"
                                f"Confidence: {match['confidence']}<br>"
                                f"{match['summary']}",
                                max_width=300,
                            ),
                        ).add_to(m)

                    # --- Adjust map view for multiple locations ---
                    if len(geocoded) > 1:
                        lats = [loc["lat"] for loc in geocoded]
                        lons = [loc["lon"] for loc in geocoded]

                        lat_min, lat_max = min(lats), max(lats)
                        lon_min, lon_max = min(lons), max(lons)

                        # Small margin (~3%)
                        lat_margin = (lat_max - lat_min) * 0.03
                        lon_margin = (lon_max - lon_min) * 0.03

                        bounds = [
                            [lat_min - lat_margin, lon_min - lon_margin],
                            [lat_max + lat_margin, lon_max + lon_margin]
                        ]
                        m.fit_bounds(bounds)

                    # --- Render map in Streamlit ---
                    map_output = st_folium(m, height=500, use_container_width=True, returned_objects=[])
                else:
                    st.warning("No locations found.")

