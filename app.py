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
        "impact_level": "HIGH/LESS",
        "reason": "1-sentence link to Indian markets (e.g. Oil prices, FII flow, Sector impact)."
    }}
    
    Rule: 
    1. Set "significant" to true if it is global or domestic economic news.
    2. Set "impact_level" to "HIGH" only for major market movers; otherwise use "LESS".
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
        "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }
    found_any = False
    
    with st.expander("🔍 Scraper Live Feed (Debug)", expanded=True):
        st.write(f"Last Pulse: {datetime.now().strftime('%H:%M:%S')}")
        
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=15)
                if r.status_code != 200:
                    st.write(f"❌ {provider} blocked us (Status: {r.status_code})")
                    continue
                
                soup = BeautifulSoup(r.content, 'xml')
                entries = soup.find_all('url')
                
                if not entries:
                    st.write(f"⚠️ {provider}: No <url> tags found.")
                    continue

                for entry in entries[:15]:
                    try:
                        title_tag = entry.find(['news:title', 'title', 'image:title'])
                        if not title_tag: continue
                        
                        title = title_tag.text.strip()
                        link = entry.find('loc').text if entry.find('loc') else "#"
                        
                        st.write(f"[{provider}] Scanning: {title[:60]}...")

                        if title not in st.session_state.seen_headlines:
                            analysis = analyze_impact_with_ai(title)
                            
                            # --- INTELLIGENCE FILTER ---
                            if analysis.get("significant") == True: 
                                found_any = True
                                st.session_state.seen_headlines.add(title)
                                send_ntfy_push(title, link, analysis)
                                
                                # Color Logic
                                direction = analysis.get("direction", "neutral").lower()
                                if direction == "bullish":
                                    color = "#28a745" # Positive Green
                                    icon = "💹"
                                elif direction == "bearish":
                                    color = "#dc3545" # Negative Red
                                    icon = "🚨"
                                else:
                                    color = "#8b949e" # Neutral Gray
                                    icon = "⚖️"
                                
                                impact = analysis.get("impact_level", "LESS").upper()
                                # Visual distinction for High Impact
                                border_width = "15px" if impact == "HIGH" else "4px"

                                # Visual Display
                                st.markdown(f"""
                                    <div style="border-left: {border_width} solid {color}; padding: 20px; background: #161b22; margin-bottom: 15px; border-radius: 12px; border: 1px solid #30363d;">
                                        <div style="display: flex; justify-content: space-between; align-items: center;">
                                            <span style="background-color: {color}22; color: {color}; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; border: 1px solid {color}44;">
                                                {impact} IMPACT
                                            </span>
                                            <small style="color: #8b949e;">{provider} {icon}</small>
                                        </div>
                                        <h3 style="margin: 12px 0 8px 0; color: white; font-size: 1.15rem;">{title}</h3>
                                        <p style="color: #c9d1d9; font-size: 14px; line-height: 1.5;">
                                            <b>AI Assessment:</b> {analysis.get('reason')}
                                        </p>
                                        <div style="display: flex; gap: 15px; margin-top: 10px;">
                                            <a href="{link}" target="_blank" style="color: #58a6ff; font-size: 12px; text-decoration: none; font-weight: bold;">READ SOURCE →</a>
                                            <span style="color: {color}; font-size: 12px; font-weight: bold;">SENTIMENT: {direction.upper()}</span>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                    except:
                        continue
            except Exception as e:
                st.write(f"⚠️ {provider} Error: {str(e)[:50]}")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner Warming Up... Waiting for economic signals.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Admin Controls")
    if st.button("Clear Cache & Force Re-scan"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
