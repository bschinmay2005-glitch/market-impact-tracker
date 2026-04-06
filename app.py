import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# 1. UI Setup
st.set_page_config(page_title="Market Impact Tracker", layout="wide")

# Custom CSS for the "Old Money" Dark Theme
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stHeader { font-family: 'Serif'; color: #D4AF37; }
    div[data-testid="stExpander"] { border: 1px solid #D4AF37; background-color: #161b22; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Market-Moving News Archive")
st.subheader("Real-time filtering: Moneycontrol | Livemint | ET")

# 2. Filter Logic
IMPACT_KEYWORDS = [
    "RBI", "FED", "RELIANCE", "HDFC", "ADANI", "IPO", "MERGER", "INDIA", "MARKET", 
    "STOCK", "US", "TRUMP", "WAR", "OIL", "TARIFF", "GLOBAL", "STRAIT", "GOLD", 
    "SILVER", "BILLION", "TRILLION", "NSE", "NASDAQ", "FEDERAL", "RESERVE", "FII", 
    "DII", "BANK", "RETURNS", "ELECTION", "CRORE", "ACQUISITION", "DEFAULT", 
    "INFLATION", "GDP", "NIFTY", "SENSEX", "CRUDE", "SANCTION", "QUARTERLY RESULTS"
]

# 3. The "Silent" Background Monitor (The Fragment)
@st.fragment(run_every=60)
def news_dashboard():
    sources = {
        "Moneycontrol": "https://www.moneycontrol.com/news/sitemap/sitemap-news.xml",
        "Livemint": "https://www.livemint.com/sitemap/news.xml",
        "Economic Times": "https://economictimes.indiatimes.com/sitemap_news.xml"
    }
    
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Create a container so we can clear and update it
    container = st.empty()
    
    with container.container():
        for provider, url in sources.items():
            try:
                r = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(r.content, 'xml')
                
                # Fetching latest 20
                for entry in soup.find_all('news:news')[:20]: 
                    title = entry.find('news:title').text
                    link = entry.parent.find('loc').text
                    
                    if any(word in title.upper() for word in IMPACT_KEYWORDS):
                        data.append({"Source": provider, "Headline": title, "URL": link})
            except:
                st.warning(f"Connection slow for {provider}...")

        if data:
            news_df = pd.DataFrame(data).drop_duplicates(subset=['Headline'])
            for _, row in news_df.iterrows():
                with st.expander(f"📌 {row['Source']}: {row['Headline']}", expanded=True):
                    st.write(f"High-impact movement detected.")
                    st.link_button("Open Source Report", row['URL'])
        else:
            st.info("Monitoring... No high-impact news detected in this cycle.")

# 4. Launch the Dashboard
news_dashboard()
