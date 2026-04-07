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
    Analyze if this headline affects Indian Markets/Economy (Domestic or International).
    Headline: "{headline}"
    Return ONLY JSON: {{"significant": true/false, "direction": "bullish/bearish", "reason": "why"}}
    """
    try:
        response = ai_model.generate_content(prompt)
        return json.loads(response.text.replace('```json', '').replace('```', '').strip())
    except:
        return {"significant": False}

@st.fragment(run_every=60)
def news_dashboard():
    # Use sitemaps for the fastest possible 'Live' news detection
    urls = ["https://www.moneycontrol.com/news/news-sitemap.xml", 
            "https://economictimes.indiatimes.com/sitemap_news.xml"]
    
    found_any = False
    with st.expander("🔍 Scraper Log", expanded=False):
        for url in urls:
            try:
                r = requests.get(url, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                for entry in soup.find_all('url')[:15]:
                    title = entry.find('news:title').text
                    if title not in st.session_state.seen_headlines:
                        analysis = analyze_impact_with_ai(title)
                        if analysis.get("significant"):
                            found_any = True
                            st.session_state.seen_headlines.add(title)
                            color = "#28a745" if analysis["direction"] == "bullish" else "#dc3545"
                            st.markdown(f"""
                                <div style="border-left: 10px solid {color}; padding: 15px; background: #161b22; margin-bottom: 10px; border-radius: 8px;">
                                    <h4 style="margin:0;">{title}</h4>
                                    <p style="color:{color}; font-size:12px;">{analysis.get('reason')}</p>
                                </div>
                            """, unsafe_allow_html=True)
            except:
                st.toast("Connection glitch... retrying.")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner Active. Waiting for market-moving news...")

# --- MAIN UI ---
st.set_page_config(page_title="AI Market Monitor", layout="wide")
st.title("🏛️ AI High-Impact Market Monitor")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# Fixed Sidebar Call: Call widgets OUTSIDE the fragment or use the 'with' block
with st.sidebar:
    st.write("Live Scanner Status: ✅")
    if st.button("Clear Cache"):
        st.session_state.seen_headlines = set()
        st.rerun()

# Run the dashboard in the main area
news_dashboard()
