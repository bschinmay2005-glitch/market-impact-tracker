import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import google.generativeai as genai

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 

# Setup Gemini
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_impact_with_ai(headline):
    prompt = f"""
    Analyze this Indian Stock Market headline: "{headline}"
    Current Context (April 2026): 
    - RBI MPC meeting (April 8).
    - US-Iran/Strait of Hormuz updates.
    - Q4 Earnings (TCS, Infosys).

    Return ONLY JSON:
    {{"significant": true, "direction": "bullish", "impact": "HIGH"}}
    """
    try:
        response = ai_model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"significant": False}

def send_ntfy_push(headline, link, direction, impact_level):
    clean_headline = re.sub(r'[^\x00-\x7f]', r'', headline)
    priority = "5" if impact_level == "HIGH" else "3"
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=clean_headline.encode('utf-8'),
            headers={
                "Title": f"[{impact_level}] MARKET {direction.upper()}",
                "Click": link,
                "Priority": priority, 
                "Tags": "rotating_light,chart" if impact_level == "HIGH" else "loudspeaker"
            },
            timeout=5
        )
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="AI Market Shaker 2026", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .news-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; background-color: #161b22; border: 1px solid #30363d; }
    .positive-impact { border-left: 10px solid #28a745; }
    .negative-impact { border-left: 10px solid #dc3545; }
    .badge-pos { background-color: #28a745; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    .badge-neg { background-color: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Monitor")
st.sidebar.title("🔍 Live Scanner Log")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

if st.sidebar.button("Clear History"):
    st.session_state.seen_headlines.clear()
    st.rerun()

@st.fragment(run_every=60)
def news_dashboard():
    search_query = "site:moneycontrol.com OR site:economictimes.indiatimes.com Indian Stock Market"
    rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-IN&gl=IN&ceid=IN:en"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.0.0.0'}
    
    found_impact = False
    
    try:
        r = requests.get(rss_url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')
        
        for item in items[:25]:
            full_title = item.find('title').text
            title = full_title.split(' - ')[0].strip()
            link = item.find('link').text
            
            # SAFE SIDEBAR LOGGING
            with st.sidebar:
                st.write(f"🔍 Scanning: {title[:50]}...")

            if title not in st.session_state.seen_headlines:
                analysis = analyze_impact_with_ai(title)
                
                if analysis.get("significant"):
                    found_impact = True
                    st.session_state.seen_headlines.add(title)
                    
                    direction = analysis["direction"]
                    impact = analysis["impact"]
                    send_ntfy_push(title, link, direction, impact)
                    
                    card_style = "positive-impact" if direction == "bullish" else "negative-impact"
                    badge_style = "badge-pos" if direction == "bullish" else "badge-neg"
                    
                    st.markdown(f'''
                        <div class="news-card {card_style}">
                            <span class="{badge_style}">{impact} {direction.upper()}</span>
                            <h3 style="margin-top: 10px; color: white;">{title}</h3>
                            <a href="{link}" target="_blank" style="color: #58a6ff; text-decoration: none;">Read Source Article →</a>
                        </div>
                    ''', unsafe_allow_html=True)
                    
    except Exception as e:
        # WRAPPED IN SIDEBAR TO PREVENT CRASH
        with st.sidebar:
            st.warning(f"Connection glitch: {str(e)[:50]}...")

    if not found_impact:
        st.info("AI is currently scanning. No market-shaking events detected in this cycle.")

# Call the dashboard
news_dashboard()
