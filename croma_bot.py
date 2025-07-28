import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'

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

# Check stock from Buy Now button color
def is_in_stock(driver):
    try:
        # Look for the Buy Now button
        buy_button = driver.find_element("xpath", "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buy now')]")
        button_color = buy_button.value_of_css_property("background-color")

        # List of green shades used on Croma (add more if needed)
        green_colors = ["rgb(0, 128, 0)", "rgb(4, 170, 109)", "rgba(4, 170, 109, 1)", "#04aa6d"]

        # Normalize color
        color = button_color.strip().lower()

        return any(green in color for green in green_colors)
    except Exception as e:
        print(f"[⚠️] Buy Now check failed: {e}")
        return False

# Main checking loop
def check_stock(driver):
    products = load_products()
    for product in products:
        name = product['name']
        url = product['url']
        try:
            driver.get(url)
            time.sleep(3)  # Wait for JS to load fully
            if is_in_stock(driver):
                print(f"[🟢 In Stock] {name}")
                send_telegram_message(f"🟢 *{name}* is *IN STOCK*! \n[Buy Now]({url})")
            else:
                print(f"[🔴 Out of Stock] {name}")
        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# Runner
if __name__ == "
