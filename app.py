import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 
IMPACT_KEYWORDS = ["RBI", "FED", "RELIANCE", "HDFC", "ADANI", "IPO", "MERGER", "INDIA", "MARKET", "STOCK", "US", "TRUMP", "WAR", "OIL", "TARIFF", "GLOBAL", "STRAIT", "GOLD", "SILVER", "BILLION", "TRILLION", "NSE", "NASDAQ", "FEDERAL", "RESERVE", "FII", "DII", "BANK", "RETURNS", "ELECTION", "CRORE",
    "ACQUISITION", "DEFAULT", "INFLATION", "GDP", "NIFTY", "SENSEX",
    "CRUDE", "SANCTION", "QUARTERLY RESULTS"]

# --- NEW: UPGRADED NOTIFICATION FUNCTION ---
# We put this here so the app knows how to send alerts before the dashboard starts
def send_ntfy_push(headline, link):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'),
            headers={
                "Title": "🚨 Market Impact Detected",
                "Click": link,
                "Priority": "5", 
                "Tags": "moneybag,warning"
            },
            timeout=5
        )
    except Exception as e:
        st.error(f"Notification Error: {e}")

# --- UI SETUP ---
st.set_page_config(page_title="Market Impact Tracker", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .news-card { border: 1px solid #D4AF37; padding: 15px; border-radius: 10px; margin-bottom: 20px; background-color: #161b22; }
    .time-stamp { color: #8899ac; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Live Market Archive")

if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE BACKGROUND MONITOR ---
@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    found_any = False
    
    for provider, url in sources.items():
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'xml')
            
            for entry in soup.find_all('url')[:20]: 
                news_tag = entry.find('news:news')
                if not news_tag: continue
                
                title = news_tag.find('news:title').text
                pub_date = news_tag.find('news:publication_date').text
                link = entry.find('loc').text
                
                img_tag = entry.find('image:loc')
                img_url = img_tag.text if img_tag else None
                
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                clean_time = dt.strftime("%b %d, %I:%M %p")

                if any(word in title.upper() for word in IMPACT_KEYWORDS):
                    found_any = True
                    
                    # --- NEW: TRIGGER THE NOTIFICATION ---
                    # This checks if we've already alerted you about this specific news
                    if title not in st.session_state.seen_headlines:
                        send_ntfy_push(title, link)
                        st.session_state.seen_headlines.add(title)
                    
                    # Display the News Card
                    with st.container():
                        st.markdown(f"---")
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            if img_url:
                                st.image(img_url, use_container_width=True)
                            else:
                                st.image("https://via.placeholder.com/150?text=No+Image", use_container_width=True)
                        
                        with col2:
                            st.caption(f"{provider} • {clean_time}")
                            st.subheader(title)
                            st.link_button("Read Full Story", link)

        except Exception as e:
            continue

    if not found_any:
        st.info("Watching the tickers... No major moves detected in the last minute.")

news_dashboard()
