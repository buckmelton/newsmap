# 🌍 NewsMap - News Article Location Mapper

This project is a take-home coding challenge for Planet.com.  
It extracts locations (cities, states, countries, landmarks) from a news article using Google Gemini, geocodes them with OpenStreetMap, and displays them on an interactive map built with Streamlit + Folium.

---

## Live App
https://planetnewsmap.streamlit.app/

Test URLs:

https://www.cnn.com/2025/09/05/sport/nfl-week-1-eagles-cowboys

https://www.cnn.com/2025/09/08/middleeast/spain-pm-pedro-sanchez-israel-travel-ban-intl

https://apnews.com/article/nepal-protest-social-media-ban-89cf500969536cf2a35c3fb884cfa620

https://apnews.com/article/brazil-bolsonaro-coup-trial-513fff1adc42b1ff60754eb2ab0f29ae

## Features

- Input a news article URL or paste raw article text
- Extracts:
  - Locations (city, state, country, landmark)
  - Confidence score (0.0–1.0)
  - One–two sentence summary of events at each location
- Filters out low-confidence results (`confidence < 0.90`)
- Geocodes locations via OpenStreetMap Nominatim
- Plots results on an interactive Leaflet/Folium map with clean Carto Light tiles
- Popups show location name, confidence, and event summary
- Auto-zooms to fit all identified locations

---

## Tech Stack

- [Python 3.10+](https://www.python.org/)
- [Streamlit](https://streamlit.io/) — Web app framework
- [Folium](https://python-visualization.github.io/folium/) — Interactive mapping
- [streamlit-folium](https://github.com/randyzwitch/streamlit-folium) — Folium integration with Streamlit
- [trafilatura](https://github.com/adbar/trafilatura) — News article text extraction
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) — HTML parsing
- [Google Gemini](https://ai.google.dev/) — Location + summary extraction
- [OpenStreetMap Nominatim](https://nominatim.org/) — Free geocoding

---

## Setup

### 1. Clone this repo
```bash
git clone https://github.com/yourusername/newsmap.git
cd newsmap
```

### 2. Create a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
Install all required Python packages using the provided requirements.txt:
```bash
pip install -r requirements.txt
```

### 4. Configure API key
Create a .env file in the project root:
```env
GOOGLE_API_KEY=your_api_key_here
```

---

## Run the App
```bash
streamlit run app.py
```
Open http://localhost:8501 in your browser.

---

## Example Workflow

1. Paste a news article URL (e.g., CNN, BBC, NYT)
2. Click "Extract & Map Locations"
3. Wait while Gemini extracts and Nominatim geocodes
4. View interactive map with markers + summaries

---

## Improvements (Next Steps)

1. Improve choice of correct locations when location is ambguous (e.g "City Hall")
2. Use Gemini-1.5-pro fallback if Gemini-1.5-flash fails parsing
3. Add caching for geocoding results
4. Export results as CSV/GeoJSON

---

## License

MIT License
