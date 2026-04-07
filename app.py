import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CONFIG ---
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_impact_with_ai(headline):
    prompt = f"""
    Role: Financial Analyst. 
    Headline: "{headline}"
    
    Task:
    1. If this is NOT about the economy, stock markets, or global business (e.g. Sports, IPL, Celebs) -> set "significant": false.
    2. If it IS related to global/domestic economy -> set "significant": true.
    3. impact_level: "HIGH" for major movers, "LESS" for minor economic updates.
    4. direction: "bullish" (Positive), "bearish" (Negative), or "neutral".

    Return ONLY JSON: 
    {{"significant": bool, "direction": "bullish/bearish/neutral", "impact_level": "HIGH/LESS", "reason": "1-sentence context"}}
    """
    try:
        response = ai_model.generate_content(prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"significant": False}

# --- UI STYLE ---
st.set_page_config(page_title="AI Market Shaker", layout="wide")
st.title("🏛️ AI Economic News Monitor")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE SCANNER ---
@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/sitemap/sitemap-index.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    found_any = False
    
    with st.expander("🔍 Scraper Live Feed (Debug)", expanded=True):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                items = soup.find_all(['url', 'sitemap'])
                
                # Moneycontrol Index handling
                if provider == "Moneycontrol" and soup.find('sitemap'):
                    r = requests.get(soup.find('loc').text, headers=headers)
                    soup = BeautifulSoup(r.content, 'xml')
                    items = soup.find_all('url')

                st.write(f"✅ {provider}: Found {len(items)} potential links.")

                for entry in items[:20]: # Check more links to find signals
                    title_node = entry.find(['news:title', 'title', 'image:title'])
                    if not title_node: continue
                    
                    title = title_node.text.strip()
                    link = entry.find('loc').text
                    
                    if title not in st.session_state.seen_headlines:
                        analysis = analyze_impact_with_ai(title)
                        st.session_state.seen_headlines.add(title)
                        
                        if analysis.get("significant"):
                            found_any = True
                            direction = analysis.get("direction", "neutral").lower()
                            impact = analysis.get("impact_level", "LESS").upper()
                            
                            # Color & Border Logic
                            color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                            border_width = "12px" if impact == "HIGH" else "3px"

                            st.markdown(f"""
                                <div style="border-left: {border_width} solid {color}; padding: 18px; background: #161b22; margin-bottom: 12px; border-radius: 8px; border: 1px solid #30363d;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: {color}; font-weight: bold; font-size: 11px;">
                                            {impact} IMPACT • {direction.upper()}
                                        </span>
                                        <small style="color: gray;">{provider}</small>
                                    </div>
                                    <h4 style="margin: 8px 0; color: white;">{title}</h4>
                                    <p style="color: #c9d1d9; font-size: 13px;">{analysis.get('reason')}</p>
                                    <a href="{link}" target="_blank" style="color: #58a6ff; font-size: 11px; text-decoration: none; font-weight: bold;">VIEW SOURCE →</a>
                                </div>
                            """, unsafe_allow_html=True)
            except:
                continue

    if not found_any and len(st.session_state.seen_headlines) > 0:
        st.info("Searching for fresh high-impact signals...")

news_dashboard()
