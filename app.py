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

def analyze_impact_with_ai(headline):
    """Uses deep reasoning to find economic meaning, not just keywords."""
    prompt = f"""
    Role: Senior Financial Analyst
    Analyze the economic impact of this headline for Indian Markets/Economy.
    Headline: "{headline}"
    
    1. Does this affect Nifty/Sensex, Global Oil, Fed Rates, or Indian Sectors?
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
    # Direct sitemaps for the fastest possible 'Live' detection
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    found_any = False

    # Expanding this will show you exactly what the scraper is reading
    with st.expander("🔍 Real-Time Scraper Activity Log", expanded=True):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                # Parse as XML specifically to handle namespaces correctly
                soup = BeautifulSoup(r.content, 'xml')
                
                # Search for tags with or without 'news:' prefix
                for entry in soup.find_all('url')[:20]:
                    news_tag = entry.find(['news:news', 'news'])
                    if not news_tag: continue
                    
                    title_tag = news_tag.find(['news:title', 'title'])
                    if not title_tag: continue
                    
                    title = title_tag.text.strip()
                    link = entry.find('loc').text
                    
                    # This ensures you see the scraper working
                    st.write(f"Reading {provider}: {title[:75]}...")

                    if title not in st.session_state.seen_headlines:
                        analysis = analyze_impact_with_ai(title)
                        
                        if analysis.get("significant"):
                            found_any = True
                            st.session_state.seen_headlines.add(title)
                            
                            # Card Display logic
                            color = "#28a745" if analysis["direction"] == "bullish" else "#dc3545"
                            st.markdown(f"""
                                <div style="border-left: 10px solid {color}; padding: 15px; background: #161b22; margin-bottom: 12px; border-radius: 8px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:11px;">
                                            {analysis['impact']} {analysis['direction'].upper()}
                                        </span>
                                        <small style="color:#8b949e;">{provider}</small>
                                    </div>
                                    <h3 style="color: white; margin: 0; font-size: 1.1rem;">{title}</h3>
                                    <p style="color:#8b949e; font-size:13px; font-style:italic; margin-top: 8px;">
                                        <strong>Analysis:</strong> {analysis['reason']}
                                    </p>
                                    <a href="{link}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 13px;">View Full Story →</a>
                                </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                # Use st.write inside fragments instead of st.toast/sidebar to prevent crashes
                st.write(f"⚠️ Connection glitch with {provider}")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner is active. Monitoring global & domestic sitemaps for impact...")

# --- MAIN UI SETUP ---
st.set_page_config(page_title="AI Market Monitor", layout="wide")
st.title("🏛️ AI High-Impact Market Monitor")
st.caption(f"System Live • Last Refresh: {datetime.now().strftime('%H:%M:%S')}")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# Sidebar is now kept static to prevent Fragment crashes
with st.sidebar:
    st.header("Scanner Settings")
    st.write("Real-time Economy & Global Macro Feed")
    if st.button("Reset Scanner & Clear Cache"):
        st.session_state.seen_headlines = set()
        st.rerun()

# Run the fragment
news_dashboard()
