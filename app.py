import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import google.generativeai as genai
from datetime import datetime

# --- CONFIG ---
# Replace with your actual Gemini API Key
genai.configure(api_key="YOUR_GEMINI_API_KEY")
ai_model = genai.GenerativeModel('gemini-1.5-flash')
NTFY_TOPIC = "chinmay_market_shaker_2026"

def analyze_impact_with_ai(headline):
    prompt = f"""
    Role: Senior Financial Analyst (Indian Markets)
    Task: Analyze the economic impact of this headline.
    Headline: "{headline}"

    Return ONLY a JSON object:
    {{
        "significant": true/false,
        "direction": "bullish/bearish/neutral",
        "impact_level": "HIGH/LESS",
        "reason": "1-sentence link to Indian markets."
    }}
    
    Rule: 
    1. Set "significant" to true if it is global or domestic economic/business news.
    2. Set "impact_level" to "HIGH" only for major market movers; otherwise use "LESS".
    """
    try:
        response = ai_model.generate_content(prompt)
        raw = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except:
        return {"significant": False}

# --- UI STYLE ---
st.set_page_config(page_title="AI Market Shaker 2026", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h3 { margin-bottom: 0px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ AI High-Impact Market Monitor")
st.caption(f"Live Scanner | Last Update: {datetime.now().strftime('%H:%M:%S')}")

# --- THE SCANNER & DISPLAY ENGINE ---
sources = {
    "Moneycontrol": "https://www.moneycontrol.com/news/news-sitemap.xml",
    "Economic Times": "https://economictimes.indiatimes.com/etstatic/sitemaps/et/news/sitemap-today.xml"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# We use an expander just for the logs so they don't clutter the screen
with st.expander("🔍 Scraper Activity Logs", expanded=False):
    st.write("Fetching latest sitemaps...")

    for provider, url in sources.items():
        try:
            r = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(r.content, 'xml')
            entries = soup.find_all('url')[:20] # Scan top 20 news items

            for entry in entries:
                title_tag = entry.find(['news:title', 'title', 'image:title'])
                if not title_tag: continue
                
                title = title_tag.text.strip()
                link = entry.find('loc').text if entry.find('loc') else "#"
                
                st.write(f"Analyzing: {title[:70]}...")
                
                # Run AI Analysis
                analysis = analyze_impact_with_ai(title)
                
                # ONLY IF SIGNIFICANT ECONOMY NEWS -> DISPLAY CARD
                if analysis.get("significant"):
                    direction = analysis.get("direction", "neutral").lower()
                    impact = analysis.get("impact_level", "LESS").upper()
                    
                    # Color & Visual Logic
                    color = "#28a745" if direction == "bullish" else "#dc3545" if direction == "bearish" else "#8b949e"
                    icon = "💹" if direction == "bullish" else "🚨" if direction == "bearish" else "⚖️"
                    
                    # 15px for HIGH, 4px for LESS
                    border_width = "15px" if impact == "HIGH" else "4px"

                    # Print the card directly to the main UI (outside the expander)
                    st.markdown(f"""
                        <div style="border-left: {border_width} solid {color}; padding: 20px; background: #161b22; margin-bottom: 15px; border-radius: 12px; border: 1px solid #30363d;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <span style="background-color: {color}22; color: {color}; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: bold; border: 1px solid {color}44;">
                                    {impact} IMPACT
                                </span>
                                <small style="color: #8b949e;">{provider} {icon}</small>
                            </div>
                            <h3 style="margin: 12px 0 8px 0; color: white; font-size: 1.15rem; font-weight: 600;">{title}</h3>
                            <p style="color: #c9d1d9; font-size: 14px; line-height: 1.5;">
                                <b>AI Assessment:</b> {analysis.get('reason')}
                            </p>
                            <div style="display: flex; gap: 15px; margin-top: 10px;">
                                <a href="{link}" target="_blank" style="color: #58a6ff; font-size: 12px; text-decoration: none; font-weight: bold;">READ SOURCE →</a>
                                <span style="color: {color}; font-size: 12px; font-weight: bold;">SENTIMENT: {direction.upper()}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error fetching {provider}: {e}")

# Sidebar Refresh
if st.sidebar.button("Force Re-Scan Now"):
    st.rerun()
