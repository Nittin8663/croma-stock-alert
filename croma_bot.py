import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# === CONFIG ===
CHECK_INTERVAL = 30  # seconds
PINCODE = "400049"
TELEGRAM_FILE = "telegram.json"

# === HARDCODED PRODUCT LIST ===
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

# === LOAD TELEGRAM CONFIG ===
def load_telegram_config():
    with open(TELEGRAM_FILE, 'r') as f:
        data = json.load(f)
        return data['token'], data['chat_id']

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[❌] Error sending message: {e}")

def setup_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    return webdriver.Chrome(options=options)

def is_in_stock(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    out_of_stock_div = soup.find("div", class_="out-of-stock-msg")
    return out_of_stock_div is None

def check_product(driver, product):
    name = product['name']
    url = product['url']
    print(f"🔍 Checking {name}...")

    try:
        driver.get(url)
        time.sleep(3)

        in_stock = is_in_stock(driver.page_source)
        if not in_stock:
            print(f"[🔴 Out of Stock] {name}")
            return

        # --- Try to detect pincode input by brute force ---
        pincode_input = None
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        for inp in all_inputs:
            attrs = [
                (inp.get_attribute("placeholder") or "").lower(),
                (inp.get_attribute("aria-label") or "").lower(),
                (inp.get_attribute("name") or "").lower(),
                (inp.get_attribute("id") or "").lower(),
            ]
            if any("pincode" in attr for attr in attrs):
                pincode_input = inp
                break

        if not pincode_input:
            print(f"[⚠️] Pincode input not found on {name}")
            return

        pincode_input.clear()
        pincode_input.send_keys(PINCODE)
        pincode_input.send_keys(Keys.RETURN)
        time.sleep(3)

        # Check if deliverable
        page = driver.page_source
        deliverable = "Not deliverable" not in page and "Enter pincode" not in page
        if deliverable:
            print(f"[✅ In Stock & Deliverable] {name}")
            send_telegram_message(f"✅ *{name}* is *In Stock & Deliverable*! \n[Buy Now]({url})")
        else:
            print(f"[🟡 In Stock but ❌ Not Deliverable] {name}")
            send_telegram_message(f"🟡 *{name}* is *In Stock* but *Not Deliverable* to {PINCODE}. \n[Check Now]({url})")

    except Exception as e:
        print(f"[❌] Error checking {name}: {e}")

# === MAIN LOOP ===
if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot Started...")
    driver = setup_browser()
    try:
        while True:
            for product in PRODUCTS:
                check_product(driver, product)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    finally:
        driver.quit()
