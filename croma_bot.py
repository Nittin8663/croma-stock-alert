import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'

# === Load Telegram config ===
with open(TELEGRAM_FILE, 'r') as f:
    tg_data = json.load(f)
    TELEGRAM_BOT_TOKEN = tg_data['token']
    TELEGRAM_CHAT_ID = tg_data['chat_id']

# === Telegram notify ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)

# === Load products ===
with open(PRODUCTS_FILE, 'r') as f:
    PRODUCTS = json.load(f)

# === Selenium Setup ===
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

# === Stock Check ===
def check_stock(product):
    driver.get(product['url'])
    time.sleep(3)  # Let page load

    variant_keywords = [kw.lower() for kw in product.get("variant_keywords", [])]
    matched_variant_found = False
    try:
        variant_blocks = driver.find_elements(By.CSS_SELECTOR, ".option-button, .btn")
        for block in variant_blocks:
            text = block.text.strip().lower()
            if all(kw in text for kw in variant_keywords):
                matched_variant_found = True
                if "unavailable" in text or "sold out" in text:
                    return f"[OUT OF STOCK] {product['name']}"
                elif "notify me" in text:
                    return f"[OUT OF STOCK] {product['name']}"
                else:
                    # Try clicking it to confirm it's selectable
                    try:
                        block.click()
                        time.sleep(1)
                    except Exception:
                        pass
                    return f"[IN STOCK ✅] {product['name']} - {product['url']}"
    except Exception as e:
        print("Error checking:", product['name'], e)

    if not matched_variant_found:
        return f"[VARIANT NOT FOUND] {product['name']}"
    return f"[OUT OF STOCK] {product['name']}"

# === Loop ===
sent_messages = set()
while True:
    for product in PRODUCTS:
        status = check_stock(product)
        print(status)
        if "[IN STOCK" in status and status not in sent_messages:
            send_telegram_message(status)
            sent_messages.add(status)
    time.sleep(CHECK_INTERVAL)
