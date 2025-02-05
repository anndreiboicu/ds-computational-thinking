import requests
import time
import pandas as pd
import sys
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Path to ChromeDriver
CHROMEDRIVER_PATH = "C:/Users/anboicu/OneDrive - ENDAVA/Desktop/chromedriver-win64/chromedriver-win64/chromedriver.exe"

# Function to scroll down the page and load content
def load_full_page(url, scroll_times=5, wait_time=2):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get(url)
        time.sleep(3)

        # Bypass cookie popup if it appears
        try:
            cookie_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="consent-page"]/div/div/div/form/div[2]/div[2]/button[2]'))
            )
            cookie_button.click()
        except:
            pass  # No cookie popup

        # Scroll down multiple times
        for _ in range(scroll_times):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(wait_time)

        page_source = driver.page_source
    finally:
        driver.quit()

    return page_source


# Function to scrape Yahoo Finance news for a single ticker
def scrape_for_single_ticker(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}/latest-news/"
    print(f"Scraping news for ticker: {ticker}")
    
    try:
        page_source = load_full_page(url)
        soup = BeautifulSoup(page_source, "html.parser")
        articles_data = extract_articles(soup)

        if articles_data:
            save_to_csv(articles_data, filename="news_articles_by_ticker.csv")
            print(f"Successfully scraped news for {ticker}.")
        else:
            print(f"No news found for {ticker}.")

    except Exception as e:
        print(f"Error scraping {ticker}: {e}")


# Function to scrape general market news from Yahoo Finance
def scrape_general_news():
    url = "https://finance.yahoo.com/topic/latest-news"
    print("Scraping general market news...")

    try:
        page_source = load_full_page(url)
        soup = BeautifulSoup(page_source, "html.parser")
        articles_data = extract_articles(soup)

        if articles_data:
            save_to_csv(articles_data, filename="news_articles.csv")
            print("Successfully scraped general market news.")
        else:
            print("No general news found.")

    except Exception as e:
        print(f"Error scraping general news: {e}")


# Function to extract articles from page source
def extract_articles(soup):
    articles_data = []

    articles = soup.find_all("div", class_="content yf-82qtw3")
    for article in articles:
        try:
            title_tag = article.find("h3", class_="clamp yf-82qtw3")
            title = title_tag.text.strip() if title_tag else "N/A"

            link_tag = article.find("a", class_="subtle-link fin-size-small titles noUnderline yf-1xqzjha")
            link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else "N/A"

            desc_tag = article.find("p", class_="clamp yf-82qtw3")
            description = desc_tag.text.strip() if desc_tag else "N/A"

            unwanted_phrase = "Most Read from Bloomberg"
            if unwanted_phrase in description:
                description = description.split(unwanted_phrase)[0].strip()

            unwanted_start = "(Bloomberg) -- "
            if unwanted_start in description:
                description = description.replace(unwanted_start, "").strip()

            reuters_string = "(Reuters) -"
            if reuters_string in description:
                description = description.replace(reuters_string, "").strip()

            source_info = article.find("div", class_="publishing yf-1weyqlp")
            source, published_date = "N/A", "N/A"
            if source_info:
                source_text = source_info.text.strip().split("•")
                if len(source_text) > 0:
                    source = source_text[0].strip()
                if len(source_text) > 1:
                    published_date = source_text[1].strip()

            tickers_div = article.find_all("div", class_="name yf-1m808gl")
            tickers = ", ".join([ticker.find("span", class_="symbol yf-1m808gl").text.strip() for ticker in tickers_div]) if tickers_div else "N/A"


            articles_data.append([title, description, source, published_date, tickers, link])

        except Exception as e:
            print(f"Error extracting article: {e}")

    return articles_data


# Function to remove duplicates and save to CSV
def save_to_csv(data, filename):
    df = pd.DataFrame(data, columns=["Title", "Short Description", "Source", "Published Date", "Affected Tickers", "Link"])
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"Data saved to {filename}")


# Define a main function that can be called from another script
def main():
    print("Fetching general market news data...")
    scrape_general_news()
    print("News data successfully fetched and saved as 'news_articles.csv'.")

# Check if this script is being run directly
if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
        scrape_for_single_ticker(ticker)
    else:
        main()  # Run the general news scraper when executed without arguments
