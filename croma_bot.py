import json
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import tempfile

# Load Telegram credentials
with open('telegram.json', 'r') as f:
    telegram_config = json.load(f)
    TELEGRAM_BOT_TOKEN = telegram_config['bot_token']
    TELEGRAM_CHAT_ID = telegram_config['chat_id']

# Load product list
with open('products.json', 'r') as f:
    products = json.load(f)

# Setup headless Chrome options
options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
user_data_dir = tempfile.mkdtemp()
options.add_argument(f"--user-data-dir={user_data_dir}")

print("\n🚀 Croma Stock Alert Bot Started...")

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print("[Telegram Error]", e)

# Track previously sent alerts to avoid duplicates
sent_alerts = set()

while True:
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    for product in products:
        name = product['name']
        url = product['url']
        try:
            driver.get(url)
            time.sleep(2)  # wait for page to load
            buy_button = driver.find_elements(By.XPATH, "//button[contains(., 'Add to Cart')]" )

            if buy_button:
                if url not in sent_alerts:
                    message = f"[🟢 In Stock] {name}\n{url}"
                    print(message)
                    send_telegram_alert(message)
                    sent_alerts.add(url)
            else:
                print(f"[🔴 Out of Stock] {name}")
                if url in sent_alerts:
                    sent_alerts.remove(url)
        except Exception as e:
            print(f"[⚠️] Failed to fetch {name} - {str(e)}")

    driver.quit()
    time.sleep(20)
