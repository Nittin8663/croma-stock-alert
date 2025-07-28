import requests
import time
import json
from bs4 import BeautifulSoup

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Load telegram config
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

# Check stock from HTML
def is_in_stock(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    out_of_stock_tag = soup.find("div", class_="out-of-stock-msg")
    return out_of_stock_tag is None

# Main checking loop
def check_stock():
    products = load_products()
    for product in products:
        name = product['name']
        url = product['url']
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                in_stock = is_in_stock(response.text)
                if in_stock:
                    print(f"[🟢 In Stock] {name}")
                    send_telegram_message(f"🟢 *{name}* is *IN STOCK*! \n[Buy Now]({url})")
                else:
                    print(f"[🔴 Out of Stock] {name}")
            else:
                print(f"[⚠️] Failed to fetch {name} - Status: {response.status_code}")
        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# Runner
if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot Started...")
    while True:
        check_stock()
        time.sleep(CHECK_INTERVAL)
