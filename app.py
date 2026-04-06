import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# --- CONFIGURATION ---
TELEGRAM_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHAT_ID = "YOUR_CHAT_ID_HERE"

IMPACT_KEYWORDS = [
    "RBI", "FED", "RELIANCE", "HDFC", "ADANI", "IPO", "MERGER", "INDIA", "MARKET", "STOCK", "RBI", "US", "TRUMP", "WAR", "OIL", "TARIFF", "GLOBAL", "STRAIT", "GOLD", "SILVER", "BILLION", "TRILLION", "NSE", "NASDAQ", "FEDERAL", "RESERVE", "FII", "DII", "BANK", "RETURNS", "ELECTION", "CRORE",
    "ACQUISITION", "DEFAULT", "INFLATION", "GDP", "NIFTY", "SENSEX",
    "CRUDE", "WAR", "SANCTION", "QUARTERLY RESULTS"
]

# --- HELPER FUNCTIONS ---
def send_telegram_push(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
    except:
        pass

# --- UI SETUP ---
st.set_page_config(page_title="Market Impact Tracker", layout="wide")
st.title("🏛️ Market-Moving News Archive")
st.subheader("Live Monitoring: Moneycontrol | Livemint | ET")

# --- DATA PROCESSING ---
# We use st.cache_resource to remember what we've already sent to your phone
if 'seen_headlines' not in st.session_state:
    st.session_state.seen_headlines = set()

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
                    # PUSH NOTIFICATION LOGIC
                    if title not in st.session_state.seen_headlines:
                        alert_text = f"🚨 *MARKET MOVE*\n\n{title}\n\n[Read More]({link})"
                        send_telegram_push(alert_text)
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
        st.info("Monitoring... Next scan in 60 seconds.")

news_dashboard()
