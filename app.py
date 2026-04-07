import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 
# Replace with your actual API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_impact_with_ai(headline):
    """
    Acts as a Senior Market Analyst to understand the 'meaning' behind news,
    not just keywords.
    """
    prompt = f"""
    Role: Senior Financial Analyst (Indian Markets)
    Task: Analyze the economic impact of this headline.
    Headline: "{headline}"

    Instructions:
    1. Determine if this news affects the Indian economy, Nifty/Sensex, or global macro-trends (Oil, Gold, Fed Rates, Geopolitics).
    2. Even if it's international (e.g., Middle East tensions, US Fed), explain the specific ripple effect on India.
    3. Determine if the impact is "Significant" (High/Medium) or "Routine" (Low).
    
    Return ONLY a JSON object in this format:
    {{
        "significant": true,
        "direction": "bullish/bearish/neutral",
        "impact_level": "HIGH/MEDIUM",
        "reasoning": "A concise 1-sentence explanation of why this matters to an Indian investor."
    }}
    """
    try:
        response = ai_model.generate_content(prompt)
        # Clean the response to ensure it's pure JSON
        raw_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_json)
    except:
        return {"significant": False}

def send_ntfy_push(headline, link, analysis):
    """Sends high-priority alerts to your phone via ntfy.sh"""
    priority = "5" if analysis.get("impact_level") == "HIGH" else "3"
    tag = "rotating_light" if analysis.get("direction") == "bearish" else "rocket"
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'),
            headers={
                "Title": f"[{analysis.get('impact_level')}] {analysis.get('direction').upper()}",
                "Click": link,
                "Priority": priority,
                "Tags": tag
            },
            timeout=5
        )
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="AI Market Shaker 2026", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #ffffff; }
    .news-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; background-color: #161b22; border: 1px solid #30363d; }
    .reasoning-box { background-color: #0d1117; padding: 10px; border-radius: 6px; margin-top: 10px; border: 1px dashed #444c56; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Monitor")
st.caption(f"Status: Scanning Live Sitemaps • Last Updated: {datetime.now().strftime('%H:%M:%S')}")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE STABLE SCANNER ---
@st.fragment(run_every=60)
def news_dashboard():
    # Direct Sitemap access for zero-delay news capture
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    found_any = False
    
    with st.expander("🔍 Scraper Activity Log", expanded=False):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                
                # Check the top 15 most recent URLs
                for entry in soup.find_all('url')[:15]:
                    news_tag = entry.find('news:news')
                    if not news_tag: continue
                    
                    title = news_tag.find('news:title').text.strip()
                    link = entry.find('loc').text
                    
                    st.write(f"[{provider}] Processing: {title[:70]}...")

                    if title not in st.session_state.seen_headlines:
                        # AI "Understands" the headline here
                        analysis = analyze_impact_with_ai(title)
                        
                        if analysis.get("significant"):
                            found_any = True
                            st.session_state.seen_headlines.add(title)
                            send_ntfy_push(title, link, analysis)
                            
                            # UI DISPLAY
                            color = "#28a745" if analysis["direction"] == "bullish" else "#dc3545"
                            st.markdown(f"""
                                <div class="news-card" style="border-left: 10px solid {color};">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="background:{color}; color:white; padding:2px 10px; border-radius:4px; font-weight:bold; font-size:12px;">
                                            {analysis.get('impact_level')} {analysis.get('direction').upper()}
                                        </span>
                                        <span style="color:#8b949e; font-size:12px;">Source: {provider}</span>
                                    </div>
                                    <h3 style="color: white; margin-top: 15px;">{title}</h3>
                                    <div class="reasoning-box">
                                        <p style="color: #c9d1d9; margin: 0; font-size: 14px;">
                                            <strong>AI Analysis:</strong> {analysis.get('reasoning')}
                                        </p>
                                    </div>
                                    <br>
                                    <a href="{link}" target="_blank" style="color: #58a6ff; text-decoration: none; font-weight: bold;">Read Full Article →</a>
                                </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                st.sidebar.error(f"Error connecting to {provider}")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner is live. Waiting for high-impact news to break...")

news_dashboard()
