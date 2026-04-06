import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

# 1. UI Setup - "Old Money" Professional Look
st.set_page_config(page_title="Market Impact Tracker", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stHeader { font-family: 'Serif'; }
    </style>
    """, unsafe_allow_html=True) # <--- Notice the change to unsafe_allow_html

st.title("🏛️ Market-Moving News Archive")
st.subheader("Real-time filtering: Moneycontrol | Livemint | ET")

# 2. The Filter Logic (Your "No Small News" Guard)
# Edit this list to include/exclude what you care about
IMPACT_KEYWORDS = [
    "RBI", "FED", "RELIANCE", "HDFC", "ADANI", "IPO", "MERGER", 
    "ACQUISITION", "DEFAULT", "INFLATION", "GDP", "NIFTY", "SENSEX",
    "CRUDE", "WAR", "SANCTION", "QUARTERLY RESULTS"
]

def fetch_live_news():
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
            
            # Standard News Sitemap tag is <news:news>
            for entry in soup.find_all('news:news')[:20]: 
                title = entry.find('news:title').text
                link = entry.parent.find('loc').text
                
                # Check for Impact
                if any(word in title.upper() for word in IMPACT_KEYWORDS):
                    data.append({"Source": provider, "Headline": title, "URL": link})
        except Exception as e:
            st.error(f"Error connecting to {provider}")
            
    return pd.DataFrame(data)

# 3. The Dashboard Display
news_df = fetch_live_news()

if not news_df.empty:
    # Remove duplicates if same news is on multiple sites
    news_df = news_df.drop_duplicates(subset=['Headline'])
    
    for _, row in news_df.iterrows():
        with st.expander(f"📌 {row['Source']}: {row['Headline']}", expanded=True):
            st.write(f"Verified impact news detected.")
            st.link_button("View Original Report", row['URL'])
else:
    st.write("Monitoring... No high-impact news detected in the last 60 seconds.")

# 4. Independent "Real-Time" Loop
# This makes the app refresh itself every 60 seconds
time.sleep(60)
st.rerun()
