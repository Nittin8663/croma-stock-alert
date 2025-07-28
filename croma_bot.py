import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'
PINCODE = "400049"

# Load Telegram config
def load_telegram_config():
    with open(TELEGRAM_FILE, 'r') as f:
        data = json.load(f)
        return data['token'], data['chat_id']

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

# Load product list
def load_products():
    with open(PRODUCTS_FILE, 'r') as f:
        return json.load(f)

# Send Telegram alert
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[❌] Error sending message: {e}")

# Setup headless Chrome browser
def setup_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    driver = webdriver.Chrome(options=options)
    return driver

# Check stock from HTML
def is_in_stock(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    out_of_stock_tag = soup.find("div", class_="out-of-stock-msg")
    return out_of_stock_tag is None

# Check deliverability to the given pincode
def is_deliverable(driver):
    try:
        # Try multiple possible selectors
        input_found = False
        possible_selectors = [
            '[id="pincode-check"]',
            'input[placeholder*="Enter Pincode"]',
            'input[class*="pincode"]',
            'input[type="tel"]',
        ]
        for selector in possible_selectors:
            try:
                input_element = driver.find_element(By.CSS_SELECTOR, selector)
                input_found = True
                break
            except:
                continue

        if not input_found:
            print("[⚠️] Pincode input not found.")
            return False

        input_element.clear()
        input_element.send_keys(PINCODE)
        input_element.send_keys(Keys.RETURN)
        time.sleep(3)

        # Check delivery status text
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        delivery_texts = soup.find_all(string=True)
        for text in delivery_texts:
            if "not deliverable" in text.lower():
                return False
            if "deliverable" in text.lower():
                return True

        return False  # Default fallback

    except Exception as e:
        print(f"[⚠️] Pincode check failed: {e}")
        return False

# Main checking loop
def check_stock(driver):
    products = load_products()
    for product in products:
        name = product['name']
        url = product['url']
        try:
            driver.get(url)
            time.sleep(3)
            page_source = driver.page_source

            in_stock = is_in_stock(page_source)
            deliverable = is_deliverable(driver)

            if in_stock and deliverable:
                print(f"[🟢 In Stock & Deliverable] {name}")
                send_telegram_message(f"🟢 *{name}* is *IN STOCK* and *DELIVERABLE* to {PINCODE}! \n[Buy Now]({url})")
            elif in_stock and not deliverable:
                print(f"[🟡 In Stock but ❌ Not Deliverable] {name}")
            else:
                print(f"[🔴 Out of Stock] {name}")

        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# Runner
if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot (Selenium) Started...")
    browser = setup_browser()
    try:
        while True:
            check_stock(browser)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    finally:
        browser.quit()
