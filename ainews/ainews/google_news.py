import feedparser
from bs4 import BeautifulSoup
import urllib.parse
from dateparser import parse as parse_date
import requests
from typing import List, Optional, Dict, Any, Union


class GoogleNews:
    """
    A class to interact with Google News RSS feeds, allowing retrieval of top news,
    topic-specific headlines, geo-specific headlines, and search results.
    """

    BASE_RSS_URL = 'https://news.google.com/rss'

    def __init__(self, language: str = 'it', country: str = 'IT') -> None:
        """
        Initialize the GoogleNews instance with specified language and country.

        :param language: Language code (default 'en')
        :param country: Country code (default 'US')
        """
        self.language = language.lower()
        self.country = country.upper()

    def _build_ceid(self) -> str:
        """
        Build the CEID parameter for the RSS feed URL based on language and country.

        :return: Formatted CEID string
        """
        return f'?ceid={self.country}:{self.language}&hl={self.language}&gl={self.country}'

    def _parse_sub_articles(self, html_content: str) -> List[Dict[str, str]]:
        """
        Parse sub-articles from the main and topic feeds using BeautifulSoup.

        :param html_content: HTML content of the summary
        :return: List of sub-articles with URL, title, and publisher
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            list_items = soup.find_all('li')
            sub_articles = []

            for li in list_items:
                try:
                    link = li.find('a', href=True)
                    publisher = li.find('font')
                    if link and publisher:
                        sub_articles.append({
                            "url": link['href'],
                            "title": link.get_text(strip=True),
                            "publisher": publisher.get_text(strip=True)
                        })
                except AttributeError:
                    continue  # Skip if expected tags are not found

            return sub_articles
        except Exception as e:
            print(f"Error parsing sub-articles: {e}")
            return []

    def _add_sub_articles(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Add sub-articles to each entry if a summary is present.

        :param entries: List of feed entries
        :return: Updated list of entries with sub_articles field
        """
        for entry in entries:
            summary = entry.get('summary', '')
            entry['sub_articles'] = self._parse_sub_articles(summary) if summary else None
        return entries

    def _fetch_with_scraping_bee(self, api_key: str, url: str) -> requests.Response:
        """
        Fetch content using ScrapingBee API.

        :param api_key: ScrapingBee API key
        :param url: URL to fetch
        :return: Response object
        :raises Exception: If the request fails
        """
        try:
            response = requests.get(
                "https://app.scrapingbee.com/api/v1/",
                params={
                    "api_key": api_key,
                    "url": url,
                    "render_js": "false"
                },
                timeout=10
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise Exception(f"ScrapingBee request failed: {e}") from e

    def _fetch_feed(self, feed_url: str, proxies: Optional[Dict[str, str]] = None,
                   scraping_bee_api_key: Optional[str] = None) -> feedparser.FeedParserDict:
        """
        Fetch and parse the RSS feed from Google News.

        :param feed_url: RSS feed URL
        :param proxies: Optional proxies dictionary
        :param scraping_bee_api_key: Optional ScrapingBee API key
        :return: Parsed feed
        :raises Exception: If feed is unsupported or cannot be fetched
        """
        if scraping_bee_api_key and proxies:
            raise ValueError("Cannot use both ScrapingBee and proxies simultaneously.")

        try:
            if scraping_bee_api_key:
                response = self._fetch_with_scraping_bee(api_key=scraping_bee_api_key, url=feed_url)
            else:
                response = requests.get(feed_url, proxies=proxies, timeout=10)
                response.raise_for_status()

            if "https://news.google.com/rss/unsupported" in response.url:
                raise Exception('This feed is not available.')

            parsed_feed = feedparser.parse(response.text)

            # Fallback if no entries found and not using proxies or ScrapingBee
            if not scraping_bee_api_key and not proxies and not parsed_feed.entries:
                parsed_feed = feedparser.parse(feed_url)

            return parsed_feed
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch feed: {e}") from e

    def _url_encode_query(self, query: str) -> str:
        """
        URL-encode the search query.

        :param query: Search query string
        :return: URL-encoded query
        """
        return urllib.parse.quote_plus(query)

    def _validate_and_format_date(self, date_str: str) -> str:
        """
        Validate and format the date string to 'YYYY-MM-DD'.

        :param date_str: Date string to validate
        :return: Formatted date string
        :raises ValueError: If the date cannot be parsed
        """
        parsed_date = parse_date(date_str)
        if not parsed_date:
            raise ValueError('Could not parse the provided date.')
        return parsed_date.strftime('%Y-%m-%d')

    def top_news(self, proxies: Optional[Dict[str, str]] = None,
                scraping_bee_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve top news articles from Google News.

        :param proxies: Optional proxies dictionary
        :param scraping_bee_api_key: Optional ScrapingBee API key
        :return: Dictionary containing feed and entries with sub-articles
        """
        feed_url = f"{self.BASE_RSS_URL}{self._build_ceid()}"
        parsed_feed = self._fetch_feed(feed_url, proxies, scraping_bee_api_key)
        parsed_feed.entries = self._add_sub_articles(parsed_feed.entries)
        return {key: parsed_feed[key] for key in ('feed', 'entries')}

    def topic_headlines(self, topic: str, proxies: Optional[Dict[str, str]] = None,
                       scraping_bee_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve headlines for a specific topic from Google News.

        :param topic: Topic name (e.g., 'WORLD', 'BUSINESS')
        :param proxies: Optional proxies dictionary
        :param scraping_bee_api_key: Optional ScrapingBee API key
        :return: Dictionary containing feed and entries with sub-articles
        :raises ValueError: If the topic is unsupported
        """
        standardized_topic = topic.upper()
        predefined_topics = [
            'WORLD', 'NATION', 'BUSINESS', 'TECHNOLOGY',
            'ENTERTAINMENT', 'SCIENCE', 'SPORTS', 'HEALTH'
        ]

        if standardized_topic in predefined_topics:
            feed_path = f"/headlines/section/topic/{standardized_topic}"
        else:
            feed_path = f"/topics/{topic}"

        feed_url = f"{self.BASE_RSS_URL}{feed_path}{self._build_ceid()}"
        parsed_feed = self._fetch_feed(feed_url, proxies, scraping_bee_api_key)
        parsed_feed.entries = self._add_sub_articles(parsed_feed.entries)

        if not parsed_feed.entries:
            raise ValueError('Unsupported topic or no articles found.')

        return {key: parsed_feed[key] for key in ('feed', 'entries')}

    def geo_headlines(self, geo: str, proxies: Optional[Dict[str, str]] = None,
                      scraping_bee_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve headlines for a specific geolocation from Google News.

        :param geo: Geolocation identifier (e.g., 'US')
        :param proxies: Optional proxies dictionary
        :param scraping_bee_api_key: Optional ScrapingBee API key
        :return: Dictionary containing feed and entries with sub-articles
        """
        feed_path = f"/headlines/section/geo/{geo}"
        feed_url = f"{self.BASE_RSS_URL}{feed_path}{self._build_ceid()}"
        parsed_feed = self._fetch_feed(feed_url, proxies, scraping_bee_api_key)
        parsed_feed.entries = self._add_sub_articles(parsed_feed.entries)
        return {key: parsed_feed[key] for key in ('feed', 'entries')}

    def search(self, query: str, helper: bool = True, when: Optional[str] = None,
               from_date: Optional[str] = None, to_date: Optional[str] = None,
               proxies: Optional[Dict[str, str]] = None,
               scraping_bee_api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for articles based on a query with optional date filters.

        :param query: Search query string
        :param helper: If True, URL-encodes the query
        :param when: Relative time filter (e.g., '2020-12-01')
        :param from_date: Start date filter (YYYY-MM-DD)
        :param to_date: End date filter (YYYY-MM-DD)
        :param proxies: Optional proxies dictionary
        :param scraping_bee_api_key: Optional ScrapingBee API key
        :return: Dictionary containing feed and entries with sub-articles
        """
        if when:
            query += f' when:{when}'
        else:
            if from_date:
                formatted_from = self._validate_and_format_date(from_date)
                query += f' after:{formatted_from}'
            if to_date:
                formatted_to = self._validate_and_format_date(to_date)
                query += f' before:{formatted_to}'

        if helper:
            query = self._url_encode_query(query)

        ceid = self._build_ceid().replace('?', '&')
        feed_url = f"{self.BASE_RSS_URL}/search?q={query}{ceid}"
        parsed_feed = self._fetch_feed(feed_url, proxies, scraping_bee_api_key)
        parsed_feed.entries = self._add_sub_articles(parsed_feed.entries)
        return {key: parsed_feed[key] for key in ('feed', 'entries')}


def main():
    """
    Example usage of the GoogleNews class.
    """
    gn = GoogleNews()

    try:
        # Fetch the first 5 top news articles
        top_news = gn.top_news()
        top_news = top_news['entries'][:3] if top_news else []
        print("Top News:")
        print(top_news)
        print('-' * 50)

        # # Fetch topic headlines
        # topic = 'WORLD'
        # topic_headlines = gn.topic_headlines(topic)
        # print(f"Topic Headlines ({topic}):")
        # print(topic_headlines)
        # print('-' * 50)

        # # Fetch geo headlines
        # geo = 'US'
        # geo_headlines = gn.geo_headlines(geo)
        # print(f"Geo Headlines ({geo}):")
        # print(geo_headlines)
        # print('-' * 50)

        # # Perform search without helper
        # search_query = 'Covid-19'
        # search_results = gn.search(search_query)
        # print(f"Search Results for '{search_query}':")
        # print(search_results)
        # print('-' * 50)

        # # Perform search with helper disabled
        # search_results_no_helper = gn.search(search_query, helper=False)
        # print(f"Search Results for '{search_query}' (No Helper):")
        # print(search_results_no_helper)
        # print('-' * 50)

        # # Perform search with 'when' filter
        # search_with_when = gn.search(search_query, when='2020-12-01')
        # print(f"Search Results for '{search_query}' with when='2020-12-01':")
        # print(search_with_when)
        # print('-' * 50)

        # # Perform search with 'from' and 'to' dates
        # search_with_dates = gn.search(
        #     search_query,
        #     from_date='2020-12-01',
        #     to_date='2020-12-02'
        # )
        # print(f"Search Results for '{search_query}' from '2020-12-01' to '2020-12-02':")
        # print(search_with_dates)
        # print('-' * 50)

        # # Perform search with dates and helper disabled
        # search_with_dates_no_helper = gn.search(
        #     search_query,
        #     from_date='2020-12-01',
        #     to_date='2020-12-02',
        #     helper=False
        # )
        # print(f"Search Results for '{search_query}' with dates and No Helper:")
        # print(search_with_dates_no_helper)
        # print('-' * 50)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == '__main__':
    main()
