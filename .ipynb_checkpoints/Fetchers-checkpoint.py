import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import dateutil.parser

# Economic Times category pages to scrape
ET_CATEGORIES = [
    "https://economictimes.indiatimes.com/news/economy/indicators",
    "https://economictimes.indiatimes.com/news/economy/foreign-trade",
    "https://economictimes.indiatimes.com/news/economy/articlelist/1286551815.cms",
    "https://economictimes.indiatimes.com/news/economy/infrastructure",
    "https://economictimes.indiatimes.com/news/economy/policy",
    "https://economictimes.indiatimes.com/news/company/corporate-trends",
    "https://economictimes.indiatimes.com/industry/banking/finance/banking",
    "https://economictimes.indiatimes.com/industry/banking-/-finance/banking",
    "https://economictimes.indiatimes.com/industry/cons-products/electronics",
    "https://economictimes.indiatimes.com/industry/cons-products/durables",
    "https://economictimes.indiatimes.com/industry/cons-products/fmcg",
    "https://economictimes.indiatimes.com/industry/services/retail",
    "https://economictimes.indiatimes.com/industry/healthcare/biotech/healthcare",
    "https://economictimes.indiatimes.com/industry/healthcare-/-biotech/biotech",
    "https://economictimes.indiatimes.com/industry/indl-goods/svs/engineering",
    "https://economictimes.indiatimes.com/industry/auto/auto-news/articlelist/64829342.cms"
]


def parse_et_date(published_str):
    """
    Parse Economic Times date string into a datetime object.
    ET dates often look like 'Aug 10, 2023, 12:30 PM IST'.
    """
    try:
        # Remove timezone label if present
        cleaned = published_str.replace(' IST', '')
        return dateutil.parser.parse(cleaned)
    except Exception:
        return None


def fetch_et_articles(category_urls=None, max_articles_per_category=5):
    """
    Scrape article links and metadata from Economic Times category pages,
    returning only those published within the last 24 hours.

    Args:
        category_urls (list): List of ET category page URLs. Defaults to ET_CATEGORIES.
        max_articles_per_category (int): Limit per category.

    Returns:
        List of dicts: [{'title':..., 'url':..., 'published': datetime}, ...]
    """
    urls = category_urls or ET_CATEGORIES
    cutoff = datetime.utcnow() - timedelta(days=1)
    articles = []

    for cat_url in urls:
        try:
            resp = requests.get(cat_url, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            story_blocks = soup.select('div.eachStory') or soup.select('li.article') or []
            count = 0
            for block in story_blocks:
                if count >= max_articles_per_category:
                    break
                a = block.find('a', href=True)
                if not a:
                    continue
                title = a.get_text(strip=True)
                link = a['href']
                if link.startswith('/'):
                    link = 'https://economictimes.indiatimes.com' + link

                time_tag = block.find('time') or block.find('span', class_='time')
                pub_str = time_tag.get_text(strip=True) if time_tag else ''
                pub_dt = parse_et_date(pub_str)

                # Skip if date parse failed or older than cutoff
                if not pub_dt or pub_dt < cutoff:
                    continue

                articles.append({
                    'title': title,
                    'url': link,
                    'published': pub_dt
                })
                count += 1
        except Exception:
            continue
    return articles


def fetch_snippet(url, max_chars=300):
    """
    Fetch a short snippet (for filtering) from the article page.

    Args:
        url (str): Article URL.
        max_chars (int): Maximum characters in snippet.

    Returns:
        str: Text snippet.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        # New ET pages often have article body in div with class 'Normal'
        paragraphs = soup.select('div.Normal p') or soup.find_all('p')
        text = ''
        for p in paragraphs:
            p_text = p.get_text(strip=True)
            if p_text:
                text += p_text + ' '
            if len(text) >= max_chars:
                break
        return text[:max_chars]
    except Exception:
        return ''


def fetch_full_text(url):
    """
    Fetch the full text of an article page.

    Args:
        url (str): Article URL.

    Returns:
        str: Full article text.
    """
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        paragraphs = soup.select('div.Normal p') or soup.find_all('p')
        full_text = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        return full_text
    except Exception:
        return ''


