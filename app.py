import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 

BULLISH_WORDS = ["SURGE", "JUMP", "PROFIT", "RECORDS", "GROWTH", "ACQUIRES", "BULLISH", "UP", "GAINS", "RECOVERY", "STIMULUS", "DIVIDEND"]
BEARISH_WORDS = ["CRASH", "PLUNGE", "LOSS", "DEBT", "FALL", "SLUMP", "BEARISH", "DOWN", "WAR", "SANCTION", "INFLATION", "DEFAULT", "LAYOFF"]
MARKET_ENTITIES = ["RBI", "NIFTY", "SENSEX", "FED", "HDFC", "RELIANCE", "ADANI", "TATA", "SEBI", "IPO", "MARKET", "STOCK"]

# --- NOTIFICATION FUNCTION (CLEANED) ---
def send_ntfy_push(headline, link, impact_type):
    # Emojis in Title cause the latin-1 error. Use plain text here.
    title_text = "Market Impact: Positive" if impact_type == "bullish" else "Market Impact: Negative" if impact_type == "bearish" else "Market News Alert"
    
    # Emojis are safe in Tags
    tag_map = {"bullish": "rocket", "bearish": "chart_with_downwards_trend", "neutral": "newspaper"}
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'),
            headers={
                "Title": title_text,
                "Click": link,
                "Priority": "4", 
                "Tags": tag_map.get(impact_type, "newspaper")
            },
            timeout=5
        )
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="Market Impact Tracker", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .news-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; background-color: #161b22; border: 1px solid #30363d; min-height: 150px; }
    .bullish-card { border-left: 8px solid #28a745; border-top: 1px solid #28a745; }
    .bearish-card { border-left: 8px solid #dc3545; border-top: 1px solid #dc3545; }
    .neutral-card { border-left: 8px solid #8899ac; }
    .badge-green { background-color: #28a745; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    .badge-red { background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    .badge-gray { background-color: #444c56; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    .time-stamp { color: #8899ac; font-size: 0.8rem; margin-left: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Live Market Archive")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    found_any = False
    for provider, url in sources.items():
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'xml')
            
            for entry in soup.find_all('url')[:30]: 
                news_tag = entry.find('news:news')
                if not news_tag: continue
                
                title = news_tag.find('news:title').text
                link = entry.find('loc').text
                pub_date = news_tag.find('news:publication_date').text
                img_url = entry.find('image:loc').text if entry.find('image:loc') else None
                
                # Time Logic
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                diff = datetime.now(dt.tzinfo) - dt
                s = diff.total_seconds()
                clean_time = f"{int(s//60)}m ago" if s < 3600 else f"{int(s//3600)}h ago" if s < 86400 else dt.strftime("%b %d")

                # --- NEW IMPACT DETECTION ---
                title_up = title.upper()
                is_bullish = any(word in title_up for word in BULLISH_WORDS)
                is_bearish = any(word in title_up for word in BEARISH_WORDS)
                has_entity = any(word in title_up for word in MARKET_ENTITIES)

                # Show it if it matches an entity OR a movement word
                if has_entity or is_bullish or is_bearish:
                    found_any = True
                    impact_type = "bullish" if is_bullish else "bearish" if is_bearish else "neutral"
                    
                    if title not in st.session_state.seen_headlines:
                        send_ntfy_push(title, link, impact_type)
                        st.session_state.seen_headlines.add(title)

                    # UI Styling
                    card_style = "bullish-card" if impact_type == "bullish" else "bearish-card" if impact_type == "bearish" else "neutral-card"
                    badge = '<span class="badge-green">POSITIVE</span>' if impact_type == "bullish" else '<span class="badge-red">NEGATIVE</span>' if impact_type == "bearish" else '<span class="badge-gray">MARKET NEWS</span>'

                    st.markdown(f'''
                        <div class="news-card {card_style}">
                            <div style="display: flex; gap: 20px;">
                                <div style="flex: 1;"><img src="{img_url if img_url else "https://via.placeholder.com/150"}" style="width: 100%; border-radius: 8px;"></div>
                                <div style="flex: 3;">
                                    {badge} <span class="time-stamp">{provider} • {clean_time}</span>
                                    <h3 style="margin-top: 10px; color: white;">{title}</h3>
                                    <a href="{link}" target="_blank" style="text-decoration: none;"><button style="background: #30363d; color: white; border: 1px solid #8899ac; padding: 5px 15px; border-radius: 5px; cursor: pointer;">Read Full Story</button></a>
                                </div>
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)

        except Exception as e:
            continue
            
    if not found_any:
        st.info("Searching for market-moving updates...")

news_dashboard()
