import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime
import re

# --- 1. CONFIGURATION ---
GEMINI_KEY = "YOUR_ACTUAL_GEMINI_API_KEY" 
NTFY_TOPIC = "chinmay_market_shaker_2026"

genai.configure(api_key=GEMINI_KEY)

ai_model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    generation_config={"response_mime_type": "application/json"},
    system_instruction=(
        "You are a Tier-1 Hedge Fund Analyst. Filter news for Indian Traders. "
        "STRICT RULE: Only accept GDP, Inflation, RBI, Fed, Corporate Earnings, M&A, or Geopolitics. "
        "IGNORE: Sports, general politics, and lifestyle. "
        "Return ONLY JSON: {'significant': bool, 'direction': 'bullish'|'bearish'|'neutral', 'impact_level': 'HIGH'|'MEDIUM'|'LOW', 'reason': 'str'}"
    )
)

# --- 2. SESSION STATE MANAGEMENT ---
if 'market_log' not in st.session_state:
    st.session_state.market_log = [] # This stores our "Display Feed"
if 'processed_urls' not in st.session_state:
    st.session_state.processed_urls = set() # This prevents duplicate AI calls

# --- 3. THE INTELLIGENCE ENGINE ---
def analyze_impact_with_ai(headline):
    try:
        response = ai_model.generate_content(f"Analyze impact: {headline}")
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"significant": False}
    except:
        return {"significant": False}

# --- 4. THE SCANNER (LATEST & HISTORICAL) ---
@st.fragment(run_every=60)
def scanner_engine():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    with st.status("Deep Scanning for Historical & Live Signals...", expanded=False) as status:
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=12)
                soup = BeautifulSoup(r.content, 'xml')
                # Grab the last 20 URLs to ensure we find at least 10 relevant ones
                urls = soup.find_all('url')[:20] 
                
                for item in urls:
                    loc = item.find('loc').text
                    title_tag = item.find(['news:title', 'title'])
                    title = title_tag.text.strip() if title_tag else ""
                    
                    if loc not in st.session_state.processed_urls and title:
                        st.session_state.processed_urls.add(loc)
                        analysis = analyze_impact_with_ai(title)
                        
                        if analysis.get("significant"):
                            entry = {
                                "time": datetime.now().strftime("%H:%M:%S"),
                                "title": title,
                                "source": provider,
                                "link": loc,
                                "analysis": analysis
                            }
                            # Always put newest at the top
                            st.session_state.market_log.insert(0, entry)
            except:
                continue
        status.update(label="Sync Complete", state="complete")

    # --- DISPLAY FEED (Limited to top 15 items) ---
    if not st.session_state.market_log:
        st.info("System Standby: No significant market-moving news found in recent history.")
    else:
        # We display the top 15 (which includes the 10 historical + any new upcoming ones)
        for item in st.session_state.market_log[:15]: 
            a = item['analysis']
            direction = a.get("direction", "neutral").lower()
            impact = a.get("impact_level", "LOW").upper()
            
            # Dynamic Styling
            if direction == "bullish":
                color, bg = "#28a745", "rgba(40, 167, 69, 0.1)"
            elif direction == "bearish":
                color, bg = "#dc3545", "rgba(220, 53, 69, 0.1)"
            else:
                color, bg = "#8b949e", "rgba(139, 148, 158, 0.05)"

            st.markdown(f"""
                <div style="border-left: 10px solid {color}; background-color: {bg}; padding: 20px; border-radius: 10px; margin-bottom: 12px; border: 1px solid {color}33;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="color: {color}; font-weight: bold; letter-spacing: 1px; font-size: 13px;">
                            [{impact} IMPACT]
                        </span>
                        <span style="color: #8b949e; font-size: 11px;">
                            🕒 {item['time']} | 🏛️ SOURCE: {item['source']}
                        </span>
                    </div>
                    <h3 style="margin: 0 0 10px 0; color: white; font-size: 1.2rem; line-height: 1.4;">{item['title']}</h3>
                    <p style="color: #c9d1d9; font-size: 14px; margin-bottom: 10px;">
                        <b>AI Assessment:</b> {a.get('reason')}
                    </p>
                    <div style="display: flex; gap: 20px; align-items: center;">
                        <a href="{item['link']}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 12px; font-weight: bold;">READ SOURCE ↗</a>
                        <span style="color: {color}; font-size: 11px; font-weight: bold; background: {color}22; padding: 2px 8px; border-radius: 4px;">
                            {direction.upper()}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- 5. UI & TERMINAL ---
st.set_page_config(page_title="Deep Market Intelligence", layout="wide")
st.title("🏛️ Tier-1 Market Intelligence")

with st.sidebar:
    st.header("Control Terminal")
    if st.button("🚀 Run Manual Test Alert"):
        test_data = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "title": "Indian GDP Growth exceeds expectations at 8.4%; Nifty futures surge",
            "source": "INTERNAL TESTER",
            "link": "#",
            "analysis": {"significant": True, "direction": "bullish", "impact_level": "HIGH", "reason": "Higher GDP growth signals strong domestic consumption and attracts global FII flows."}
        }
        st.session_state.market_log.insert(0, test_data)
        st.rerun()

    if st.button("Clear & Restart Scanner"):
        st.session_state.market_log = []
        st.session_state.processed_urls = set()
        st.rerun()
    
    st.divider()
    st.info("System is deep-scanning the last 40 headlines across Moneycontrol & ET to find the 10 most relevant starting points.")

# EXECUTE SCANNER
scanner_engine()
