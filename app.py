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

# Keywords that trigger the "High Impact" glow and priority notifications
SUPER_IMPACT = ["WAR", "RBI", "CRASH", "BREAKING", "URGENT", "LEVY", "SURGE", "PLUNGE", "ISRAEL", "IRAN"]
# --- CONFIGURATION ---
NTFY_TOPIC = "chinmay_market_shaker_2026" 

# Things that move the price UP
BULLISH_WORDS = ["SURGE", "JUMP", "PROFIT", "GROWTH", "ACQUIRES", "BULLISH", "UP", "GAINS", "RECOVERY", "STIMULUS", "DIVIDEND", "RECORD", "BEATS"]

# Things that move the price DOWN
BEARISH_WORDS = ["CRASH", "PLUNGE", "LOSS", "DEBT", "FALL", "SLUMP", "BEARISH", "DOWN", "WAR", "SANCTION", "INFLATION", "DEFAULT", "LAYOFF", "DROPS"]

# The "Who" - only alert if these are mentioned
MARKET_ENTITIES = ["RBI", "FED", "RELIANCE", "HDFC", "ADANI", "TATA", "NIFTY", "SENSEX", "IPO", "STOCK", "NSE", "NASDAQ", "BANK", "GDP"]
# --- UPGRADED NOTIFICATION FUNCTION ---
def send_ntfy_push(headline, link, is_super=False):
    # We keep emojis in the 'Tags' and 'Priority' instead of the Title
    # This prevents the 'latin-1' encoding crash
    priority = "5" if is_super else "4"
    tags = "fire,warning" if is_super else "moneybag,warning"
    
    # We use a plain text Title to stay safe with the server
    title_text = "CRITICAL MARKET IMPACT" if is_super else "Market Impact Detected"
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'), # Headline is safely encoded here
            headers={
                "Title": title_text, 
                "Click": link,
                "Priority": priority, 
                "Tags": tags
            },
            timeout=5
        )
    except Exception as e:
        # This will now print to your Streamlit logs if there is a real network issue
        print(f"Notification System Error: {e}")

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
                img_url = entry.find('image:loc').text if entry.find('image:loc') else None
                
                # --- RELATIVE TIME LOGIC ---
                dt = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                now = datetime.now(dt.tzinfo)
                diff = now - dt
                seconds = diff.total_seconds()

                if seconds < 60:
                    clean_time = f"{int(seconds)}s ago"
                elif seconds < 3600:
                    clean_time = f"{int(seconds // 60)}m ago"
                elif seconds < 86400:
                    clean_time = f"{int(seconds // 3600)}h ago"
                else:
                    clean_time = dt.strftime("%b %d, %I:%M %p")

                # --- CHECK FOR IMPORTANCE ---
                is_super = any(word in title.upper() for word in SUPER_IMPACT)
                is_normal = any(word in title.upper() for word in IMPACT_KEYWORDS)

                if is_super or is_normal:
                    found_any = True
                    
                    if title not in st.session_state.seen_headlines:
                        send_ntfy_push(title, link, is_super)
                        st.session_state.seen_headlines.add(title)
                    
                    # Choose style based on impact level
                    card_class = "high-impact-card" if is_super else "news-card"
                    
                    # Display the Card
                    st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                    col1, col2 = st.columns([1, 3])
                    
                    with col1:
                        st.image(img_url if img_url else "https://via.placeholder.com/150", use_container_width=True)
                    
                    with col2:
                        badge = '<span class="impact-badge">🔥 HIGH IMPACT</span>' if is_super else ""
                        st.markdown(f"{badge}<span class='time-stamp'>{provider} • {clean_time}</span>", unsafe_allow_html=True)
                        st.subheader(title)
                        st.link_button("View Analysis", link)
                    st.markdown('</div>', unsafe_allow_html=True)

        except Exception as e:
            continue

    if not found_any:
        st.info("Watching the tickers... No major moves detected in the last minute.")

news_dashboard()
