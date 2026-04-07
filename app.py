import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime, timedelta
import re
import os

# --- 1. CONFIGURATION ---
GEMINI_KEY = "YOUR_ACTUAL_GEMINI_API_KEY" 
DB_FILE = "market_db.json" # Our permanent storage file

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

# --- 2. PERMANENT STORAGE LOGIC ---
def load_permanent_data():
    """Loads news from the local JSON file so it survives a refresh."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            try:
                data = json.load(f)
                # Convert string timestamps back to datetime objects
                for item in data:
                    item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                return data
            except:
                return []
    return []

def save_permanent_data(log):
    """Saves the current news log to the local JSON file."""
    # Convert datetimes to strings for JSON compatibility
    serializable_data = []
    for item in log[:50]: # Keep only the last 50 items to save space
        temp_item = item.copy()
        if isinstance(temp_item['timestamp'], datetime):
            temp_item['timestamp'] = temp_item['timestamp'].isoformat()
        serializable_data.append(temp_item)
    
    with open(DB_FILE, "w") as f:
        json.dump(serializable_data, f)

# --- 3. SESSION INITIALIZATION ---
if 'market_log' not in st.session_state:
    st.session_state.market_log = load_permanent_data()
if 'processed_urls' not in st.session_state:
    # Pre-fill processed URLs so we don't re-analyze what's already in the DB
    st.session_state.processed_urls = {item['link'] for item in st.session_state.market_log}

# --- 4. HELPERS ---
def format_relative_time(dt):
    if not isinstance(dt, datetime): return "Recent"
    now = datetime.now()
    diff = now - dt
    if diff < timedelta(seconds=60): return f"{int(diff.total_seconds())}s ago"
    elif diff < timedelta(minutes=60): return f"{int(diff.total_seconds() // 60)}m ago"
    elif diff < timedelta(hours=24): return f"{int(diff.total_seconds() // 3600)}h ago"
    else: return dt.strftime("%Y-%m-%d")

def analyze_impact_with_ai(headline):
    try:
        response = ai_model.generate_content(f"Analyze: {headline}")
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else {"significant": False}
    except: return {"significant": False}

# --- 5. SCANNER ENGINE ---
@st.fragment(run_every=60)
def scanner_engine():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    with st.status("Scanning Markets...", expanded=False) as status:
        new_data_found = False
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                urls = soup.find_all('url')[:20] 
                
                for item in urls:
                    loc = item.find('loc').text.strip()
                    title = item.find(['news:title', 'title']).text.strip()
                    
                    if loc not in st.session_state.processed_urls:
                        st.session_state.processed_urls.add(loc)
                        analysis = analyze_impact_with_ai(title)
                        
                        if analysis.get("significant"):
                            entry = {
                                "timestamp": datetime.now(), 
                                "title": title,
                                "source": provider,
                                "link": loc,
                                "analysis": analysis
                            }
                            st.session_state.market_log.insert(0, entry)
                            new_data_found = True
            except: continue
        
        if new_data_found:
            save_permanent_data(st.session_state.market_log)
        status.update(label="Sync Complete", state="complete")

    # --- DISPLAY FEED ---
    if not st.session_state.market_log:
        st.info("System Standby: Searching for market signals...")
    else:
        for item in st.session_state.market_log[:20]: 
            a = item['analysis']
            rel_time = format_relative_time(item.get('timestamp'))
            color = "#28a745" if a['direction'] == "bullish" else "#dc3545" if a['direction'] == "bearish" else "#8b949e"
            
            st.markdown(f"""
                <div style="border-left: 8px solid {color}; background-color: {color}15; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid {color}33;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px;">
                        <b style="color: {color};">[{a['impact_level']} IMPACT]</b>
                        <span style="color: #8b949e;">🕒 {rel_time} | 🏛️ {item['source']}</span>
                    </div>
                    <h4 style="margin: 8px 0; color: white;">{item['title']}</h4>
                    <p style="color: #c9d1d9; font-size: 13px; margin-bottom: 10px;"><b>AI:</b> {a['reason']}</p>
                    <a href="{item['link']}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 12px; font-weight: bold;">READ SOURCE ↗</a>
                </div>
            """, unsafe_allow_html=True)

# --- 6. UI ---
st.set_page_config(page_title="Permanent Market Intelligence", layout="wide")
st.title("🏛️ Tier-1 Market Intelligence")

with st.sidebar:
    st.header("Terminal Settings")
    if st.button("Clear All History (Wipe DB)"):
        if os.path.exists(DB_FILE): os.remove(DB_FILE)
        st.session_state.market_log = []
        st.session_state.processed_urls = set()
        st.rerun()
    st.info("News is now saved to market_db.json and will survive browser refreshes.")

scanner_engine()
