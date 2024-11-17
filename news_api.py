import os
import finnhub
import requests
from dotenv import load_dotenv

load_dotenv()
# API key from Finnhub (sign up for free key)
api_key = os.getenv("FINNHUB_API_KEY")

# Request to get news for a specific stock (e.g., Apple)
url = f'https://finnhub.io/api/v1/news?category=general&token={api_key}'

response = requests.get(url)
news_data = response.json()

# Print the news articles
for article in news_data:
    print(article)
    # print(f"Title: {article['headline']}")
    # print(f"Source: {article['source']}")
    # print(f"Link: {article['url']}")
    # print(f"Published: {article['datetime']}")
    print("-" * 80)

# finnhub_client = finnhub.Client(api_key=api_key)

# print(finnhub_client.general_news('general', min_id=0))
