import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 

# Broadened to capture geopolitical moves that affect the market
BULLISH_INDICATORS = ["SURGE", "JUMP", "PROFIT", "RECORDS", "GROWTH", "ACQUIRES", "UP", "GAINS", "STIMULUS", "DIVIDEND", "BEATS", "RECOVERY"]
BEARISH_INDICATORS = ["CRASH", "PLUNGE", "LOSS", "DEBT", "FALL", "SLUMP", "DOWN", "WAR", "SANCTION", "INFLATION", "DEFAULT", "LAYOFF", "DROPS", "SCRAMBLES", "AMIDST"]
# Entities and context words that make news "Market-Related"
MARKET_ENTITIES = ["RBI", "NIFTY", "SENSEX", "FED", "HDFC", "RELIANCE", "ADANI", "TATA", "SEBI", "IPO", "NSE", "NASDAQ", "GDP", "BILLION", "TRILLION", "UAE", "IRAN", "USA", "INDIA", "OIL", "GOLD"]

# --- THE "SAFE" NOTIFICATION FUNCTION ---
def send_ntfy_push(headline, link, impact_type):
    # REMOVE ALL EMOJIS from the string to prevent latin-1 errors
    # This regex strips out everything except standard text/numbers
    clean_headline = re.sub(r'[^\x00-\x7f]',r'', headline)
    
    title_text = "MARKET ALERT: POSITIVE" if impact_type == "bullish" else "MARKET ALERT: NEGATIVE"
    
    # We use simple text tags instead of emoji icons to be 100% safe
    safe_tags = "success,chart" if impact_type == "bullish" else "warning,skull"
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=clean_headline.encode('utf-8'),
            headers={
                "Title": title_text,
                "Click": link,
                "Priority": "5", 
                "Tags": safe_tags
            },
            timeout=5
        )
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="High-Impact Market Tracker", layout="wide")
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

st.title("🏛️ High-Impact Market Archive")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    found_impact = False
    for provider, url in sources.items():
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'xml')
            
            for entry in soup.find_all('url')[:40]: # Checking more stories
                news_tag = entry.find('news:news')
                if not news_tag: continue
                
                title = news_tag.find('news:title').text
                link = entry.find('loc').text
                pub_date = news_tag.find('news:publication_date').text
                img_url = entry.find('image:loc').text if entry.find('image:loc') else "https://via.placeholder.com/150"
                
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                diff = datetime.now(dt.tzinfo) - dt
                s = diff.total_seconds()
                clean_time = f"{int(s//60)}m ago" if s < 3600 else f"{int(s//3600)}h ago" if s < 86400 else dt.strftime("%b %d")

                title_up = title.upper()
                is_bullish = any(word in title_up for word in BULLISH_INDICATORS)
                is_bearish = any(word in title_up for word in BEARISH_INDICATORS)
                is_entity = any(word in title_up for word in MARKET_ENTITIES)

                # TRIGGER: Entity + Direction OR just a very high-impact geopolitical word
                if (is_entity and (is_bullish or is_bearish)) or ("WAR" in title_up) or ("CRISIS" in title_up):
                    found_impact = True
                    impact_direction = "bullish" if is_bullish else "bearish"
                    
                    if title not in st.session_state.seen_headlines:
                        send_ntfy_push(title, link, impact_direction)
                        st.session_state.seen_headlines.add(title)

                    card_class = "positive-impact" if is_bullish else "negative-impact"
                    badge_text = "📈 POSITIVE IMPACT" if is_bullish else "📉 NEGATIVE IMPACT"
                    badge_class = "badge-pos" if is_bullish else "badge-neg"

                    st.markdown(f'''
                        <div class="news-card {card_class}">
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
        st.info("Scanning for significant market-moving events...")

news_dashboard()
