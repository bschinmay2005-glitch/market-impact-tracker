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
    
    with st.expander("🔍 Scraper Live Feed (Debug)", expanded=True):
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                
                # LOOP START
                for entry in soup.find_all('url')[:20]:
                    try: # This is the 'try' that was causing the IndentationError
                        news_tag = entry.find(['news:news', 'news'])
                        if not news_tag: 
                            continue
                        
                        title_tag = news_tag.find(['news:title', 'title'])
                        if not title_tag: 
                            continue
                        
                        title = title_tag.text.strip()
                        link = entry.find('loc').text
                        
                        st.write(f"[{provider}] Scanning: {title[:75]}...")

                        if title not in st.session_state.seen_headlines:
                            analysis = analyze_impact_with_ai(title)
                            
                            if analysis.get("significant"):
                                found_any = True
                                st.session_state.seen_headlines.add(title)
                                send_ntfy_push(title, link, analysis)
                                
                                direction = analysis.get("direction", "neutral")
                                color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                                
                                st.markdown(f"""
                                    <div style="border-left: 10px solid {color}; padding: 15px; background: #161b22; margin-bottom: 12px; border-radius: 8px;">
                                        <h4 style="margin:0; color:white;">{title}</h4>
                                        <p style="color:{color}; font-size:13px; margin-top:8px;"><b>{analysis.get('impact_level')} IMPACT:</b> {analysis.get('reason')}</p>
                                    </div>
                                """, unsafe_allow_html=True)
                    except Exception as inner_e:
                        continue # Skip individual bad headlines

            except Exception as outer_e:
                st.write(f"⚠️ [{provider}] Connection Error: {str(outer_e)[:50]}...")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner is warming up. No high-impact events identified in current batch.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Admin")
    if st.button("Clear Cache & Force Re-scan"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
