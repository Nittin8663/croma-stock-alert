import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime

# Load Telegram credentials from JSON
with open('telegram.json') as f:
    telegram_config = json.load(f)

TOKEN = telegram_config['token']
CHAT_ID = telegram_config['chat_id']

# Product URLs
PRODUCTS = {
    "Vivo X200 FE 5G": "https://www.croma.com/vivo-x200-fe-5g-12gb-ram-256gb-frost-blue-/p/316890",
    "Vivo Y300 5G": "https://www.croma.com/vivo-y300-5g-8gb-ram-128gb-rom-emerald-green-/p/311901"
}

# Track previous status to avoid duplicate alerts
previous_status = {name: None for name in PRODUCTS.keys()}

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, json=payload)

def check_stock(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Customize based on Croma's HTML (inspect page to update selectors)
        if "Add to Cart" in str(soup):
            return "IN STOCK"
        elif "Out of Stock" in str(soup) or "Notify Me" in str(soup):
            return "OUT OF STOCK"
        else:
            return "UNKNOWN"
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return "ERROR"

def main():
    print("Starting stock monitor... Press Ctrl+C to stop.")
    while True:
        for name, url in PRODUCTS.items():
            current_status = check_stock(url)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if current_status != previous_status[name]:
                message = f"🚀 {name}: {current_status}\n{url}\n({timestamp})"
                print(message)
                send_telegram_alert(message)
                previous_status[name] = current_status
            
            time.sleep(1)  # Small delay between product checks
        
        time.sleep(20)  # Check every 20 seconds

if __name__ == "__main__":
    main()
