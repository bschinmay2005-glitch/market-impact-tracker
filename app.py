import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime
import re
import pandas as pd

# --- 1. CRITICAL CONFIG & API SETUP ---
# It's better to use st.secrets["GEMINI_API_KEY"] if deploying, 
# otherwise replace the string below.
GEMINI_KEY = "YOUR_ACTUAL_GEMINI_API_KEY" 
NTFY_TOPIC = "chinmay_market_shaker_2026"

genai.configure(api_key=GEMINI_KEY)

# This is the "Brain" of the system - strictly tuned for traders.
ai_model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"},
    system_instruction=(
        "You are a Tier-1 Hedge Fund Analyst. Your ONLY job is to filter market-moving news. "
        "IGNORE: Sports, entertainment, lifestyle, general politics, or fluff. "
        "ONLY ACCEPT: GDP, Inflation, RBI/Fed policy, Corporate Earnings, Mergers, "
        "Sectoral shifts (Auto, Tech, Banking), and Geopolitics affecting Oil/Trade. "
        "If news is significant, classify impact as HIGH/MEDIUM/LOW and direction as bullish/bearish/neutral."
    )
)

# --- 2. CORE FUNCTIONS ---

def analyze_impact_with_ai(headline):
    """Sends headline to Gemini and enforces a strict JSON response."""
    prompt = f"Analyze this headline for Indian Market impact: '{headline}'"
    try:
        response = ai_model.generate_content(prompt)
        # Use regex to ensure we only get the JSON part
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return data
        return {"significant": False}
    except Exception:
        return {"significant": False}

def send_ntfy_push(title, link, analysis):
    """Sends a high-priority notification to your phone via ntfy.sh."""
    priority = "5" if analysis.get("impact_level") == "HIGH" else "3"
    tag = "rotating_light" if analysis.get("direction") == "bearish" else "rocket"
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=title.encode('utf-8'),
            headers={
                "Title": f"[{analysis.get('impact_level')}] Market Alert",
                "Click": link,
                "Priority": priority,
                "Tags": tag
            }, timeout=5
        )
    except:
        pass

# --- 3. UI LAYOUT & STYLING ---

st.set_page_config(page_title="AI Market Intelligence", layout="wide", page_icon="🏛️")

# Custom Dark Theme CSS
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Tier-1 Market Intelligence")
st.subheader(f"Global & Domestic Economic Scanner")

# Initialize Session States
if 'market_log' not in st.session_state:
    st.session_state.market_log = []
if 'processed_urls' not in st.session_state:
    st.session_state.processed_urls = set()

# --- 4. SCANNER ENGINE ---

@st.fragment(run_every=60)
def scanner_loop():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    # Progress indicator
    with st.status("Scanning Markets...", expanded=False) as status:
        found_new = False
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                urls = soup.find_all('url')[:15] # Fresh 15
                
                for item in urls:
                    loc = item.find('loc').text
                    title_tag = item.find(['news:title', 'title'])
                    title = title_tag.text.strip() if title_tag else ""
                    
                    # Only process if we haven't seen this URL before
                    if loc not in st.session_state.processed_urls and title:
                        analysis = analyze_impact_with_ai(title)
                        st.session_state.processed_urls.add(loc)
                        
                        if analysis.get("significant") == True:
                            new_entry = {
                                "time": datetime.now().strftime("%H:%M"),
                                "title": title,
                                "source": provider,
                                "link": loc,
                                "analysis": analysis
                            }
                            st.session_state.market_log.insert(0, new_entry)
                            send_ntfy_push(title, loc, analysis)
                            found_new = True
            except Exception as e:
                st.write(f"Error connecting to {provider}")
        
        status.update(label="Scan Complete", state="complete")

    # --- 5. DISPLAY RESULTS ---
    
    if not st.session_state.market_log:
        st.info("Awaiting high-impact market signals. System is active.")
    else:
        for entry in st.session_state.market_log[:25]: # Show latest 25 items
            a = entry['analysis']
            direction = a.get("direction", "neutral").lower()
            impact = a.get("impact_level", "LOW").upper()
            
            # Logic for Visuals based on Sentiment
            if direction == "bullish":
                color, bg = "#28a745", "rgba(40, 167, 69, 0.1)" # Green
            elif direction == "bearish":
                color, bg = "#dc3545", "rgba(220, 53, 69, 0.1)" # Red
            else:
                color, bg = "#8b949e", "rgba(139, 148, 158, 0.1)" # Neutral

            # HTML Injection for the "Market Card"
            st.markdown(f"""
                <div style="border-left: 8px solid {color}; background-color: {bg}; padding: 20px; border-radius: 10px; margin-bottom: 12px; border: 1px solid {color}44;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="color: {color}; font-weight: bold; font-size: 14px;">[{impact} IMPACT]</span>
                        <span style="color: #8b949e; font-size: 12px;">{entry['time']} | {entry['source']}</span>
                    </div>
                    <h3 style="margin: 10px 0; color: white; font-size: 1.2rem;">{entry['title']}</h3>
                    <p style="color: #c9d1d9; font-size: 14px;"><b>Analysis:</b> {a.get('reason')}</p>
                    <div style="display: flex; gap: 20px;">
                        <a href="{entry['link']}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 12px; font-weight: bold;">READ FULL NEWS →</a>
                        <span style="color: {color}; font-size: 12px; font-weight: bold;">SENTIMENT: {direction.upper()}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- 6. SIDEBAR ADMIN ---
with st.sidebar:
    st.header("Settings")
    if st.button("Clear Dashboard"):
        st.session_state.market_log = []
        st.session_state.processed_urls = set()
        st.rerun()
    
    st.divider()
    st.write("Monitoring:")
    st.write("- Global Macro")
    st.write("- Domestic Policy")
    st.write("- Corporate Earnings")

# Start the dashboard
scanner_loop()
