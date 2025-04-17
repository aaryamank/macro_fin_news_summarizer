import os
import json
import openai
import streamlit as st

# Load OpenAI API key from Streamlit secrets
# Create a file `.streamlit/secrets.toml` in your project root with:
# OPENAI_API_KEY = "sk-..."
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Agent: Summarization

def summarize_agent(title: str, full_text: str) -> str:
    """
    Summarizes the full article and returns a JSON string with keys:
      - title: original title
      - summary: list of bullet points
      - impact: string describing potential impact on Indian stock markets
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
  "affected": ["Sector1", "Sector2", ...],
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
    - Combined summaries grouped under each article's shortened title
    - Under each title, a brief outlook using that article's impact and affected sectors
    """
    prompt = f"""
You are a macro-economic and financial news synthesizer.
The following is a JSON array of article summaries:
{summaries_json}

Please produce a markdown report with each article grouped under a shortened header of its title, followed by its summary bullet points and an "Outlook:" line that briefly states the impact and affected sectors.

For example:

## [Shortened Title]
- summary point 1
- summary point 2
Outlook: Describe impact on [sectors], tone is [Bullish/Bearish/Neutral].

Do this for each article in the input, preserving order. Return only the markdown content.
"""
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()
