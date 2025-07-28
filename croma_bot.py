import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIG ===
PINCODE = "400049"
CHECK_INTERVAL = 30  # seconds
TELEGRAM_FILE = 'telegram.json'

# Hardcoded product list
PRODUCTS = [
    {
        "name": "Y300-Silver",
        "url": "https://www.croma.com/vivo-y300-5g-8gb-ram-128gb-rom-titanium-silver-/p/311900"
    },
    {
        "name": "Y400",
        "url": "https://www.croma.com/vivo-x200-fe-5g-12gb-ram-256gb-frost-blue-/p/316890"
    }
]

# Load Telegram config
def load_telegram_config():
    with open(TELEGRAM_FILE, 'r') as f:
        data = json.load(f)
        return data['token'], data['chat_id']

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

# Send Telegram alert
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[❌] Error sending message: {e}")

# Setup headless browser
def setup_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    return webdriver.Chrome(options=options)

# Main checker
def check_stock(driver):
    for product in PRODUCTS:
        name = product['name']
        url = product['url']
        print(f"🔍 Checking {name}...")

        try:
            driver.get(url)
            time.sleep(3)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Check if "Buy Now" or similar button exists
            in_stock = "Buy Now" in page_source or "Add to Cart" in page_source

            # Attempt pincode check
            delivery_status = "⚠️ Pincode input not found"
            try:
                # Step 1: Click "Change" or "Deliver to"
                try:
                    change_btn = WebDriverWait(driver, 3).until(EC.element_to_be_clickable(
                        (By.XPATH, '//span[contains(text(), "Change") or contains(text(), "Deliver to")]')
                    ))
                    change_btn.click()
                    time.sleep(1.5)
                except:
                    pass

                # Step 2: Enter pincode
                input_field = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                    (By.XPATH, '//input[contains(@placeholder, "Enter Pincode")]')
                ))
                input_field.clear()
                input_field.send_keys(PINCODE)
                input_field.send_keys(Keys.ENTER)
                time.sleep(3)

                # Step 3: Check deliverability
                updated_page = BeautifulSoup(driver.page_source, 'html.parser')
                if updated_page.find(string=lambda t: "not deliverable" in t.lower() or "unavailable" in t.lower()):
                    delivery_status = "❌ Not Deliverable"
                else:
                    delivery_status = "✅ Deliverable"
            except Exception as e:
                print(f"[⚠️] Pincode input not found on {name}")

            # Final decision & alert
            if in_stock and delivery_status == "✅ Deliverable":
                print(f"[🟢 IN STOCK & DELIVERABLE] {name}")
                send_telegram_message(f"🟢 *{name}* is *IN STOCK & DELIVERABLE*! \n[Buy Now]({url})")
            elif in_stock:
                print(f"[🟡 In Stock but ❌ Not Deliverable] {name}")
            else:
                print(f"[🔴 Out of Stock] {name}")

        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# Runner
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
