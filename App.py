### app.py ###
import streamlit as st
import json
import yfinance as yf
import pandas as pd
from Fetchers import fetch_et_articles, fetch_snippet, fetch_full_text
from Agents import summarize_agent, aggregate_agent, executive_summary_agent

# Helper: fetch market data via yfinance
def fetch_market_data():
    symbols = {
        "S&P 500": "^GSPC",
        "Dow Jones Industrial Average": "^DJI",
        "Nifty 50": "^NSEI",
        "Nifty 500": "^CNX500",
        "USD/INR": "INR=X",
        "Gold": "GC=F",
        "US 10Y Treasury Yield": "^TNX"
    }
    records = []
    for name, sym in symbols.items():
        try:
            ticker = yf.Ticker(sym)
            # Fetch recent history for day-ago and week-ago closes
            hist = ticker.history(period="8d")
            if hist.empty:
                raise ValueError("No history data")
            # Use last available close as current proxy
            current_price = hist['Close'][-1]
            prev_close = hist['Close'][-2] if len(hist) >= 2 else None
            week_ago_close = hist['Close'][-6] if len(hist) >= 6 else None
            # Calculate changes
            day_change = current_price - prev_close if prev_close else None
            week_change = current_price - week_ago_close if week_ago_close else None
            day_pct = (day_change / prev_close * 100) if prev_close else None
            week_pct = (week_change / week_ago_close * 100) if week_ago_close else None
        except Exception:
            current_price = prev_close = week_ago_close = None
            day_change = week_change = day_pct = week_pct = None
        records.append({
            'Market': name,
            'Price': current_price,
            'Day Change': day_change,
            'Day %': day_pct,
            'Week Change': week_change,
            'Week %': week_pct
        })
    return pd.DataFrame(records)

st.set_page_config(page_title="News Swarm", layout="wide")
st.title("📰 Financial and Economic News Summarizer")

st.markdown("""
This app scrapes recent macro‑economic and financial news articles,
summarizes each with GPT, generates an executive overview, and then presents detailed article summaries and sources in separate sections.
""")

# Sidebar controls
max_per_cat = st.sidebar.slider("Max articles per category", 1, 10, 5)
if st.sidebar.button("Fetch & Summarize"):
    # 1. Fetch
    with st.spinner("Fetching recent articles…"):
        raw_articles = fetch_et_articles(max_articles_per_category=max_per_cat)
    st.success(f"Fetched {len(raw_articles)} articles (up to {max_per_cat}/category).")

    # 2. Summarize individually
    summaries = []
    for art in raw_articles:
        with st.spinner(f"Summarizing: {art['title'][:50]}…"):
            full = fetch_full_text(art['url'])
            try:
                summ_json = json.loads(summarize_agent(art['title'], full))
                summaries.append(summ_json)
            except Exception as e:
                st.warning(f"Failed to summarize '{art['title']}': {e}")
    if not summaries:
        st.error("No summaries generated. Check your fetchers or API key.")
        st.stop()
    st.success(f"Generated {len(summaries)} summaries.")

    # 3. Executive Summary
    with st.expander("Executive Summary: 1-Page Overview of Key Articles with Sector Insights", expanded=False):
        st.subheader("Live Market Update")
        mkt_df = fetch_market_data()
        st.dataframe(mkt_df)
        exec_md = executive_summary_agent(json.dumps(summaries, indent=2))
        # Escape dollar signs to prevent markdown math/font issues
        safe_exec_md = exec_md.replace("$", "\$")
        st.markdown(safe_exec_md)

    # 4. Summary of Articles (3-4 bullets each, no outlook or metadata)
    with st.expander("Summary of Articles", expanded=False):
        for summ in summaries:
            # Escape dollar signs to prevent markdown math/font issues
            safe_title = summ['title'].replace("$", "\$")
            st.markdown(f"### {safe_title}")
            for point in summ.get('summary', [])[:4]:
                safe_point = point.replace("$", "\$")
                st.markdown(f"- {safe_point}")

    # 5. Sources
    with st.expander("Sources of Articles", expanded=False):
        for art in raw_articles:
            # Escape dollar signs in article titles
            safe_art_title = art['title'].replace("$", "\$")
            st.write(f"- [{safe_art_title}]({art['url']})")

else:
    st.info("Click **Fetch & Summarize** in the sidebar to run the pipeline.")