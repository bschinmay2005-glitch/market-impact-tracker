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
    Role: Senior Financial Analyst
    Headline: "{headline}"
    Task: Return JSON only. "significant" MUST be true. 
    "impact_level" is HIGH for major Indian market moves, LOW for others.
    "direction" is bullish, bearish, or neutral.
    "reason": 1-sentence context.
    """
    try:
        response = ai_model.generate_content(prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"significant": True, "direction": "neutral", "impact_level": "LOW", "reason": "Market update."}

# --- UI SETUP ---
st.set_page_config(page_title="AI Market Shaker", layout="wide")
st.title("🏛️ Market Intelligence Terminal")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

@st.fragment(run_every=60)
def news_dashboard():
    # UPDATED 2026 PATHS
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/sitemap/sitemap-index.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    
    # ADVANCED HEADERS to bypass "403 Forbidden" or "404 Fake" errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

    found_new = False
    
    with st.expander("📡 Live Scraper Status", expanded=True):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code != 200:
                    st.error(f"❌ {provider} Status {r.status_code}. Retrying next pulse...")
                    continue
                
                soup = BeautifulSoup(r.content, 'xml')
                # Find all URL nodes
                urls = soup.find_all('url')
                
                # If it's a sitemap index (like Moneycontrol), we need to dive one level deeper
                if not urls and soup.find_all('sitemap'):
                    sub_url = soup.find('loc').text
                    r = requests.get(sub_url, headers=headers, timeout=10)
                    soup = BeautifulSoup(r.content, 'xml')
                    urls = soup.find_all('url')

                for entry in urls[:10]:
                    # Extract Title (Sitemaps use various tags)
                    title_node = entry.find(['news:title', 'title', 'image:title'])
                    if not title_node: continue
                    
                    title = title_node.text.strip()
                    link = entry.find('loc').text if entry.find('loc') else "#"

                    if title not in st.session_state.seen_headlines:
                        st.write(f"🟢 **{provider}**: {title[:70]}...")
                        analysis = analyze_impact_with_ai(title)
                        st.session_state.seen_headlines.add(title)
                        found_new = True
                        
                        # UI COLOR LOGIC
                        direction = analysis.get("direction", "neutral").lower()
                        color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                        impact = analysis.get("impact_level", "LOW").upper()
                        border = "12px" if impact == "HIGH" else "4px"
                        
                        st.markdown(f"""
                            <div style="border-left: {border} solid {color}; padding: 15px; background: #161b22; margin-bottom: 10px; border-radius: 8px;">
                                <div style="display: flex; justify-content: space-between;">
                                    <span style="color:{color}; font-weight:bold; font-size:12px;">{impact} IMPACT</span>
                                    <small style="color:gray;">{provider}</small>
                                </div>
                                <h4 style="margin:5px 0; color:white;">{title}</h4>
                                <p style="color:#8b949e; font-size:13px;">{analysis.get('reason')}</p>
                                <a href="{link}" target="_blank" style="color:#58a6ff; font-size:11px;">View Article →</a>
                            </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Connection issue with {provider}")

    if not found_new and len(st.session_state.seen_headlines) == 0:
        st.info("Searching for fresh market signals...")

# Sidebar for Reset
with st.sidebar:
    if st.button("Reset Scanner"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
