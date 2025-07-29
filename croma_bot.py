import time
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# === Load Telegram Config ===
with open('telegram.json') as f:
    telegram = json.load(f)

BOT_TOKEN = telegram['token']
CHAT_ID = telegram['chat_id']
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# === Load Product List ===
with open('products.json') as f:
    PRODUCTS = json.load(f)

CHECK_INTERVAL = 20  # seconds

# === Setup Headless Chrome ===
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=chrome_options)

# === Telegram Notification ===
def send_telegram(message):
    try:
        payload = {'chat_id': CHAT_ID, 'text': message}
        requests.post(TELEGRAM_API, data=payload)
    except Exception as e:
        print("Telegram send error:", e)

# === Check Stock Function ===
def check_stock(product):
    try:
        driver.get(product['url'])
        time.sleep(3)  # allow page to load

        # Find Add to Cart button by class
        add_to_cart = driver.find_element(By.CSS_SELECTOR, "button.pdp-add-to-cart")

        if add_to_cart.is_enabled() and add_to_cart.is_displayed():
            print(f"[AVAILABLE] {product['name']}")
            send_telegram(f"🟢 IN STOCK: {product['name']}\n{product['url']}")
        else:
            print(f"[OUT OF STOCK] {product['name']} (Button disabled)")
    except Exception:
        print(f"[OUT OF STOCK] {product['name']} (Button not found)")

# === Main Loop ===
print("🔄 Bot started. Checking every", CHECK_INTERVAL, "seconds.")
try:
    while True:
        for product in PRODUCTS:
            check_stock(product)
        time.sleep(CHECK_INTERVAL)
except KeyboardInterrupt:
    print("⛔ Bot stopped by user.")
finally:
    driver.quit()
