import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURATION ---
# Replace with your actual API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')
NTFY_TOPIC = "chinmay_market_shaker_2026"

def analyze_impact_with_ai(headline):
    """
    Acts as a Senior Financial Analyst to interpret the 'meaning' 
    and ripple effects of global and domestic news.
    """
    prompt = f"""
    Role: Senior Financial Analyst
    Task: Analyze the economic impact of this headline for an Indian Investor.
    Headline: "{headline}"

    Instructions:
    1. Evaluate impact on: Indian Economy, Nifty/Sensex, Global Macro (Oil, Fed, Gold), or specific sectors.
    2. Even if it's international (e.g. Iran, China, US), determine the ripple effect on India.
    3. Categorize impact: HIGH, MEDIUM, or LOW.
    4. Determine direction: BULLISH (Positive) or BEARISH (Negative).

    Return ONLY JSON:
    {{
        "significant": true,
        "direction": "bullish/bearish/neutral",
        "impact_level": "HIGH/MEDIUM/LOW",
        "reason": "1-sentence explanation of the specific link to Indian markets."
    }}
    """
    try:
        response = ai_model.generate_content(prompt)
        # Clean the response to ensure valid JSON
        res_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(res_text)
    except:
        return {"significant": False}

def send_ntfy_push(title, link, analysis):
    """Sends high-priority mobile alerts via ntfy.sh"""
    try:
        priority = "5" if analysis.get("impact_level") == "HIGH" else "3"
        tag = "rotating_light" if analysis.get("direction") == "bearish" else "rocket"
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

# --- UI SETUP ---
st.set_page_config(page_title="AI Market Shaker 2026", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .news-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; background-color: #161b22; border: 1px solid #30363d; }
    .bullish-border { border-left: 10px solid #28a745; }
    .bearish-border { border-left: 10px solid #dc3545; }
    .neutral-border { border-left: 10px solid #8b949e; }
    .reason-text { color: #8b949e; font-style: italic; font-size: 0.9rem; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Monitor")
st.caption(f"Status: Live Scanning Sitemaps • Last Refresh: {datetime.now().strftime('%H:%M:%S')}")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

@st.fragment(run_every=60)
def news_dashboard():
    # Using Sitemaps is the fastest way - no Google News delay.
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    found_any = False
    
    # We display a log to show the scraper is working in real-time
    with st.expander("🔍 Scraper Activity Log", expanded=False):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                # Grab the 20 most recent URLs
                for entry in soup.find_all('url')[:20]:
                    news_tag = entry.find('news:news')
                    if not news_tag: continue
                    
                    title = news_tag.find('news:title').text.strip()
                    link = entry.find('loc').text
                    
                    st.write(f"Reading: {title[:70]}...")

                    if title not in st.session_state.seen_headlines:
                        # AI Reasoning Step
                        analysis = analyze_impact_with_ai(title)
                        
                        # We only skip if the AI explicitly says it's not significant 
                        # (e.g. lifestyle news, sports, etc.)
                        if analysis.get("significant"):
                            found_any = True
                            st.session_state.seen_headlines.add(title)
                            send_ntfy_push(title, link, analysis)
                            
                            # UI Rendering
                            impact = analysis.get("impact_level", "LOW")
                            direction = analysis.get("direction", "neutral")
                            color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                            border_class = f"{direction}-border"

                            st.markdown(f"""
                                <div class="news-card {border_class}">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:12px;">
                                            {impact} {direction.upper()}
                                        </span>
                                        <span style="color:#58a6ff; font-size:12px;">{provider}</span>
                                    </div>
                                    <h3 style="color: white; margin-top: 10px;">{title}</h3>
                                    <p class="reason-text"><strong>AI Analysis:</strong> {analysis.get('reason')}</p>
                                    <a href="{link}" target="_blank" style="color: #58a6ff; text-decoration: none; font-size: 14px;">Read Source Story →</a>
                                </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                continue

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner Active. Watching for global and domestic economic shifts...")

# --- MAIN UI EXECUTION ---
with st.sidebar:
    st.header("Control Panel")
    st.write("Target: International & Domestic Economy")
    if st.button("Clear Dashboard"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
