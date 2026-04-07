import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CRITICAL CONFIG ---
# Ensure you replace this with your actual API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')
NTFY_TOPIC = "chinmay_market_shaker_2026"

def analyze_impact_with_ai(headline):
    prompt = f"""
    Role: Senior Financial Analyst (Indian Markets)
    Task: Analyze the economic impact of this headline.
    Headline: "{headline}"

    Return ONLY a JSON object:
    {{
        "significant": true/false,
        "direction": "bullish/bearish/neutral",
        "impact_level": "HIGH/LESS",
        "reason": "1-sentence link to Indian markets."
    }}
    
    Rule: 
    1. Set "significant" to true if it is global or domestic economic/business news.
    2. Set "impact_level" to "HIGH" only for major market movers; otherwise use "LESS".
    """
    try:
        response = ai_model.generate_content(prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"significant": False}

def send_ntfy_push(title, link, analysis):
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

# --- UI STYLE ---
st.set_page_config(page_title="AI Market Shaker 2026", layout="wide")
st.markdown("<style>.main { background-color: #0e1117; }</style>", unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Monitor")
st.caption(f"Scanner Live • Sitemaps Active • {datetime.now().strftime('%H:%M:%S')}")

# Persistent storage so news doesn't vanish on refresh
if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()
if 'saved_news' not in st.session_state:
    st.session_state.saved_news = []

# --- THE SCANNER (Runs in background) ---
@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    with st.expander("🔍 Scraper Live Feed (Debug)", expanded=False):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=15)
                soup = BeautifulSoup(r.content, 'xml')
                entries = soup.find_all('url')

                for entry in entries[:15]:
                    title_tag = entry.find(['news:title', 'title', 'image:title'])
                    if not title_tag: continue
                    
                    title = title_tag.text.strip()
                    link = entry.find('loc').text if entry.find('loc') else "#"
                    
                    if title not in st.session_state.seen_headlines:
                        analysis = analyze_impact_with_ai(title)
                        st.session_state.seen_headlines.add(title)
                        
                        if analysis.get("significant"):
                            # Save to session state
                            st.session_state.saved_news.insert(0, {
                                "title": title,
                                "link": link,
                                "provider": provider,
                                "analysis": analysis
                            })
                            # Send push notification
                            send_ntfy_push(title, link, analysis)
            except:
                continue

# Execute the background scanner
news_dashboard()

# --- THE DISPLAY ENGINE (Stays visible) ---
if not st.session_state.saved_news:
    st.info("Scanner Warming Up... Waiting for economic signals.")
else:
    for item in st.session_state.saved_news:
        ans = item['analysis']
        direction = ans.get("direction", "neutral").lower()
        impact = ans.get("impact_level", "LESS").upper()
        
        # Color Logic: Green for Bullish, Red for Bearish
        color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
        icon = "💹" if direction == "bullish" else "🚨" if direction == "bearish" else "⚖️"
        
        # Border Logic: 15px for HIGH impact, 4px for LESS
        border_width = "15px" if impact == "HIGH" else "4px"

        st.markdown(f"""
            <div style="border-left: {border_width} solid {color}; padding: 20px; background: #161b22; margin-bottom: 15px; border-radius: 12px; border: 1px solid #30363d;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="background-color: {color}22; color: {color}; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold;">
                        {impact} IMPACT
                    </span>
                    <small style="color: #8b949e;">{item['provider']} {icon}</small>
                </div>
                <h3 style="margin: 12px 0 8px 0; color: white; font-size: 1.15rem;">{item['title']}</h3>
                <p style="color: #c9d1d9; font-size: 14px;"><b>AI Assessment:</b> {ans.get('reason')}</p>
                <div style="display: flex; gap: 15px; margin-top: 10px;">
                    <a href="{item['link']}" target="_blank" style="color: #58a6ff; font-size: 12px; text-decoration: none; font-weight: bold;">READ SOURCE →</a>
                    <span style="color: {color}; font-size: 12px; font-weight: bold;">SENTIMENT: {direction.upper()}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Admin Controls")
    if st.button("Clear All News"):
        st.session_state.saved_news = []
        st.session_state.seen_headlines = set()
        st.rerun()
