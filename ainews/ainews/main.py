#!/usr/bin/env python3
import os
import requests
from google_news import GoogleNews  # Adjust the module name/path if necessary
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

API_KEY = os.getenv("API_KEY", "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")

def scrape_article(url: str) -> str:
    """
    Apre la pagina con Selenium, bypassa il banner dei cookie cercando un elemento
    il cui testo contiene "accetta" e poi estrae il testo principale dell'articolo.
    """
    # Configura Selenium per usare Chrome in modalità headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--log-level=3")  # Riduce la verbosità dei log

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        
        # Lista di possibili selettori basati sul contenuto (case insensitive) che contiene "accetta"
        cookie_selectors = [
            # Seleziona un <button> che contiene "accetta"
            (By.XPATH, "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta')]"),
            # Seleziona un <a> che contiene "accetta"
            (By.XPATH, "//a[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'accetta')]")
        ]
        
        banner_cliccato = False
        for how, selector in cookie_selectors:
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((how, selector))
                )
                cookie_button.click()
                print(f"Banner dei cookie bypassato cliccando l'elemento trovato con {how}='{selector}'")
                banner_cliccato = True
                time.sleep(1)  # attesa per far registrare l'interazione
                break
            except TimeoutException:
                continue  # Se il selettore non trova nulla, passa al successivo
        
        if not banner_cliccato:
            print("Banner dei cookie non trovato o già gestito.")
        
        # Attendi ulteriormente per il caricamento completo della pagina
        time.sleep(2)
        html = driver.page_source

    except Exception as e:
        driver.quit()
        return f"Error fetching the URL: {e}"

    driver.quit()

    # Parsing dell'HTML renderizzato con BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(["script", "style", "noscript", "header", "footer", "aside", "nav"]):
        tag.decompose()
    
    MIN_LENGTH = 200  # Lunghezza minima per considerare valido il testo dell'articolo

    # 1. Prova a cercare il contenuto nell'elemento <article>
    article_tag = soup.find('article')
    if article_tag:
        text = article_tag.get_text(separator='\n', strip=True)
        if text and len(text) > MIN_LENGTH:
            return text

    # 2. Prova con alcuni selettori comuni per il contenuto dell'articolo
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

    # 3. Fallback: cerca il blocco di testo più grande tra <div> o <section>
    largest_text = ""
    containers = soup.find_all(['div', 'section'])
    for container in containers:
        text = container.get_text(separator='\n', strip=True)
        if text and len(text) > len(largest_text):
            largest_text = text
    if largest_text and len(largest_text) > MIN_LENGTH:
        return largest_text

    # 4. Fallback finale: unisci tutti i tag <p>
    paragraphs = soup.find_all('p')
    if paragraphs:
        content = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        if content and len(content) > MIN_LENGTH:
            return content

    return "No article content found."

def sum_up_article(article: str) -> str:
    """
    Sintetizza l'articolo usando un servizio di IA.
    """
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Sintetizza il seguente articolo:\n"
                    f"{article}"
                )
            },
        ],
    }

    print("Sending request to external API...")

    api_url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(api_url, headers=headers, json=payload)

    if response.status_code != 200:
        return f"Error: {response.text}"
    
    data = response.json()


    summary = data.get("choices", [{}])[0].get("message", {}).get("content", "No content found.")

    return summary

def main():
    # Create an instance of GoogleNews (using default language and country)
    gn = GoogleNews()

    try:
        # Get the top news entries and take only the first three
        top_news_response = gn.top_news()
        top_entries = top_news_response.get('entries', [])[:5]
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

        article_content = scrape_article(url)
        # Add the scraped content to the entry object (you can choose any key name; here we use 'content')
        entry['content'] = article_content
        full_articles.append(entry)



    # Sum up the articles using an AI service
    for idx, article in enumerate(full_articles, start=1):
        print(f"\nArticle {idx}: {article.get('title')}")
        summary = sum_up_article(article.get('content'))
        print(f"Summary: {summary}")
        

if __name__ == '__main__':
    main()
