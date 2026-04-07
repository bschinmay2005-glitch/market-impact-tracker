import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CRITICAL CONFIG ---
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')
NTFY_TOPIC = "chinmay_market_shaker_2026"

def analyze_impact_with_ai(headline):
    prompt = f"""
    Role: Senior Financial Analyst
    Headline: "{headline}"

    Task:
    1. If this is NOT about the economy, stock markets, or macro-policy (e.g., Sports, IPL, Entertainment) -> set "significant": false.
    2. If it IS news related to global or domestic economy -> set "significant": true.
    3. impact_level: "HIGH" for major movers, "LESS" for minor economic updates.
    4. direction: "bullish" (Positive), "bearish" (Negative), or "neutral".

    Return ONLY JSON:
    {{
        "significant": true/false,
        "direction": "bullish/bearish/neutral",
        "impact_level": "HIGH/LESS",
        "reason": "1-sentence link to economic impact."
    }}
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
st.caption(f"Scanner Live • Economic Filter Active • {datetime.now().strftime('%H:%M:%S')}")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE SCANNER ---
@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    found_any = False
    
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
                            found_any = True
                            send_ntfy_push(title, link, analysis)
                            
                            # Color & Border Logic
                            direction = analysis.get("direction", "neutral").lower()
                            color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                            
                            impact = analysis.get("impact_level", "LESS").upper()
                            border_width = "12px" if impact == "HIGH" else "3px"

                            st.markdown(f"""
                                <div style="border-left: {border_width} solid {color}; padding: 20px; background: #161b22; margin-bottom: 15px; border-radius: 8px; border: 1px solid #30363d;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="color: {color}; font-weight: bold; font-size: 11px;">
                                            {impact} IMPACT • {direction.upper()}
                                        </span>
                                        <small style="color: #8b949e;">{provider}</small>
                                    </div>
                                    <h3 style="margin: 10px 0; color: white; font-size: 1.1rem;">{title}</h3>
                                    <p style="color: #c9d1d9; font-size: 14px;"><b>Context:</b> {analysis.get('reason')}</p>
                                    <a href="{link}" target="_blank" style="color: #58a6ff; font-size: 12px; text-decoration: none; font-weight: bold;">VIEW SOURCE →</a>
                                </div>
                            """, unsafe_allow_html=True)
            except Exception as e:
                st.write(f"⚠️ {provider} Error")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Admin")
    if st.button("Reset Scanner"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
