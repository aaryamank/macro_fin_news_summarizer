import streamlit as st
import json
from Fetchers import fetch_et_articles, fetch_snippet, fetch_full_text
from Agents import summarize_agent, aggregate_agent

st.set_page_config(page_title="News Swarm", layout="wide")
st.title("📰 Financial and Economic News Summarizer")

st.markdown("""
This app scrapes recent macro‑economic and financial news articles, 
summarizes each with GPT, and then generates a combined report.
""")

# 1. Fetch Articles
max_per_cat = st.sidebar.slider("Max articles per category", 1, 10, 5)
if st.sidebar.button("Fetch & Summarize"):
    with st.spinner("Fetching recent articles…"):
        raw_articles = fetch_et_articles(max_articles_per_category=max_per_cat)
    st.success(f"Fetched {len(raw_articles)} articles (up to {max_per_cat}/category).")
    
    # 2. Summarize Individually
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

    # 3. Aggregate
    with st.spinner("Aggregating into combined report…"):
        joint_md = aggregate_agent(json.dumps(summaries, indent=2))

    st.markdown("## Combined News Report")
    st.markdown(joint_md)

    # 4. List Referenced Articles
    st.markdown("### Referenced Articles")
    for art in raw_articles:
        st.write(f"- [{art['title']}]({art['url']})")

# 5. Instructions if not yet run
else:
    st.info("Click **Fetch & Summarize** in the sidebar to run the pipeline.")
