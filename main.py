import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import yfinance as yf
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

def fetch_company_news(ticker, start_date):
    """
    Fetches recent news for a specific company (ticker) from yfinance.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., "AAPL").
        start_date (str): Date from which to fetch news (format: "YYYY-MM-DD").
        
    Returns:
        list: A list of dictionaries containing news headlines and metadata.
    """
    stock = yf.Ticker(ticker)
    
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid start_date format. Use 'YYYY-MM-DD'.")
    
    news = stock.news
    if not news:
        return []
    
    # Filter news by date
    filtered_news = [
        {
            "title": item['title'],
            "link": item['link'],
            "provider": item.get('publisher', 'Unknown'),
            "published_date": datetime.utcfromtimestamp(item['providerPublishTime']).strftime('%Y-%m-%d %H:%M:%S')
        }
        for item in news
        if datetime.utcfromtimestamp(item['providerPublishTime']) >= datetime.strptime(start_date, "%Y-%m-%d")
    ]
    
    return filtered_news

# def scrape_first_paragraph(url):
#     """
#     Scrapes the first paragraph from a news article.
    
#     Args:
#         url (str): The URL of the news article.
        
#     Returns:
#         str: The first paragraph of the article or an error message if unable to fetch.
#     """
#     try:
#         response = requests.get(url, timeout=10)
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Extract the first paragraph
#         paragraph = soup.find('p')
#         if paragraph:
#             return paragraph.get_text(strip=True)
#         else:
#             return "No paragraph found."
#     except Exception as e:
#         return f"Error fetching content: {e}"


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
# Add any additional options here if needed

service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)
import time

def scrape_first_paragraph_selenium(url):
    """
    Scrapes the first paragraph from a news article using Selenium.
    
    Args:
        url (str): The URL of the news article.
        
    Returns:
        str: The first paragraph of the article or an error message.
    """
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    
    try:
        driver.get(url)
        time.sleep(5)  # Wait for the page to load
        
        # Find the first paragraph
        paragraph = driver.find_element(By.TAG_NAME, "p").text
        return paragraph if paragraph else "No paragraph found."
    except Exception as e:
        return f"Error fetching content: {e}"
    finally:
        driver.quit()


def save_news_to_json(news_items, file_name):
    """
    Saves news items to a JSON file.
    
    Args:
        news_items (list): List of news item dictionaries.
        file_name (str): File name for the JSON file.
    """
    with open(file_name, 'w') as json_file:
        json.dump(news_items, json_file, indent=4)
    print(f"News data saved to {file_name}")

def prepare_data_for_rag(news_items):
    """
    Prepares data in a format suitable for RAG by adding first paragraphs.
    
    Args:
        news_items (list): List of news item dictionaries.
        
    Returns:
        list: List of dictionaries with added 'content' field.
    """
    for news in news_items:
        news['content'] = scrape_first_paragraph_selenium(news['link'])
    return news_items


# Example Usage
ticker = "AAPL"
start_date = "2024-01-01"
file_name = "filtered_news.json"

# Fetch and save news
news_items = fetch_company_news(ticker, start_date)
save_news_to_json(news_items, file_name)

# Prepare for RAG
rag_ready_data = prepare_data_for_rag(news_items)

# Save the RAG data
rag_file_name = "rag_data.json"
save_news_to_json(rag_ready_data, rag_file_name)

print("Data prepared for RAG and saved.")
