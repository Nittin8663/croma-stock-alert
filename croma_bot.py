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

# Check if product is deliverable to the specified pincode
def is_deliverable(driver):
    try:
        time.sleep(1)

        inputs = driver.find_elements(By.TAG_NAME, "input")
        target_input = None

        for input_tag in inputs:
            placeholder = input_tag.get_attribute("placeholder")
            aria_label = input_tag.get_attribute("aria-label")
            name = input_tag.get_attribute("name")
            class_name = input_tag.get_attribute("class")

            if (placeholder and "pincode" in placeholder.lower()) or \
               (aria_label and "pincode" in aria_label.lower()) or \
               (name and "pincode" in name.lower()) or \
               (class_name and "pincode" in class_name.lower()):
                target_input = input_tag
                break

        if not target_input:
            print("[⚠️] Pincode input not found.")
            return False

        driver.execute_script("arguments[0].scrollIntoView(true);", target_input)
        target_input.clear()
        target_input.send_keys(PINCODE)
        target_input.send_keys(Keys.ENTER)
        time.sleep(3)

        page = driver.page_source
        soup = BeautifulSoup(page, 'html.parser')
        for text in soup.stripped_strings:
            txt = text.lower()
            if "not deliverable" in txt or "out of delivery" in txt:
                return False
            if "deliverable" in txt or "delivery available" in txt:
                return True

        return False

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
            time.sleep(4)
            page_source = driver.page_source

            if is_in_stock(page_source):
                if is_deliverable(driver):
                    print(f"[✅ In Stock & Deliverable] {name}")
                    send_telegram_message(f"✅ *{name}* is *IN STOCK* and *DELIVERABLE* to {PINCODE}\n[Buy Now]({url})")
                else:
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
