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
    Role: Financial Analyst. Headline: "{headline}"
    1. If NOT about economy/stocks/finance -> significant: false.
    2. If YES -> significant: true. 
    3. impact_level: "HIGH" (major movers) or "LESS" (minor).
    4. direction: "bullish" (Green) or "bearish" (Red).
    Return ONLY JSON: {{"significant":bool, "direction":str, "impact_level":str, "reason":str}}
    """
    try:
        response = ai_model.generate_content(prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"significant": False}

st.set_page_config(page_title="AI Market Shaker", layout="wide")
st.title("🏛️ AI Economic News Monitor")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE SCANNER ---
@st.fragment(run_every=60)
def news_dashboard():
    # 2026 Direct Sitemap URLs
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/sitemap/sitemap-index.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    
    # Modern browser headers to prevent 403 Forbidden
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'application/xml,text/xml,*/*'
    }

    found_new = False
    
    with st.expander("📡 Scanner Debug Console", expanded=True):
        st.write(f"Pulse Check: {datetime.now().strftime('%H:%M:%S')}")
        
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code != 200:
                    st.write(f"❌ {provider} blocked (Status {r.status_code})")
                    continue
                
                soup = BeautifulSoup(r.content, 'xml')
                # Sitemaps use <url> or <sitemap> tags
                items = soup.find_all(['url', 'sitemap'])
                
                # If Moneycontrol gives an index, we jump to the first actual sitemap link
                if provider == "Moneycontrol" and soup.find('sitemap'):
                    inner_url = soup.find('loc').text
                    r = requests.get(inner_url, headers=headers, timeout=10)
                    soup = BeautifulSoup(r.content, 'xml')
                    items = soup.find_all('url')

                st.write(f"✅ {provider}: Found {len(items)} potential links.")

                for entry in items[:15]:
                    title_node = entry.find(['news:title', 'title', 'image:title'])
                    if not title_node: continue
                    
                    title = title_node.text.strip()
                    link = entry.find('loc').text
                    
                    if title not in st.session_state.seen_headlines:
                        analysis = analyze_impact_with_ai(title)
                        st.session_state.seen_headlines.add(title)
                        
                        if analysis.get("significant"):
                            found_new = True
                            direction = analysis.get("direction", "neutral").lower()
                            impact = analysis.get("impact_level", "LESS").upper()
                            
                            # Green for Bullish, Red for Bearish
                            color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                            border = "12px" if impact == "HIGH" else "3px"

                            st.markdown(f"""
                                <div style="border-left: {border} solid {color}; padding: 15px; background: #161b22; margin-bottom: 10px; border-radius: 8px;">
                                    <span style="color:{color}; font-weight:bold; font-size:11px;">{impact} IMPACT</span>
                                    <h4 style="margin:5px 0; color:white;">{title}</h4>
                                    <p style="color:gray; font-size:13px;">{analysis.get('reason')}</p>
                                    <a href="{link}" target="_blank" style="color:#58a6ff; font-size:11px;">Source Link</a>
                                </div>
                            """, unsafe_allow_html=True)
            except:
                st.write(f"⚠️ {provider} connection timed out.")

    if not found_new and len(st.session_state.seen_headlines) > 0:
        st.info("No new high-impact economic news since last pulse.")

with st.sidebar:
    if st.button("Force Re-scan All"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
