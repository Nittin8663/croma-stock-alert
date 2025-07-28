import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PINCODE = "400049"
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'

# === Load config ===
def load_telegram_config():
    with open(TELEGRAM_FILE, 'r') as f:
        data = json.load(f)
        return data['token'], data['chat_id']

def load_products():
    with open(PRODUCTS_FILE, 'r') as f:
        return json.load(f)

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

# === Telegram Notify ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[❌] Error sending message: {e}")

# === Headless Chrome Setup ===
def setup_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    return webdriver.Chrome(options=options)

# === Stock Check ===
def is_in_stock(soup):
    return soup.find("div", class_="out-of-stock-msg") is None

# === Pincode Check ===
def is_deliverable(driver):
    try:
        # Wait for pincode input using any known ID or fallback
        pin_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((
                By.CSS_SELECTOR, 'input[id*="pincode"], input[class*="pincode"]'
            ))
        )
        pin_input.clear()
        pin_input.send_keys(PINCODE)
        pin_input.send_keys(Keys.RETURN)
        
        # Wait for result (e.g. "Available at", "Not deliverable", etc.)
        WebDriverWait(driver, 6).until(
            EC.presence_of_element_located((By.CLASS_NAME, "delivery-message"))
        )
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        msg = soup.find("div", class_="delivery-message")
        if msg and "not available" in msg.text.lower():
            return False
        return True
    except Exception as e:
        print(f"[⚠️] Pincode check failed: {e}")
        return False

# === Main Checker ===
def check_stock(driver):
    products = load_products()
    for product in products:
        name = product['name']
        url = product['url']
        try:
            driver.get(url)
            time.sleep(3)  # Allow JS content to load
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            stock = is_in_stock(soup)
            deliverable = is_deliverable(driver)

            if stock and deliverable:
                status = f"[🟢 In Stock & ✅ Deliverable] {name}"
                msg = f"🟢 *{name}* is *IN STOCK* and *Deliverable to {PINCODE}*!\n[Buy Now]({url})"
            elif stock and not deliverable:
                status = f"[🟡 In Stock but ❌ Not Deliverable] {name}"
                msg = f"🟡 *{name}* is *IN STOCK* but *NOT Deliverable to {PINCODE}*.\n[Buy Now]({url})"
            else:
                status = f"[🔴 Out of Stock] {name}"
                msg = None

            print(status)
            if msg:
                send_telegram_message(msg)

        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# === Runner ===
if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot Started...")
    browser = setup_browser()
    try:
        while True:
            check_stock(browser)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    finally:
        browser.quit()
