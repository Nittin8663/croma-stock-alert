import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

# === CONFIG ===
PINCODE = "400049"
CHECK_INTERVAL = 30  # seconds
TELEGRAM_FILE = 'telegram.json'

# Direct product list
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

# === SETUP BROWSER ===
def setup_browser():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

# === CHECK STOCK LOGIC ===
def check_stock(driver):
    for product in PRODUCTS:
        name = product["name"]
        url = product["url"]
        print(f"🔍 Checking {name}...")

        try:
            driver.get(url)
            time.sleep(4)

            # STEP 1: Check if "Buy Now" or "Add to Cart" button exists
            try:
                buy_button = driver.find_element(By.XPATH, '//button[contains(text(), "Buy Now") or contains(text(), "Add to Cart")]')
                in_stock = buy_button.is_enabled()
            except NoSuchElementException:
                in_stock = False

            # STEP 2: Check deliverability to pincode
            try:
                # Try to find and fill the pincode field
                pincode_input = driver.find_element(By.CSS_SELECTOR, 'input[type="tel"], input[id*="pincode"]')
                pincode_input.clear()
                pincode_input.send_keys(PINCODE)
                time.sleep(1)

                # Click check button
                check_buttons = driver.find_elements(By.XPATH, '//button[contains(text(), "Check")]')
                for btn in check_buttons:
                    if btn.is_enabled():
                        btn.click()
                        time.sleep(2)
                        break

                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                not_serviceable = soup.find(text=lambda t: t and ("not serviceable" in t.lower() or "not deliverable" in t.lower()))
                deliverable = not_serviceable is None
            except Exception:
                print(f"[⚠️] Pincode input not found on {name}")
                deliverable = False

            # STEP 3: Evaluate and report
            if in_stock and deliverable:
                print(f"[🟢 In Stock and ✅ Deliverable] {name}")
                send_telegram_message(f"🟢 *{name}* is *IN STOCK* and *DELIVERABLE*! \n[Buy Now]({url})")
            elif in_stock and not deliverable:
                print(f"[🟡 In Stock but ❌ Not Deliverable] {name}")
            else:
                print(f"[🔴 Out of Stock] {name}")

        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# === MAIN RUNNER ===
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
