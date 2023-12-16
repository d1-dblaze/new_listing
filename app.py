import os
import re
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()
channel_id = os.getenv('TELEGRAM_BOT_TOKEN')
bot_token = os.getenv('TELEGRAM_CHANNEL_ID')

#div = "css-1yxx6id"
#a = 'css-1w8j6ia'


class BinanceAnnouncementScraper:
    def __init__(self, url, database_path='announcements.db', telegram_bot_token=None, telegram_chat_id=None):
        self.url = url
        self.database_path = database_path
        self.driver = None
        self.conn = None
    
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

        if self.telegram_bot_token and self.telegram_chat_id:
            self.bot = Bot(token=self.telegram_bot_token)

    def send_telegram_message(self, message):
        try:
            if self.bot:
                self.bot.send_message(chat_id=self.telegram_chat_id, text=message)
        except TelegramError as e:
            print(f"Failed to send Telegram message: {e}")

           
    def create_announcements_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS binance_announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                link TEXT,
                headline TEXT,
                date TEXT,
                symbols TEXT
            )
        ''')
        self.conn.commit()

    def insert_announcement(self, link, headline, date, symbols):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO binance_announcements (link, headline, date, symbols)
            VALUES (?, ?, ?, ?)
        ''', (link, headline, date, symbols))
        self.conn.commit()

    def symbol_exists(self, symbol):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM binance_announcements WHERE symbols = ?', (symbol,))
        return cursor.fetchone() is not None


    def initialize_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        self.driver = webdriver.Chrome(options=options)
        
    def get_announcements(self):
        try:
            self.initialize_driver()
            self.driver.get(self.url)

            # Wait for the announcements to load (adjust the timeout as needed)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'css-1w8j6ia'))
            )

            # Scroll down to load more content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait for the additional content to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'css-1w8j6ia'))
            )

            # Get the updated page source after dynamic content has loaded
            page_source = self.driver.page_source

            soup = BeautifulSoup(page_source, 'html.parser')

            announcements = soup.find_all('a', class_='css-1w8j6ia')

            result = []
            #print(result)
            # Create or connect to the SQLite database
            self.conn = sqlite3.connect(self.database_path)

            # Create the announcements table if it doesn't exist
            self.create_announcements_table()
            
            for announcement in announcements:
                link = "https://www.binance.com" + announcement['href']
                headline = announcement.find('div', class_='css-1yxx6id').get_text(strip=True)
                date = announcement.find('h6', class_='css-eoufru').get_text(strip=True)
                
            # Check if the word 'list' is present in the headline
                if 'list' in headline.lower():
                    # Extract the word inside parentheses using regular expression
                    symbols_match = re.search(r'\(([^)]+)\)', headline)
                    symbols = symbols_match.group(1) if symbols_match else None

                    # Check if the symbol already exists in the database
                    if symbols and not self.symbol_exists(symbols):
                        print(symbols)
                        result.append({
                            'link': link,
                            'headline': headline,
                            'date': date,
                            'symbols': symbols
                        })

                        # Add the announcement to the database
                        self.insert_announcement(link, headline, date, symbols)

            return result

        finally:
            if self.driver:
                self.driver.quit()
            if self.conn:
                self.conn.close()

    def poll_announcements(self, interval=5):
        try:
            while True:
                announcements = self.get_announcements()
                if announcements:
                    print("Binance Announcements:")
                    for announcement in announcements:
                        print(f"Link: {announcement['link']}")
                        print(f"Headline: {announcement['headline']}")
                        print(f"Date: {announcement['date']}")
                        print(f"Symbols: {announcement['symbols']}")
                        print()
                        if self.telegram_bot_token and self.telegram_chat_id:
                            message = f"New Binance Listing:\n{announcement['headline']}\n{announcement['link']}"
                            self.send_telegram_message(message)
                else:
                    print("No new Binance listing.")

                time.sleep(interval)

        except KeyboardInterrupt:
            print("Polling stopped by the user.")
        finally:
            if self.driver:
                self.driver.quit()
            if self.conn:
                self.conn.close()
                                            
def main() :
    announcement_url = 'https://www.binance.com/en/support/announcement/new-cryptocurrency-listing?c=48&navId=48'
    binance_scraper = BinanceAnnouncementScraper(
        url=announcement_url,
        telegram_bot_token=bot_token,
        telegram_chat_id=channel_id)
    binance_scraper.poll_announcements()

        
if __name__ == "__main__":
    main()
