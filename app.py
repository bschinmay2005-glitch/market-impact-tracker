import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CONFIG ---
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')
NTFY_TOPIC = "chinmay_market_shaker_2026"

def analyze_impact_with_ai(headline):
    prompt = f"""
    Role: Senior Equity Research Analyst
    Headline: "{headline}"
    
    Task: 
    1. FILTER: If this is NOT about the economy, stock markets, or macro-policy (e.g., Sports/IPL, Bollywood, Crime) -> set "significant": false.
    2. TARGET: If it IS related to global/domestic economy or markets -> set "significant": true.
    3. IMPACT: "HIGH" for Nifty/Global macro movers, "LESS" for minor economic updates or general news.
    4. DIRECTION: "bullish" (Positive/Green), "bearish" (Negative/Red), or "neutral".
    
    Return ONLY JSON:
    {{
        "significant": true/false,
        "direction": "bullish/bearish/neutral",
        "impact_level": "HIGH/LESS",
        "reason": "1-sentence economic impact."
    }}
    """
    try:
        response = ai_model.generate_content(prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"significant": False}

# --- UI STYLE ---
st.set_page_config(page_title="AI Market Intelligence", layout="wide")
st.markdown("<style>.main { background-color: #0e1117; }</style>", unsafe_allow_html=True)
st.title("🏛️ Economic & Market Intelligence Terminal")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }

    with st.expander("📡 Live Scraper Status (Debug)", expanded=True):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code != 200:
                    st.write(f"❌ {provider} Connection Error ({r.status_code})")
                    continue
                
                soup = BeautifulSoup(r.content, 'xml')
                urls = soup.find_all('url')

                for entry in urls[:15]:
                    title_node = entry.find(['news:title', 'title', 'image:title'])
                    if not title_node: continue
                    
                    title = title_node.text.strip()
                    link = entry.find('loc').text if entry.find('loc') else "#"

                    if title not in st.session_state.seen_headlines:
                        analysis = analyze_impact_with_ai(title)
                        st.session_state.seen_headlines.add(title)

                        # Logic: Only display a card if the AI confirms it is economic news
                        if analysis.get("significant"):
                            direction = analysis.get("direction", "neutral").lower()
                            impact = analysis.get("impact_level", "LESS").upper()
                            
                            # Color Mapping: Green/Red/Gray
                            color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                            # Visual Weight: 12px bar for HIGH, 3px for LESS
                            border_width = "12px" if impact == "HIGH" else "3px"

                            st.markdown(f"""
                                <div style="border-left: {border_width} solid {color}; padding: 15px; background: #161b22; margin-bottom: 10px; border-radius: 8px; border: 1px solid #30363d;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color:{color}; font-weight:bold; font-size:11px;">{impact} IMPACT • {direction.upper()}</span>
                                        <small style="color:gray;">{provider}</small>
                                    </div>
                                    <h4 style="margin:8px 0; color:white; font-size: 1.05rem;">{title}</h4>
                                    <p style="color:#c9d1d9; font-size:13px; line-height: 1.4;"><b>AI Analysis:</b> {analysis.get('reason')}</p>
                                    <a href="{link}" target="_blank" style="color:#58a6ff; font-size:11px; text-decoration:none; font-weight:bold;">READ SOURCE →</a>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Silently skip sports/entertainment noise
                            pass
            except Exception as e:
                st.write(f"⚠️ {provider} Error: {str(e)[:50]}")

# Sidebar
with st.sidebar:
    if st.button("Clear Dashboard & Re-scan"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
