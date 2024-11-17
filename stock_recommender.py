import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from openai import OpenAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()
api_key = os.getenv("FINNHUB_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Set up OpenAI API client
client = OpenAI(api_key=openai_api_key)

# Cache file
CACHE_FILE = "news_cache.json"

# Initialize sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Function to fetch news data from API
def fetch_news_from_api(api_key, category="general"):
    url = f"https://finnhub.io/api/v1/news?category={category}&token={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return []

# Function to load cached data
def load_cached_data():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Cache file is corrupted. Starting fresh.")
            return []
    return []

# Function to save data to cache
def save_to_cache(data):
    with open(CACHE_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Function to get news data (with caching)
def get_news_data(api_key, category="general"):
    cached_data = load_cached_data()
    if cached_data:
        print("Loaded data from cache.")
        return cached_data
    print("Fetching data from API...")
    new_data = fetch_news_from_api(api_key, category)
    if new_data:
        save_to_cache(new_data)
    return new_data

# Function to perform sentiment analysis
def analyze_sentiment(text):
    sentiment = analyzer.polarity_scores(text)
    return sentiment['compound']

# Function to extract tickers
def extract_tickers(article):
    related_field = article.get("related", "")
    tickers = [ticker.strip() for ticker in related_field.split(",") if ticker.strip()]
    return tickers


class ModerationResult(BaseModel):
        tickers: list[str]

def openai_response(article):
    response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": """"Based on the following news article, identify relevant stock tickers that may benefit.
        List only the stock tickers, separated by commas.
                                        """
                                        },
        {"role": "user", "content": f"News articles: {json.dumps(article, indent=4)}."},
    ],
    response_format = ModerationResult,
    )
    decision = response.choices[0].message.parsed
    # print(decision)
    return decision

# Fallback function to use OpenAI for ticker extraction
def infer_tickers_from_openai(article):
    try:
        result = openai_response(article).tickers
        return result
    #     tickers = response.choices[0].text.strip().split(",")
    #     return [ticker.strip().upper() for ticker in tickers if ticker.strip()]
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return []

# Function to process and display news
def process_news(news_data):
    stock_sentiments = {}
    most_positive_news = None
    highest_sentiment_score = float("-inf")
    
    for article in news_data:
        title = article.get("headline", "No Title")
        summary = article.get("summary", "")
        content = f"{title} {summary}"
        source = article.get("source", "Unknown Source")
        url = article.get("url", "No URL")
        datetime_unix = article.get("datetime", 0)
        published_date = datetime.utcfromtimestamp(datetime_unix).strftime('%Y-%m-%d %H:%M:%S') if datetime_unix else "Unknown Date"

        # Perform sentiment analysis on title + summary
        sentiment_score = analyze_sentiment(content)

        # Update most positive news
        if sentiment_score > highest_sentiment_score:
            highest_sentiment_score = sentiment_score
            most_positive_news = article

        # Extract related tickers
        tickers = extract_tickers(article)
        for ticker in tickers:
            if ticker:
                if ticker not in stock_sentiments:
                    stock_sentiments[ticker] = []
                stock_sentiments[ticker].append(sentiment_score)

        print(f"Title: {title}")
        print(f"Source: {source}")
        print(f"Link: {url}")
        print(f"Published: {published_date}")
        print(f"Sentiment Score: {sentiment_score:.2f}")
        print("-" * 80)

    # Handle case where no tickers are found for the most positive news
    if most_positive_news and not extract_tickers(most_positive_news):
        print("\nNo tickers found for the most positive news. Using OpenAI to infer tickers...")
        inferred_tickers = infer_tickers_from_openai(most_positive_news)
        for ticker in inferred_tickers:
            if ticker not in stock_sentiments:
                stock_sentiments[ticker] = []
            stock_sentiments[ticker].append(highest_sentiment_score)

    return stock_sentiments

# Function to suggest top stocks based on sentiment
def suggest_top_stocks(stock_sentiments, top_n=5):
    avg_sentiments = {ticker: sum(scores) / len(scores) for ticker, scores in stock_sentiments.items()}
    sorted_stocks = sorted(avg_sentiments.items(), key=lambda x: x[1], reverse=True)
    print(f"\nTop {top_n} Stocks Based on Sentiment:")
    for ticker, sentiment in sorted_stocks[:top_n]:
        print(f"Stock: {ticker}, Average Sentiment: {sentiment:.2f}")

# Main execution
if __name__ == "__main__":
    if not api_key:
        print("API key is missing. Please set it in your .env file.")
    elif not openai_api_key:
        print("OpenAI API key is missing. Please set it in your .env file.")
    else:
        news_data = get_news_data(api_key)
        if news_data:
            stock_sentiments = process_news(news_data)
            suggest_top_stocks(stock_sentiments)
        else:
            print("No news articles fetched.")
