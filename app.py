import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import google.generativeai as genai

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_impact_with_ai(headline):
    prompt = f"Analyze this Indian Stock Market headline for impact (Bullish/Bearish/High/Low): {headline}. Return ONLY JSON."
    try:
        response = ai_model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"significant": False}

# --- UI SETUP ---
st.set_page_config(page_title="AI Market Shaker 2026", layout="wide")
st.title("🏛️ AI High-Impact Market Monitor")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE STABLE SCANNER ---
@st.fragment(run_every=60)
def news_dashboard():
    search_query = "site:moneycontrol.com OR site:economictimes.indiatimes.com Indian Stock Market"
    rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    # 1. Fetch data safely
    try:
        r = requests.get(rss_url, timeout=15)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')[:20]
    except Exception as e:
        st.error("Connection lost. Retrying in 60s...")
        return

    # 2. Process and Display
    found_any = False
    
    # Simple log in the main area instead of the sidebar to prevent crashes
    with st.expander("🔍 Current Scrape Log (Last 60s)", expanded=False):
        for item in items:
            full_title = item.find('title').text
            title = full_title.split(' - ')[0].strip()
            link = item.find('link').text
            st.write(f"Reading: {title[:60]}...")

            if title not in st.session_state.seen_headlines:
                analysis = analyze_impact_with_ai(title)
                
                if analysis.get("significant"):
                    found_any = True
                    st.session_state.seen_headlines.add(title)
                    
                    # Display the Card
                    color = "#28a745" if analysis["direction"] == "bullish" else "#dc3545"
                    st.markdown(f"""
                        <div style="border-left: 10px solid {color}; padding: 20px; background: #161b22; margin-bottom: 15px; border-radius: 12px;">
                            <h3 style="color: white; margin: 0;">{title}</h3>
                            <p style="color: {color}; font-weight: bold;">{analysis['impact']} {analysis['direction'].upper()}</p>
                            <a href="{link}" target="_blank" style="color: #58a6ff;">Read More →</a>
                        </div>
                    """, unsafe_allow_html=True)

    if not found_any:
        st.info("Scanning... No new high-impact events detected.")

news_dashboard()
