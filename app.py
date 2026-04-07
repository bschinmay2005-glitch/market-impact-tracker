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
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Monitor")
# This caption now updates its own timestamp inside the fragment
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
    # NEW: More robust headers to avoid being blocked
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
                # Verify we actually got a 'Success' response
                if r.status_code != 200:
                    st.write(f"❌ {provider} blocked us (Status: {r.status_code})")
                    continue
                
                soup = BeautifulSoup(r.content, 'xml')
                entries = soup.find_all('url')
                
                if not entries:
                    st.write(f"⚠️ {provider}: Sitemap loaded but no <url> tags found.")
                    continue

                for entry in entries[:15]:
                    try:
                        # Find the title using any available tag
                        title_tag = entry.find(['news:title', 'title', 'image:title'])
                        if not title_tag: continue
                        
                        title = title_tag.text.strip()
                        link = entry.find('loc').text if entry.find('loc') else "#"
                        
                        st.write(f"[{provider}] Scanning: {title[:60]}...")

                        if title not in st.session_state.seen_headlines:
                            analysis = analyze_impact_with_ai(title)
                            
                            # FORCE DISPLAY: I've added 'or True' so you can see it working first
                            # Change back to 'if analysis.get("significant"):' once cards appear
                            if analysis.get("significant") or True: 
                                found_any = True
                                st.session_state.seen_headlines.add(title)
                                
                                direction = analysis.get("direction", "neutral")
                                color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                                
                                st.markdown(f"""
                                    <div style="border-left: 10px solid {color}; padding: 15px; background: #161b22; margin-bottom: 12px; border-radius: 8px;">
                                        <div style="display: flex; justify-content: space-between;">
                                            <span style="color:{color}; font-weight:bold; font-size:12px;">{analysis.get('impact_level', 'MID')} {direction.upper()}</span>
                                            <small style="color:gray;">{provider}</small>
                                        </div>
                                        <h4 style="margin:10px 0; color:white;">{title}</h4>
                                        <p style="color:#8b949e; font-size:13px;">{analysis.get('reason', 'Scanning market ripple effects...')}</p>
                                        <a href="{link}" target="_blank" style="color:#58a6ff; font-size:12px; text-decoration:none;">Read Full Story →</a>
                                    </div>
                                """, unsafe_allow_html=True)
                    except:
                        continue
            except Exception as e:
                st.write(f"⚠️ {provider} Error: {str(e)[:50]}")

    if not found_any and len(st.session_state.seen_headlines) == 0:
        st.info("Scanner Active. If this persists, the websites may be rate-limiting your IP.")

# --- SIDEBAR ---
with st.sidebar:
    st.header("Admin Controls")
    if st.button("Clear Cache & Force Re-scan"):
        st.session_state.seen_headlines = set()
        st.rerun()

news_dashboard()
