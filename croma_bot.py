import requests
from bs4 import BeautifulSoup
import time
import json

# Load Telegram credentials from JSON file
with open("telegram.json", "r") as file:
    config = json.load(file)
    TELEGRAM_BOT_TOKEN = config["bot_token"]
    TELEGRAM_CHAT_ID = config["chat_id"]

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
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Failed to send message: {e}")

def check_stock(url, name):
    session = requests.Session()
    try:
        response = session.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        # Check Buy Now button
        buy_button = soup.select_one('button[data-testid="buy-button"]')
        buy_available = bool(buy_button and 'Buy Now' in buy_button.get_text())

        # Check pincode deliverability via Croma API
        product_id = url.split("/")[-1].split("/p/")[-1]
        api_url = "https://www.croma.com/ccstoreui/v1/pickupStore/getProductAvailabilityByPincode"
        payload = {"pincode": PINCODE, "productId": product_id}

        pincode_response = session.post(api_url, json=payload, headers=HEADERS, timeout=10)
        deliverable = pincode_response.json().get("pincodeAvailable", False)

        if buy_available and deliverable:
            send_telegram_message(f"🟢 <b>{name}</b> is <b>In Stock</b> & Deliverable to <b>{PINCODE}</b>\n{url}")
        elif buy_available:
            send_telegram_message(f"🟡 <b>{name}</b> is <b>In Stock</b> but <b>Not Deliverable</b> to <b>{PINCODE}</b>\n{url}")
        else:
            print(f"[🔴 Out of Stock] {name}")
    except Exception as e:
        print(f"[⚠️ Error] {name} - {e}")

if __name__ == "__main__":
    while True:
        print("🔍 Checking Croma stock...")
        for name, url in PRODUCTS.items():
            check_stock(url, name)
        time.sleep(60)  # Check every 60 seconds
