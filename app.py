import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime, timedelta
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
        "Return ONLY JSON: {'significant': bool, 'direction': 'bullish'|'bearish'|'neutral', 'impact_level': 'HIGH'|'MEDIUM'|'LOW', 'reason': 'str'}"
    )
)

# --- 2. SESSION STATE ---
if 'market_log' not in st.session_state:
    st.session_state.market_log = []
if 'processed_urls' not in st.session_state:
    st.session_state.processed_urls = set()

# --- 3. TIME FORMATTING HELPER ---
def format_relative_time(dt):
    now = datetime.now()
    diff = now - dt
    
    if diff < timedelta(seconds=60):
        return f"{int(diff.total_seconds())} secs ago"
    elif diff < timedelta(minutes=60):
        return f"{int(diff.total_seconds() // 60)} mins ago"
    elif diff < timedelta(hours=24):
        return f"{int(diff.total_seconds() // 3600)} hrs ago"
    else:
        return dt.strftime("%Y-%m-%d %H:%M")

# --- 4. CORE FUNCTIONS ---
def analyze_impact_with_ai(headline):
    try:
        response = ai_model.generate_content(f"Analyze: {headline}")
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else {"significant": False}
    except:
        return {"significant": False}

# --- 5. THE SCANNER ENGINE ---
@st.fragment(run_every=60)
def scanner_engine():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    with st.status("Syncing Live & Historical Data...", expanded=False) as status:
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=12)
                soup = BeautifulSoup(r.content, 'xml')
                # Scanning last 20 to ensure we find the "Previous 10" relevant news
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
                                "timestamp": datetime.now(), # Store raw datetime for relative calculation
                                "title": title,
                                "source": provider,
                                "link": loc,
                                "analysis": analysis
                            }
                            st.session_state.market_log.insert(0, entry)
            except:
                continue
        status.update(label="System Synced", state="complete")

    # --- DISPLAY FEED ---
    if not st.session_state.market_log:
        st.info("System Standby: Deep-scanning for market signals...")
    else:
        # Displaying the feed
        for item in st.session_state.market_log[:15]: 
            a = item['analysis']
            rel_time = format_relative_time(item['timestamp'])
            direction = a.get("direction", "neutral").lower()
            impact = a.get("impact_level", "LOW").upper()
            
            # Color Logic
            color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
            bg = f"{color}15"

            st.markdown(f"""
                <div style="border-left: 10px solid {color}; background-color: {bg}; padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid {color}33;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <span style="color: {color}; font-weight: bold; letter-spacing: 1px; font-size: 12px;">
                            [{impact} IMPACT]
                        </span>
                        <span style="color: #8b949e; font-size: 11px; font-weight: 600;">
                            🕒 {rel_time} | 🏛️ {item['source']}
                        </span>
                    </div>
                    <h3 style="margin: 0 0 10px 0; color: white; font-size: 1.2rem; line-height: 1.4;">{item['title']}</h3>
                    <p style="color: #c9d1d9; font-size: 14px; margin-bottom: 12px;">
                        <b>AI Logic:</b> {a.get('reason')}
                    </p>
                    <div style="display: flex; gap: 25px; align-items: center;">
                        <a href="{item['link']}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 13px; font-weight: bold; border: 1px solid #58a6ff44; padding: 4px 10px; border-radius: 5px;">
                            READ SOURCE ↗
                        </a>
                        <span style="color: {color}; font-size: 11px; font-weight: bold; background: {color}22; padding: 3px 8px; border-radius: 4px; border: 1px solid {color}44;">
                            SENTIMENT: {direction.upper()}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --- UI & TERMINAL ---
st.set_page_config(page_title="Deep Market Scanner", layout="wide")
st.title("🏛️ Tier-1 Market Intelligence")

with st.sidebar:
    st.header("Admin Terminal")
    if st.button("🚀 Run Manual Test Alert"):
        st.session_state.market_log.insert(0, {
            "timestamp": datetime.now() - timedelta(minutes=5),
            "title": "Federal Reserve signals potential rate cut in June meeting",
            "source": "INTERNAL TESTER",
            "link": "https://www.google.com",
            "analysis": {"significant": True, "direction": "bullish", "impact_level": "HIGH", "reason": "Dovish Fed stance usually leads to lower yields and increased FII flow to India."}
        })
        st.rerun()

    if st.button("Clear Dashboard"):
        st.session_state.market_log = []
        st.session_state.processed_urls = set()
        st.rerun()
    
    st.divider()
    st.info("System deep-scans last 20 headlines to ensure a historical baseline of 10 items is met.")

scanner_engine()
