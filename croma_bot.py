import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCTS_FILE = "products.json"
TELEGRAM_FILE = "telegram.json"

# === LOAD TELEGRAM CONFIG ===
with open(TELEGRAM_FILE, "r") as f:
    config = json.load(f)
    TELEGRAM_BOT_TOKEN = config["token"]
    TELEGRAM_CHAT_ID = config["chat_id"]

# === LOAD PRODUCTS ===
with open(PRODUCTS_FILE, "r") as f:
    products = json.load(f)

# === SEND TELEGRAM MESSAGE ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("Telegram API error:", response.text)
    except Exception as e:
        print("Telegram error:", e)

# === CHECK STOCK FUNCTION ===
def is_product_available(driver, url):
    driver.get(url)
    time.sleep(5)
    try:
        add_to_cart = driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]")
        return add_to_cart.is_enabled()
    except:
        return False

# === MAIN LOOP ===
def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    notified_flags = {product["url"]: False for product in products}

    while True:
        for product in products:
            name = product["name"]
            url = product["url"]
            try:
                if is_product_available(driver, url):
                    if not notified_flags[url]:
                        print(f"[IN STOCK] {name}")
                        send_telegram_message(f"✅ <b>{name}</b> is <b>IN STOCK</b>\n{url}")
                        notified_flags[url] = True
                    else:
                        print(f"[IN STOCK] {name} (Already notified)")
                else:
                    print(f"[OUT OF STOCK] {name}")
                    notified_flags[url] = False
            except Exception as e:
                print(f"[ERROR] {name}: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
