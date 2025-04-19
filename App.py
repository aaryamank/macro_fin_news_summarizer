### app.py ###
import streamlit as st
import json
from Fetchers import fetch_et_articles, fetch_snippet, fetch_full_text
from Agents import summarize_agent, aggregate_agent, executive_summary_agent

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