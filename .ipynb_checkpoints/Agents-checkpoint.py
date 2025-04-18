import streamlit as st
import openai
import json

# Load OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Agent: Summarization

def summarize_agent(title: str, full_text: str) -> str:
    """
    Summarizes the full article and returns a JSON string with keys:
      - title: article title
      - summary: list of bullet points
      - impact: describe impact on Indian stock markets
      - affected sectors: list of sectors
      - affected stocks: list of stocks
      - tone: Bullish | Bearish | Neutral
    """
    prompt = f"""
You are a financial journalist.
Article Title: {title}

Article Text:
""" + full_text + """

Provide the following in JSON format exactly:
{{
  "title": "{title}",
  "summary": ["point 1", "point 2", ...],
  "impact": "Describe potential impact on Indian stock markets.",
  "affected_sectors": ["Sector1", "Sector2", ...],
  "affected_stocks": ["Stock1", "Stock2", ...],
  "tone": "Bullish|Bearish|Neutral"
}}
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

# Agent: Aggregation

def aggregate_agent(summaries_json: str) -> str:
    """
    Takes a JSON array of article summary objects and returns a markdown string with:
    - Combined summaries under each article title
    - Outlook line per article indicating impact, affected sectors, and tone
    """
    prompt = f"""
You are a macro‑economic and financial news synthesizer.

INPUT: A JSON array of article summaries, where each object has:
- title
- summary (list of bullet points)
- impact (string)
- affected_sectors (list)
- affected_stocks (list)
- tone (Bullish/Bearish/Neutral)

Produce a **single** markdown report that, for **each article**, shows:

## Article Title
- summary point 1
- summary point 2
Outlook:
  - Impact: …
  - Affected Sectors: …
  - Affected Stocks: …
  - Tone: …

Return only the markdown content with **all** articles in order.
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()
