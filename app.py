import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 

# These words represent "Movement"
BULLISH_WORDS = ["SURGE", "JUMP", "PROFIT", "RECORDS", "GROWTH", "ACQUIRES", "BULLISH", "UP", "GAINS", "RECOVERY", "STIMULUS", "DIVIDEND"]
BEARISH_WORDS = ["CRASH", "PLUNGE", "LOSS", "DEBT", "FALL", "SLUMP", "BEARISH", "DOWN", "WAR", "SANCTION", "INFLATION", "DEFAULT", "LAYOFF"]
MARKET_ENTITIES = ["RBI", "NIFTY", "SENSEX", "FED", "HDFC", "RELIANCE", "ADANI", "TATA", "SEBI", "IPO"]

# --- NOTIFICATION FUNCTION ---
def send_ntfy_push(headline, link, impact_type):
    emoji = "🚀" if impact_type == "bullish" else "📉" if impact_type == "bearish" else "📢"
    tags = "chart_with_upwards_trend" if impact_type == "bullish" else "chart_with_downwards_trend"
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'),
            headers={
                "Title": f"{emoji} Market Impact Alert",
                "Click": link,
                "Priority": "5", 
                "Tags": tags
            },
            timeout=5
        )
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="Market Impact Tracker", layout="wide")
st.markdown("""
    st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .news-card { padding: 20px; border-radius: 12px; margin-bottom: 20px; background-color: #161b22; border: 1px solid #30363d; }
    
    /* Green highlight for Positive news */
    .bullish-card { border-left: 8px solid #28a745; background-color: #101c12; border-top: 1px solid #28a745; }
    
    /* Red highlight for Negative news */
    .bearish-card { border-left: 8px solid #dc3545; background-color: #1c1010; border-top: 1px solid #dc3545; }
    
    .badge-green { background-color: #28a745; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    .badge-red { background-color: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.7rem; }
    .time-stamp { color: #8899ac; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)
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
            
            for entry in soup.find_all('url')[:25]: 
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

                # --- IMPACT DETECTION ENGINE ---
                title_up = title.upper()
                is_bullish = any(word in title_up for word in BULLISH_WORDS)
                is_bearish = any(word in title_up for word in BEARISH_WORDS)
                has_entity = any(word in title_up for word in MARKET_ENTITIES)

                # Only highlight if it's a Market Entity + a Sentiment word
                if has_entity and (is_bullish or is_bearish):
                    found_any = True
                    impact_type = "bullish" if is_bullish else "bearish"
                    
                    if title not in st.session_state.seen_headlines:
                        send_ntfy_push(title, link, impact_type)
                        st.session_state.seen_headlines.add(title)

                    # UI Styling
                    card_class = "bullish-card" if is_bullish else "bearish-card"
                    badge = f'<span class="badge-green">POSITIVE IMPACT</span>' if is_bullish else f'<span class="badge-red">NEGATIVE IMPACT</span>'

                    st.markdown(f'<div class="card {card_class}">', unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        st.image(img_url if img_url else "https://via.placeholder.com/150", use_container_width=True)
                    with col2:
                        st.markdown(f"{badge} <span class='time-stamp'>{provider} • {clean_time}</span>", unsafe_allow_html=True)
                        st.subheader(title)
                        st.link_button("View Analysis", link)
                    st.markdown('</div>', unsafe_allow_html=True)

        except: continue
    if not found_any: st.info("Monitoring markets for high-impact moves...")

news_dashboard()
