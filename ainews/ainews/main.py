#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from google_news import GoogleNews  # Adjust the module name/path if necessary

import requests
from bs4 import BeautifulSoup

def scrape_article(url: str) -> str:
    """
    Given a URL, fetch the page content and attempt to extract the main article text.

    :param url: The URL of the article to scrape.
    :return: The scraped article text or an error message.
    """
    try:
        response = requests.get(url, timeout=10)

        response.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching the URL: {e}"
    
    # Parse the HTML
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Remove tags that usually contain non-article content.
    for tag in soup(["script", "style", "noscript", "header", "footer", "aside", "nav"]):
        tag.decompose()
    
    MIN_LENGTH = 200  # minimum number of characters for valid article text

    # 1. Try using the <article> tag.
    article_tag = soup.find('article')
    if article_tag:
        text = article_tag.get_text(separator='\n', strip=True)
        if text and len(text) > MIN_LENGTH:
            return text

    # 2. Try common selectors that are often used for article content.
    candidate_selectors = [
        "div[itemprop='articleBody']",
        "div[class*='article-content']",
        "div[class*='post-content']",
        "div[class*='entry-content']",
        "section[class*='article']",
        "div[id*='content']",
        "div[class*='main-content']"
    ]
    
    for selector in candidate_selectors:
        candidate = soup.select_one(selector)
        if candidate:
            text = candidate.get_text(separator='\n', strip=True)
            if text and len(text) > MIN_LENGTH:
                return text

    # 3. As a fallback, look for the largest text block within <div> or <section> tags.
    largest_text = ""
    containers = soup.find_all(['div', 'section'])
    for container in containers:
        text = container.get_text(separator='\n', strip=True)
        # Update if this container has more text than previous ones.
        if text and len(text) > len(largest_text):
            largest_text = text
    if largest_text and len(largest_text) > MIN_LENGTH:
        return largest_text

    # 4. Final fallback: join all <p> tags.
    paragraphs = soup.find_all('p')
    if paragraphs:
        content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        if content and len(content) > MIN_LENGTH:
            return content

    return "No article content found."

def main():
    # Create an instance of GoogleNews (using default language and country)
    gn = GoogleNews()

    try:
        # Get the top news entries and take only the first three
        top_news_response = gn.top_news()
        top_entries = top_news_response.get('entries', [])[:30]
    except Exception as e:
        print(f"Error retrieving top news: {e}")
        return

    full_articles = []

    # Process each entry by scraping the full article text
    for entry in top_entries:
        
        print(f"Entry: {entry.get('title')}")

        url = entry.get('link')
        if not url:
            print("No URL found for entry; skipping.")
            continue

        print(f"Scraping article from: {url}")
        article_content = scrape_article(url)
        # Add the scraped content to the entry object (you can choose any key name; here we use 'content')
        entry['content'] = article_content
        full_articles.append(entry)

    # Print out the full objects (original data plus scraped content)
    for idx, article in enumerate(full_articles, start=1):
        print("=" * 80)
        print(f"Article #{idx}")
        print(f"Title: {article.get('title')}")
        print(f"Publisher: {article.get('publisher')}")
        print(f"URL: {article.get('url')}")
        print("Content:")
        print(article.get('content'))
        print("=" * 80)
        print("\n")

if __name__ == '__main__':
    main()
