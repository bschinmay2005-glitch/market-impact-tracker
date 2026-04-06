import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 

# Pure Directional Sentiment (Market Language)
BULLISH_INDICATORS = ["SURGE", "JUMP", "PROFIT", "RECORDS", "GROWTH", "ACQUIRES", "BULLISH", "UP", "GAINS", "RECOVERY", "STIMULUS", "DIVIDEND", "RECORD", "BEATS", "HIKE"]
BEARISH_INDICATORS = ["CRASH", "PLUNGE", "LOSS", "DEBT", "FALL", "SLUMP", "BEARISH", "DOWN", "WAR", "SANCTION", "INFLATION", "DEFAULT", "LAYOFF", "DROPS", "CRUDE", "TARIFF"]

# The "High Volatility" Entities
MARKET_ENTITIES = ["RBI", "NIFTY", "SENSEX", "FED", "HDFC", "RELIANCE", "ADANI", "TATA", "SEBI", "IPO", "NSE", "NASDAQ", "GDP"]

# --- CRASH-PROOF NOTIFICATION SYSTEM ---
def send_ntfy_push(headline, link, impact_type):
    # No emojis in Title = No 'latin-1' error. 
    # Emojis go in Tags which are handled differently by the server.
    title_text = "MARKET IMPACT: POSITIVE" if impact_type == "bullish" else "MARKET IMPACT: NEGATIVE"
    tags = "rocket,chart_with_upwards_trend" if impact_type == "bullish" else "chart_with_downwards_trend,warning"
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'),
            headers={
                "Title": title_text,
                "Click": link,
                "Priority": "5", 
                "Tags": tags
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
    .news-card { padding: 22px; border-radius: 12px; margin-bottom: 25px; background-color: #161b22; border: 1px solid #30363d; transition: 0.3s; }
    
    /* Strong Visual Indicators for Market Direction */
    .positive-impact { border-left: 10px solid #28a745; border-top: 1px solid #28a745; box-shadow: 0px 4px 15px rgba(40, 167, 69, 0.1); }
    .negative-impact { border-left: 10px solid #dc3545; border-top: 1px solid #dc3545; box-shadow: 0px 4px 15px rgba(220, 53, 69, 0.1); }
    
    .badge-pos { background-color: #28a745; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
    .badge-neg { background-color: #dc3545; color: white; padding: 4px 12px; border-radius: 6px; font-weight: 800; font-size: 0.75rem; }
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
            
            # Scanning top 30 most recent stories
            for entry in soup.find_all('url')[:30]: 
                news_tag = entry.find('news:news')
                if not news_tag: continue
                
                title = news_tag.find('news:title').text
                link = entry.find('loc').text
                pub_date = news_tag.find('news:publication_date').text
                img_url = entry.find('image:loc').text if entry.find('image:loc') else "https://via.placeholder.com/150"
                
                # Relative Time Logic
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                diff = datetime.now(dt.tzinfo) - dt
                s = diff.total_seconds()
                clean_time = f"{int(s//60)}m ago" if s < 3600 else f"{int(s//3600)}h ago" if s < 86400 else dt.strftime("%b %d")

                # --- VOLATILITY FILTER ---
                title_up = title.upper()
                is_bullish = any(word in title_up for word in BULLISH_INDICATORS)
                is_bearish = any(word in title_up for word in BEARISH_INDICATORS)
                is_entity = any(word in title_up for word in MARKET_ENTITIES)

                # TRIGGER: Only show if an Entity is moving in a clear Direction
                if is_entity and (is_bullish or is_bearish):
                    found_impact = True
                    impact_direction = "bullish" if is_bullish else "bearish"
                    
                    if title not in st.session_state.seen_headlines:
                        send_ntfy_push(title, link, impact_direction)
                        st.session_state.seen_headlines.add(title)

                    # UI Logic
                    card_class = "positive-impact" if is_bullish else "negative-impact"
                    badge_html = '<span class="badge-pos">📈 POSITIVE IMPACT</span>' if is_bullish else '<span class="badge-neg">📉 NEGATIVE IMPACT</span>'

                    st.markdown(f'''
                        <div class="news-card {card_class}">
                            <div style="display: flex; gap: 20px; align-items: center;">
                                <div style="flex: 1;"><img src="{img_url}" style="width: 100%; border-radius: 8px; object-fit: cover; max-height: 120px;"></div>
                                <div style="flex: 3;">
                                    {badge_html} <span class="time-meta">{provider} • {clean_time}</span>
                                    <h3 style="margin: 12px 0; color: white; font-size: 1.2rem;">{title}</h3>
                                    <a href="{link}" target="_blank" style="text-decoration: none;">
                                        <button style="background: #30363d; color: white; border: 1px solid #444c56; padding: 6px 18px; border-radius: 6px; cursor: pointer; font-weight: 600;">Trade Analysis</button>
                                    </a>
                                </div>
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)

        except: continue
    
    if not found_impact:
        st.info("Scanning for significant market-moving events...")

news_dashboard()
