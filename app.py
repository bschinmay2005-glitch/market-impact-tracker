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

# --- UPGRADED NOTIFICATION FUNCTION ---
def send_ntfy_push(headline, link, is_super=False):
    # If super impact, use Priority 5 (Max) and Fire emoji
    priority = "5" if is_super else "4"
    tags = "fire,warning" if is_super else "moneybag,warning"
    title_text = "🔥 CRITICAL IMPACT" if is_super else "Market Impact Detected"
    
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'),
            headers={
                "Title": title_text,
                "Click": link,
                "Priority": priority, 
                "Tags": tags
            },
            timeout=5
        )
    except Exception as e:
        st.error(f"Notification System Error: {e}")

# --- UI SETUP ---
st.set_page_config(page_title="Market Impact Tracker", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    
    /* Standard Card Style */
    .news-card { 
        border: 1px solid #30363d; 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 25px; 
        background-color: #161b22; 
    }
    
    /* HIGH IMPACT Card Style (Gold Glow) */
    .high-impact-card { 
        border: 2px solid #D4AF37; 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 25px; 
        background-color: #1c1910; 
        box-shadow: 0px 0px 20px rgba(212, 175, 55, 0.2);
    }
    
    .time-stamp { color: #8899ac; font-size: 0.85rem; }
    .impact-badge { 
        background-color: #D4AF37; 
        color: #000000; 
        padding: 2px 10px; 
        border-radius: 4px; 
        font-weight: bold; 
        font-size: 0.75rem;
        margin-right: 10px;
    }
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
