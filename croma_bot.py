import time
import requests
from bs4 import BeautifulSoup
import json

def load_telegram_config(path='telegram.json'):
    with open(path) as f:
        return json.load(f)

def is_in_stock(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    # Use string= as per BeautifulSoup's current best practice
    out_of_stock = soup.find(string=lambda t: t and "out of stock" in t.lower())
    return not out_of_stock

def send_telegram_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    requests.post(url, data=data)

if __name__ == '__main__':
    config = load_telegram_config('telegram.json')
    CROMA_PRODUCT_URL = 'https://www.croma.com/vivo-y400-pro-5g-8gb-ram-256gb-freestyle-white-/p/316365'
    CHECK_INTERVAL = 20  # seconds
    already_notified = False
    while True:
        try:
            if is_in_stock(CROMA_PRODUCT_URL):
                if not already_notified:
                    send_telegram_message(
                        config['bot_token'],
                        config['chat_id'],
                        f"Product is IN STOCK! {CROMA_PRODUCT_URL}"
                    )
                    already_notified = True
            else:
                print("Still out of stock...")
                already_notified = False
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(CHECK_INTERVAL)
