import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCT_URL = "https://www.samsung.com/in/smartphones/galaxy-s24-ultra/buy/"  # Replace with your product URL
TELEGRAM_FILE = "telegram.json"

# === LOAD TELEGRAM CONFIG ===
with open(TELEGRAM_FILE, "r") as f:
    data = json.load(f)
    TELEGRAM_BOT_TOKEN = data["bot_token"]
    TELEGRAM_CHAT_ID = data["chat_id"]

# === TELEGRAM NOTIFY ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram error:", e)

# === CHECK STOCK FUNCTION ===
def is_product_available(driver):
    driver.get(PRODUCT_URL)
    time.sleep(5)
    try:
        add_to_cart = driver.find_element(By.XPATH, "//button[contains(text(), 'Add to Cart')]")
        if add_to_cart.is_enabled():
            return True
    except:
        pass
    return False

# === MAIN ===
def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)

    notified = False

    while True:
        try:
            if is_product_available(driver):
                if not notified:
                    print("[IN STOCK] Sending Telegram alert...")
                    send_telegram_message(f"[IN STOCK] {PRODUCT_URL}")
                    notified = True
                else:
                    print("[IN STOCK] Already notified.")
            else:
                print("[OUT OF STOCK]")
                notified = False
        except Exception as e:
            print("Error:", e)
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
