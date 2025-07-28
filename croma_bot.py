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
PINCODE = "400049"  # Update pincode if needed

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
    return webdriver.Chrome(options=options)

# Check if "Buy Now" button is present
def is_buy_now_available(driver):
    try:
        buy_btn = driver.find_element(By.XPATH, "//button[contains(., 'Buy Now')]")
        return buy_btn.is_enabled()
    except:
        return False

# Check if deliverable to specific pincode
def check_pincode_deliverable(driver, pincode):
    try:
        # Click on pincode change input if visible
        delivery_btn = driver.find_element(By.CLASS_NAME, "delivery-check-pincode")
        delivery_btn.click()
        time.sleep(1)

        # Enter pincode and submit
        pincode_input = driver.find_element(By.ID, "pincode-check")
        pincode_input.clear()
        pincode_input.send_keys(pincode)
        pincode_input.send_keys(Keys.RETURN)
        time.sleep(2)

        # Check result
        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        not_deliverable = soup.find(string=lambda t: "Not Available for your pincode" in t)
        return not bool(not_deliverable)
    except Exception as e:
        print(f"[⚠️] Pincode check failed: {e}")
        return False

# Main checker
def check_stock(driver):
    products = load_products()
    for product in products:
        name = product['name']
        url = product['url']
        try:
            driver.get(url)
            time.sleep(3)

            in_stock = is_buy_now_available(driver)
            deliverable = check_pincode_deliverable(driver, PINCODE)

            if in_stock and deliverable:
                print(f"[✅ In Stock & Deliverable] {name}")
                send_telegram_message(f"✅ *{name}* is *IN STOCK* and *DELIVERABLE* to `{PINCODE}`.\n[Buy Now]({url})")
            elif in_stock and not deliverable:
                print(f"[⚠️ In Stock, ❌ Not Deliverable] {name}")
                send_telegram_message(f"⚠️ *{name}* is *IN STOCK* but *NOT Deliverable* to `{PINCODE}`.\n[View Product]({url})")
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
