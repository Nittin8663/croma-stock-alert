import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Load product URLs
with open('products.json', 'r') as f:
    products = json.load(f)

# Load Telegram config from root directory
with open('telegram.json', 'r') as f:
    telegram_config = json.load(f)

TELEGRAM_TOKEN = telegram_config['token']
CHAT_ID = telegram_config['chat_id']

CHECK_INTERVAL = 20  # seconds

headers_list = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    },
    {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    },
]

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

def is_in_stock(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    buy_button = soup.find(string="Buy Now") or soup.select_one('button.add-to-cart')
    return buy_button is not None

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"[❌] Telegram Error: {e}")

print("🚀 Croma Stock Alert Bot Started...")

while True:
    for product in products:
        url = product['url']
        name = product['name']
        success = False

        for headers in headers_list:
            try:
                driver.get(url)
                time.sleep(3)
                if is_in_stock(driver.page_source):
                    message = f"[🟢 In Stock] *{name}*\n[Buy Now]({url})"
                    send_telegram_message(message)
                    print(message)
                else:
                    print(f"[🔴 Out of Stock] {name}")
                success = True
                break
            except Exception as e:
                print(f"[Retry] Error for {name}, retrying with different headers...\n{e}")

        if not success:
            print(f"[⚠️] Failed to fetch {name}")

    time.sleep(CHECK_INTERVAL)
