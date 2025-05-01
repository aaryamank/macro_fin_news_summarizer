### app.py ###
import streamlit as st
import json
import time
import yfinance as yf
import pandas as pd
from Fetchers import fetch_et_articles, fetch_snippet, fetch_full_text
from Agents import summarize_agent, aggregate_agent, executive_summary_agent

def safe_fetch_yfinance(ticker, period="100d", interval="1d", retries=5, base_delay=2):
    """
    Tries to fetch Yahoo Finance data with retry + exponential backoff.
    Falls back to .history() if download() fails repeatedly.
    """
    for attempt in range(1, retries + 1):
        try:
            print(f"🔁 Attempt {attempt} for {ticker} using download()")
            df = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
            if df is not None and not df.empty:
                print("✅ Success via download()")
                return df
        except yf.shared._exceptions.YFRateLimitError as e:
            wait_time = base_delay * attempt
            print(f"⏳ Rate limited. Waiting {wait_time} sec (Attempt {attempt}/{retries})")
            for i in range(wait_time, 0, -1):
                print(f"   ⏱ {i} sec remaining...", end="\r")
                time.sleep(1)
        except Exception as e:
            print(f"⚠️ Error on download attempt {attempt}: {e}")
            time.sleep(base_delay * attempt)

    # Fallback to .history()
    try:
        print(f"⛑ Fallback to .history() for {ticker}")
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval)
        if df is not None and not df.empty:
            print("✅ Success via .history() fallback")
            return df
        else:
            print("⚠️ .history() returned empty")
    except Exception as e:
        print(f"❌ .history() failed: {e}")

    print(f"❌ Final failure: No data returned for {ticker}")
    return pd.DataFrame()
    

# Helper: fetch market data via yfinance
def fetch_market_data():
    symbols = {
        "S&P 500": "^GSPC",
        "Dow Jones Industrial Average": "^DJI",
        "Nifty 50": "^NSEI",
        "Sensex": "^BSESN",
        "USD/INR": "INR=X",
        "Gold": "GC=F",
        "US 10Y Treasury Yield": "^TNX"
    }

    records = []

    for name, sym in symbols.items():
        print(f"\n📊 Fetching {name} ({sym})")
        hist = safe_fetch_yfinance(sym, period="100d", interval="1d")

        if hist.empty or 'Close' not in hist.columns:
            print(f"⚠️ Skipping {name} — no data available.")
            current = prev_close = week_close = month_close = three_month_close = None
            day_pct = week_pct = month_pct = three_month_pct = None
        else:
            closes = hist['Close']
            current = closes.iloc[-1]
            prev_close = closes.iloc[-2] if len(closes) >= 2 else None
            week_close = closes.iloc[-6] if len(closes) >= 6 else None
            month_close = closes.iloc[-22] if len(closes) >= 22 else None
            three_month_close = closes.iloc[-64] if len(closes) >= 64 else None

            # Compute % changes
            day_pct = ((current - prev_close) / prev_close * 100) if prev_close else None
            week_pct = ((current - week_close) / week_close * 100) if week_close else None
            month_pct = ((current - month_close) / month_close * 100) if month_close else None
            three_month_pct = ((current - three_month_close) / three_month_close * 100) if three_month_close else None

        records.append({
            'Market': name,
            'Price': current,
            '1-Day Chg%': day_pct,
            '1-Week Chg%': week_pct,
            '1-Month Chg%': month_pct,
            '3-Month Chg%': three_month_pct
        })

        # Avoid hammering Yahoo Finance
        time.sleep(1.5)

    return pd.DataFrame(records)


st.set_page_config(page_title="News Swarm", layout="wide")
st.title("📰 Financial and Economic News Summarizer")

st.markdown("""
This app scrapes macro‑economic and financial news articles over the last 24 hours,
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
                print(f"❌ Failed to summarize '{art['title']}': {e}")
                continue  # Skip this article in output
    if not summaries:
        st.error("No summaries generated. Check your fetchers or API key.")
        st.stop()
    st.success(f"Generated {len(summaries)} summaries.")

    # 3. Executive Summary
    with st.expander("Executive Summary: 1-Page Overview of Key Articles with Sector Insights", expanded=False):
        # st.subheader("Live Market Update")
        # mkt_df = fetch_market_data()
        # st.dataframe(mkt_df)
        exec_md = executive_summary_agent(json.dumps(summaries, indent=2))
        # Escape dollar signs to prevent markdown math/font issues
        safe_exec_md = exec_md.replace("$", "\\$")
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