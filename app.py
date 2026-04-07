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

# --- 2. DATA PERSISTENCE ---
if 'market_log' not in st.session_state:
    st.session_state.market_log = []
if 'processed_urls' not in st.session_state:
    st.session_state.processed_urls = set()

# --- 3. HELPER FUNCTIONS ---
def analyze_impact_with_ai(headline):
    try:
        response = ai_model.generate_content(f"Analyze: {headline}")
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else {"significant": False}
    except:
        return {"significant": False}

# --- 4. THE DEEP SCANNER ---
@st.fragment(run_every=60)
def scanner_engine():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    with st.status("Performing Deep Market Scan...", expanded=False) as status:
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                # CHANGED: Now taking the latest 15 URLs instead of 1
                urls = soup.find_all('url')[:15] 
                
                for item in urls:
                    loc = item.find('loc').text
                    title_tag = item.find(['news:title', 'title'])
                    title = title_tag.text.strip() if title_tag else ""
                    
                    if loc not in st.session_state.processed_urls and title:
                        st.session_state.processed_urls.add(loc)
                        analysis = analyze_impact_with_ai(title)
                        
                        if analysis.get("significant"):
                            entry = {
                                "time": datetime.now().strftime("%H:%M"),
                                "title": title,
                                "source": provider,
                                "link": loc,
                                "analysis": analysis
                            }
                            st.session_state.market_log.insert(0, entry)
            except:
                continue
        status.update(label="Deep Scan Complete", state="complete")

    # --- DISPLAY ---
    if not st.session_state.market_log:
        st.info("Searching deeper... No high-impact signals found in the last 30 headlines.")
    else:
        for item in st.session_state.market_log[:20]:
            a = item['analysis']
            color = "#28a745" if a['direction'] == "bullish" else "#dc3545" if a['direction'] == "bearish" else "#8b949e"
            bg = f"{color}22"

            st.markdown(f"""
                <div style="border-left: 8px solid {color}; background-color: {bg}; padding: 15px; border-radius: 8px; margin-bottom: 10px; border: 1px solid {color}44;">
                    <small style="color: {color}; font-weight: bold;">[{a['impact_level']} IMPACT]</small>
                    <h4 style="margin: 5px 0;">{item['title']}</h4>
                    <p style="font-size: 14px; color: #c9d1d9;"><b>Reason:</b> {a['reason']}</p>
                    <a href="{item['link']}" target="_blank" style="color: #58a6ff; font-size: 12px; text-decoration: none;">View Source ↗</a>
                </div>
            """, unsafe_allow_html=True)

# --- 5. UI LAYOUT ---
st.set_page_config(page_title="Deep Market Scanner", layout="wide")
st.title("🏛️ Tier-1 Market Intelligence")

with st.sidebar:
    st.header("Tester Console")
    if st.button("🚀 Run Manual Test Alert"):
        test_title = "US Federal Reserve announces emergency 75bps rate cut to support economy"
        test_analysis = {"significant": True, "direction": "bullish", "impact_level": "HIGH", "reason": "Emergency rate cuts are highly bullish for global liquidity and Indian IT/Financial sectors."}
        st.session_state.market_log.insert(0, {"time": "TEST", "title": test_title, "source": "TESTER", "link": "#", "analysis": test_analysis})
        st.rerun()
    
    if st.button("Clear Dashboard"):
        st.session_state.market_log = []
        st.session_state.processed_urls = set()
        st.rerun()

scanner_engine()
