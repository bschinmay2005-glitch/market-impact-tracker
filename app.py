import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import json
import google.generativeai as genai

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 

# Setup Gemini - Replace with your actual API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_impact_with_ai(headline):
    prompt = f"""
    Analyze this news headline for its impact on the Indian Stock Market: "{headline}"
    
    1. Is it a significant market mover?
    2. Is the impact Bullish (Positive) or Bearish (Negative)?
    3. Is it High impact (market-shaking) or Low impact (sector-specific)?

    Return ONLY JSON:
    {{"significant": true, "direction": "bullish", "impact": "HIGH"}}
    """
    try:
        response = ai_model.generate_content(prompt)
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except:
        return {"significant": False}

# --- THE NOTIFICATION FUNCTION ---
def send_ntfy_push(headline, link, direction, impact_level):
    clean_headline = re.sub(r'[^\x00-\x7f]', r'', headline)
    
    # Priority 5 (Red Alert) for High Impact, 3 for Low
    priority = "5" if impact_level == "HIGH" else "3"
    title_text = f"[{impact_level}] MARKET {direction.upper()}"
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=clean_headline.encode('utf-8'),
            headers={
                "Title": title_text,
                "Click": link,
                "Priority": priority, 
                "Tags": "rotating_light,chart" if impact_level == "HIGH" else "loudspeaker"
            },
            timeout=5
        )
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="High-Impact AI Market Tracker", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .news-card { padding: 22px; border-radius: 12px; margin-bottom: 25px; background-color: #161b22; border: 1px solid #30363d; }
    .positive-impact { border-left: 10px solid #28a745; border-top: 1px solid #28a745; }
    .negative-impact { border-left: 10px solid #dc3545; border-top: 1px solid #dc3545; }
    .badge-pos { background-color: #28a745; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 0.75rem; }
    .badge-neg { background-color: #dc3545; color: white; padding: 4px 12px; border-radius: 6px; font-weight: bold; font-size: 0.75rem; }
    .time-meta { color: #8899ac; font-size: 0.85rem; margin-left: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Archive")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/.xml",
        "Moneycontrol": "https://www.moneycontrol.com/news/business/markets/.xml",
        "Moneycontrol": "https://www.moneycontrol.com/news/business/economy/.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    found_impact = False
    for provider, url in sources.items():
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'xml')
            
            for entry in soup.find_all('url')[:20]: # AI is slower, so we check the latest 20
                news_tag = entry.find('news:news')
                if not news_tag: continue
                
                title = news_tag.find('news:title').text
                # TEMPORARY TEST: Force a domestic/international headline
                title = "RBI surprises market with 50bps rate cut; Titagarh Rail hits 20% upper circuit"
                link = entry.find('loc').text
                pub_date = news_tag.find('news:publication_date').text
                img_url = entry.find('image:loc').text if entry.find('image:loc') else "https://via.placeholder.com/150"
                
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                diff = datetime.now(dt.tzinfo) - dt
                s = diff.total_seconds()
                clean_time = f"{int(s//60)}m ago" if s < 3600 else f"{int(s//3600)}h ago" if s < 86400 else dt.strftime("%b %d")

                # --- STEP 3: THE AI ANALYST (REPLACED KEYWORDS) ---
                if title not in st.session_state.seen_headlines:
                    analysis = analyze_impact_with_ai(title)
                
                    if analysis.get("significant"):
                        found_impact = True
                        direction = analysis["direction"]
                        impact_level = analysis["impact"]
                        
                        send_ntfy_push(title, link, direction, impact_level)
                        st.session_state.seen_headlines.add(title)

                        # UI Display Logic
                        card_class = "positive-impact" if direction == "bullish" else "negative-impact"
                        badge_text = f"{impact_level} {direction.upper()} IMPACT"
                        badge_class = "badge-pos" if direction == "bullish" else "badge-neg"
                        glow = "box-shadow: 0px 0px 20px rgba(255, 255, 255, 0.15);" if impact_level == "HIGH" else ""

                        st.markdown(f'''
                            <div class="news-card {card_class}" style="{glow}">
                                <div style="display: flex; gap: 20px; align-items: center;">
                                    <div style="flex: 1;"><img src="{img_url}" style="width: 100%; border-radius: 8px;"></div>
                                    <div style="flex: 3;">
                                        <span class="{badge_class}">{badge_text}</span> <span class="time-meta">{provider} • {clean_time}</span>
                                        <h3 style="margin: 12px 0; color: white;">{title}</h3>
                                        <a href="{link}" target="_blank" style="text-decoration: none;">
                                            <button style="background: #30363d; color: white; border: 1px solid #444c56; padding: 8px 20px; border-radius: 6px; cursor: pointer;">View Impact Analysis</button>
                                        </a>
                                    </div>
                                </div>
                            </div>
                        ''', unsafe_allow_html=True)
        except: continue
    
    if not found_impact:
        st.info("AI is scanning for significant market-moving events...")

news_dashboard()
