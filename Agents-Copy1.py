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
      - affected: list of sectors/stocks
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
  "affected": ["Industry1", "Industry2", ...],
  "affected": ["Stock1", "Stock2", ...],
  "tone": "Bullish|Bearish|Neutral"
}}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
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
You are a macro-economic and financial news synthesizer.
The following is a JSON array of article summaries:
{summaries_json}

Please produce a markdown report with each article grouped under its title as a header, followed by its summary bullet points and an "Outlook:" line stating impact, affected sectors (if no clear-cut industries then display N/A), affected stocks (if none then display N/A) and tone.

Return only the markdown content.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()


# Executive summary agent (new)
def executive_summary_agent(summaries_json: str) -> str:
    prompt = f"""
You are a senior financial analyst tasked with writing a one-page executive summary.
Given the following JSON array of article summaries:
{summaries_json}

Craft a concise, structured, 1-page overview organized by key sectors (e.g., Macroeconomic Updates, Banking & Financial Services, Real Estate & Infrastructure, Power & Energy, Services, Industrial Goods & Services, IT & Telecom, Pharma, Auto).
Each section should highlight top bullet points and sector-specific insights.
This should be followed by an Sector-Specific Analysis sub-section which has Bullish, Bearish and Neutral sections with the appropriate corresponding sectors for each based on your overall analysis of each sector based on its respective article summaries.
Return only the markdown content for the executive summary.
"""
    response = openai.ChatCompletion.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()
