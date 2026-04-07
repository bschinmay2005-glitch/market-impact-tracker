import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CONFIG ---
# Replace with your actual API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')
NTFY_TOPIC = "chinmay_market_shaker_2026"

def analyze_impact_with_ai(headline):
    """Deep reasoning to connect global events to Indian markets."""
    prompt = f"""
    Role: Senior Financial Analyst (Indian Markets)
    Analyze this headline: "{headline}"
    
    1. Does it affect Indian Economy/Nifty/Sensex or Global Macro (Oil/Fed/Gold)?
    2. Determine direction: BULLISH (Positive) or BEARISH (Negative).
    3. Determine impact: HIGH, MEDIUM, or LOW.
    
    Return ONLY JSON:
    {{
        "significant": true/false,
        "direction": "bullish/bearish",
        "impact": "HIGH/MEDIUM/LOW",
        "reason": "1-sentence link to Indian investor impact."
    }}
    """
    try:
        response = ai_model.generate_content(prompt)
        res = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res)
    except:
        return {"significant": False}

@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0'}
    found_any = False

    with st.expander("🔍 Scraper Activity Log", expanded=False):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                # Parse as XML specifically
                soup = BeautifulSoup(r.content, 'xml')
                
                # Search specifically for tags with or without namespaces
                for entry in soup.find_all('url')[:20]:
                    news_tag = entry.find(['news:news', 'news'])
                    if not news_tag: continue
                    
                    title_tag = news_tag.find(['news:title', 'title'])
                    title = title_tag.text.strip()
                    link = entry.find('loc').text
                    
                    st.write(f"Scanning {provider}: {title[:60]}...")

                    if title not in st.session_state.seen_headlines:
                        analysis = analyze_impact_with_ai(title)
                        
                        if analysis.get("significant"):
                            found_any = True
                            st.session_state.seen_headlines.add(title)
                            
                            # UI Rendering
                            color = "#28a745" if analysis["direction"] == "bullish" else "#dc3545"
                            st.markdown(f"""
                                <div style="border-left: 10px solid {color}; padding: 15px; background: #161b22; margin-bottom: 10px; border-radius: 8px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:10px;">
                                            {analysis['impact']} {analysis['direction'].upper()}
                                        </span>
                                        <small style="color:gray;">{provider}</small>
                                    </div>
                                    <h4 style="margin-top:10px; color:white;">{title}</h4>
                                    <p style="color:#8b949e; font-size:13px; font-style:italic;">{analysis['reason']}</p>
                                </div>
                            """, unsafe_allow_html=True)
            except Exception:
                # Use st.write inside fragments instead of st.toast/sidebar to avoid crashes
                st.write(f"⚠️ {provider} connection error.")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner Active. Waiting for market-shaking news...")

# --- MAIN UI ---
st.set_page_config(page_title="AI Market Monitor", layout="wide")
st.title("🏛️ AI High-Impact Market Monitor")
st.caption(f"Last Scan: {datetime.now().strftime('%H:%M:%S')}")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

with st.sidebar:
    st.header("Settings")
    if st.button("Reset Scanner"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
