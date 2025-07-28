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
CHECK_INTERVAL = 20  # seconds
PINCODE = "400049"
TELEGRAM_FILE = 'telegram.json'

# === HARDCODED PRODUCTS ===
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

# === TELEGRAM CONFIG ===
def load_telegram_config():
    with open(TELEGRAM_FILE, 'r') as f:
        data = json.load(f)
        return data['token'], data['chat_id']

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[❌] Error sending Telegram message: {e}")

# === BROWSER SETUP ===
def setup_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    return webdriver.Chrome(options=options)

# === STOCK + PINCODE CHECK ===
def check_product(driver, product):
    name = product["name"]
    url = product["url"]
    print(f"🔍 Checking {name}...")

    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Check stock via button presence
        buy_btn = soup.find("button", string=lambda x: x and ("buy now" in x.lower() or "add to cart" in x.lower()))
        in_stock = bool(buy_btn)

        # Try entering pincode
        try:
            pincode_input = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Enter Pincode']"))
            )
            pincode_input.clear()
            pincode_input.send_keys(PINCODE)
            pincode_input.send_keys(Keys.RETURN)
            time.sleep(3)
        except Exception:
            print(f"[⚠️] Pincode input not found on {name}")
            return

        # Re-parse after pincode attempt
        updated_soup = BeautifulSoup(driver.page_source, "html.parser")
        deliverable = not updated_soup.find(string=lambda t: t and "not available for delivery" in t.lower())

        # Final logic
        if in_stock and deliverable:
            print(f"[🟢 In Stock and ✅ Deliverable] {name}")
            send_telegram_message(f"🟢 *{name}* is *IN STOCK* and *Deliverable to {PINCODE}*!\n[Buy Now]({url})")
        elif in_stock and not deliverable:
            print(f"[🟡 In Stock but ❌ Not Deliverable] {name}")
        else:
            print(f"[🔴 Out of Stock] {name}")

    except Exception as e:
        print(f"[❌] Error checking {name}: {e}")

# === MAIN LOOP ===
if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot Started...")
    browser = setup_browser()
    try:
        while True:
            for product in PRODUCTS:
                check_product(browser, product)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    finally:
        browser.quit()
