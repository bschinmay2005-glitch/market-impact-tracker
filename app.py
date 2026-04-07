import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CRITICAL CONFIG ---
# Replace with your actual Gemini API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')
NTFY_TOPIC = "chinmay_market_shaker_2026"

def analyze_impact_with_ai(headline):
    """
    The 'Brain': Evaluates Global/Domestic news for impact on India.
    Does not use keywords; uses financial reasoning.
    """
    prompt = f"""
    Role: Senior Financial Analyst (Indian Markets)
    Task: Analyze the economic impact of this headline.
    Headline: "{headline}"

    Return ONLY a JSON object:
    {{
        "significant": true/false,
        "direction": "bullish/bearish/neutral",
        "impact_level": "HIGH/MEDIUM/LOW",
        "reason": "1-sentence link to Indian markets (e.g. Oil prices, FII flow, Sector impact)."
    }}
    """
    try:
        response = ai_model.generate_content(prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"significant": False}

def send_ntfy_push(title, link, analysis):
    """Sends high-priority mobile alerts."""
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
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .news-card { padding: 20px; border-radius: 12px; margin-bottom: 15px; background-color: #161b22; border: 1px solid #30363d; }
    .bullish-card { border-left: 10px solid #28a745; }
    .bearish-card { border-left: 10px solid #dc3545; }
    .neutral-card { border-left: 10px solid #8b949e; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Monitor")
st.caption(f"Scanner Live • Sitemaps Active • {datetime.now().strftime('%H:%M:%S')}")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE SCANNER ---
@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    found_any = False
    
    # Activity Log to prove it is working
    with st.expander("🔍 Scraper Live Feed (Debug)", expanded=True):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                
                # We check the top 20 most recent URLs from each site
                for entry in soup.find_all('url')[:20]:
                    news_tag = entry.find(['news:news', 'news'])
                    if not news_tag: continue
                    
                    title_tag = news_tag.find(['news:title', 'title'])
                    if not title_tag: continue
                    
                    title = title_tag.text.strip()
                    link = entry.find('loc').text
                    
                    st.write(f"Reading: {title[:70]}...")

                    if title not in st.session_state.seen_headlines:
                        # AI intelligently decides if this is worth showing
                        analysis = analyze_impact_with_ai(title)
                        
                        if analysis.get("significant"):
                            found_any = True
                            st.session_state.seen_headlines.add(title)
                            send_ntfy_push(title, link, analysis)
                            
                            # UI Rendering
                            impact = analysis.get("impact_level", "LOW")
                            direction = analysis.get("direction", "neutral")
                            color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                            card_class = f"{direction}-card"

                            st.markdown(f"""
                                <div class="news-card {card_class}">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="background:{color}; color:white; padding:2px 8px; border-radius:4px; font-weight:bold; font-size:12px;">
                                            {impact} {direction.upper()}
                                        </span>
                                        <small style="color:#58a6ff;">{provider}</small>
                                    </div>
                                    <h3 style="color: white; margin-top: 10px;">{title}</h3>
                                    <p style="color: #8b949e; font-style: italic;"><b>AI Analysis:</b> {analysis.get('reason')}</p>
                                    <a href="{link}" target="_blank" style="color: #58a6ff; text-decoration: none;">View Full Details →</a>
                                </div>
                            """, unsafe_allow_html=True)
            except:
                st.write(f"⚠️ Failed to reach {provider}")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner is warming up. If this stays blank, click 'Clear Cache' in the sidebar.")

# --- SIDEBAR (Static) ---
with st.sidebar:
    st.header("Admin")
    if st.button("Clear Cache & Force Re-scan"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
