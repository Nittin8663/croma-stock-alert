import requests
from bs4 import BeautifulSoup
import time

# ✅ These should already be available in your environment or another file
# Make sure to define them before running this script
# Example:
# TELEGRAM_BOT_TOKEN = ...
# TELEGRAM_CHAT_ID = ...

PRODUCTS = {
    "Y300-Emerald": "https://www.croma.com/vivo-y300-5g-8gb-ram-128gb-rom-emerald-green-/p/311901",
    "X200-Frost": "https://www.croma.com/vivo-x200-fe-5g-12gb-ram-256gb-frost-blue-/p/316890"
}

PINCODE = "400049"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"[Telegram Error] {e}")

def check_stock(url, name):
    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # Check for Buy Now
        buy_button = soup.select_one('button[data-testid="buy-button"]')
        in_stock = bool(buy_button and "Buy Now" in buy_button.text)

        # Pincode delivery check
        product_id = url.split("/p/")[-1]
        api_url = "https://www.croma.com/ccstoreui/v1/pickupStore/getProductAvailabilityByPincode"
        payload = {"pincode": PINCODE, "productId": product_id}
        pin_response = session.post(api_url, json=payload, headers=HEADERS, timeout=10)
        deliverable = pin_response.json().get("pincodeAvailable", False)

        # Decision logic
        if in_stock and deliverable:
            send_telegram_message(f"🟢 <b>{name}</b> is <b>In Stock</b> & <b>Deliverable</b> to {PINCODE}\n{url}")
        elif in_stock:
            send_telegram_message(f"🟡 <b>{name}</b> is <b>In Stock</b> but <b>Not Deliverable</b> to {PINCODE}\n{url}")
        else:
            print(f"[🔴 Out of Stock] {name}")
    except Exception as e:
        print(f"[⚠️ Error: {name}] {e}")

if __name__ == "__main__":
    while True:
        print("🔍 Checking Croma products...")
        for name, url in PRODUCTS.items():
            check_stock(url, name)
        time.sleep(60)
