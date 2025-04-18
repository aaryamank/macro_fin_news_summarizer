import streamlit as st
import json
import openai
from Fetchers import fetch_et_articles, fetch_snippet, fetch_full_text
from Agents import summarize_agent, aggregate_agent

# Streamlit page config
st.set_page_config(page_title="News Swarm", layout="wide")
st.title("📰 Financial and Economic News Summarizer")

st.markdown("""
This app scrapes recent macro‑economic and financial news articles,  
summarizes each with GPT, and then generates a combined report.
""")

# ——— Helper: Chunked aggregation ———
def chunked_aggregate(summaries, chunk_size=20, model="gpt-3.5-turbo"):
    """
    Breaks the list of summary dicts into batches of size `chunk_size`,
    calls `aggregate_agent` on each batch to get partial markdown reports,
    then merges those partials into one final markdown doc via a GPT call.
    """
    partial_reports = []
    for i in range(0, len(summaries), chunk_size):
        batch = summaries[i : i + chunk_size]
        batch_json = json.dumps(batch, indent=2)
        partial_md = aggregate_agent(batch_json)
        partial_reports.append(partial_md.strip())

    # Now stitch them together
    merge_prompt = (
        "You are a macro‑economic and financial news synthesizer.\n"
        "Combine the following partial markdown reports into one unified markdown document, "
        "deduplicating any repeated points. Return only the final markdown:\n\n"
        + "\n\n".join(partial_reports)
    )
    resp = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": merge_prompt}],
        temperature=0.4,
    )
    return resp.choices[0].message.content.strip()


# ——— Sidebar & Fetching ———
max_per_cat = st.sidebar.slider("Max articles per category", 1, 10, 5)
if st.sidebar.button("Fetch & Summarize"):
    with st.spinner("1️⃣ Fetching recent articles…"):
        raw_articles = fetch_et_articles(max_articles_per_category=max_per_cat)
    st.success(f"Fetched {len(raw_articles)} articles (up to {max_per_cat}/category).")

    # ——— Summarize each article ———
    summaries = []
    for art in raw_articles:
        with st.spinner(f"✍️ Summarizing: {art['title'][:50]}…"):
            full = fetch_full_text(art["url"])
            try:
                summ_json = json.loads(summarize_agent(art["title"], full))
                summaries.append(summ_json)
            except Exception as e:
                st.warning(f"Failed to summarize '{art['title']}': {e}")

    if not summaries:
        st.error("No summaries generated. Check your fetchers or API key.")
        st.stop()
    st.success(f"✅ Generated {len(summaries)} summaries.")

    # ——— Chunked aggregation ———
    with st.spinner("🔗 Aggregating into combined report…"):
        joint_md = chunked_aggregate(summaries, chunk_size=20, model="gpt-3.5-turbo")

    st.markdown("## Combined News Report")
    st.markdown(joint_md)

    # ——— List referenced articles ———
    st.markdown("### Referenced Articles")
    for art in raw_articles:
        st.write(f"- [{art['title']}]({art['url']})")

else:
    st.info("Click **Fetch & Summarize** in the sidebar to run the pipeline.")