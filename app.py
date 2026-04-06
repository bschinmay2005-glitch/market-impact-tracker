import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- CONFIGURATION ---
# Use the EXACT same name you typed in the ntfy app
NTFY_TOPIC = "chinmay_market_shaker_2026" 

IMPACT_KEYWORDS = [
    "RBI", "FED", "RELIANCE", "HDFC", "ADANI", "IPO", "MERGER", "INDIA", "MARKET", "STOCK", "RBI", "US", "TRUMP", "WAR", "OIL", "TARIFF", "GLOBAL", "STRAIT", "GOLD", "SILVER", "BILLION", "TRILLION", "NSE", "NASDAQ", "FEDERAL", "RESERVE", "FII", "DII", "BANK", "RETURNS", "ELECTION", "CRORE",
    "ACQUISITION", "DEFAULT", "INFLATION", "GDP", "NIFTY", "SENSEX",
    "CRUDE", "WAR", "SANCTION", "QUARTERLY RESULTS"
]

# --- NOTIFICATION FUNCTION ---
def send_ntfy_push(headline, link):
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=headline.encode('utf-8'),
            headers={
                "Title": "🚨 Market Alert",
                "Click": link,
                "Priority": "high",
                "Tags": "moneybag,chart_with_upwards_trend"
            }
        )
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="Market Impact Tracker", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stHeader { font-family: 'Serif'; color: #D4AF37; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Market-Moving News Archive")

# Memory system so you don't get 100 alerts for the same news
if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

# --- THE BACKGROUND MONITOR ---
@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/sitemap/sitemap-news.xml",
        "Livemint": "https://www.livemint.com/sitemap/news.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for provider, url in sources.items():
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.content, 'xml')
            for entry in soup.find_all('news:news')[:15]: 
                title = entry.find('news:title').text
                link = entry.parent.find('loc').text
                
                # Check for Impact
                if any(word in title.upper() for word in IMPACT_KEYWORDS):
                    # Only send push if we haven't seen this EXACT headline before
                    if title not in st.session_state.seen_headlines:
                        send_ntfy_push(title, link)
                        st.session_state.seen_headlines.add(title)
                    
                    data.append({"Source": provider, "Headline": title, "URL": link})
        except:
            continue

    if data:
        news_df = pd.DataFrame(data).drop_duplicates(subset=['Headline'])
        for _, row in news_df.iterrows():
            with st.expander(f"📌 {row['Source']}: {row['Headline']}", expanded=True):
                st.link_button("Open Source Report", row['URL'])
    else:
        st.info("Monitoring... System is active in the background.")

news_dashboard()
