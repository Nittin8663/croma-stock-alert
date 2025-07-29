import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from selenium import webdriver  # Only if needed for dynamic content

# Load Telegram config
with open('telegram.json') as f:
    config = json.load(f)
TOKEN = config['token']
CHAT_ID = config['chat_id']

# Products to track (add more as needed)
PRODUCTS = {
    "Vivo X200 FE 5G": "https://www.croma.com/vivo-x200-fe-5g-12gb-ram-256gb-frost-blue-/p/316890",
    "Vivo Y300 5G": "https://www.croma.com/vivo-y300-5g-8gb-ram-128gb-rom-emerald-green-/p/311901"
}

# Browser-like headers to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.croma.com/"
}

def send_alert(message):
    """Send Telegram notification"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message})

def check_stock(url):
    """Check stock status with error handling"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # CUSTOMIZE THESE SELECTORS BASED ON CROMA'S HTML
        # Option 1: Check for button text
        if soup.find("button", text=lambda t: t and "Add to Cart" in t):
            return "IN STOCK"
        
        # Option 2: Check for out-of-stock class (inspect Croma's page)
        if soup.find("div", class_="out-of-stock"):  # Update class name
            return "OUT OF STOCK"
        
        # Fallback: Raw text search (less reliable)
        page_text = soup.get_text().lower()
        if "add to cart" in page_text:
            return "IN STOCK"
        elif "out of stock" in page_text or "notify me" in page_text:
            return "OUT OF STOCK"
        
        return "UNKNOWN (Update selectors in bot.py)"
    
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    print(f"🚀 Tracking {len(PRODUCTS)} products. Press Ctrl+C to stop.")
    previous_status = {name: None for name in PRODUCTS}
    
    while True:
        for name, url in PRODUCTS.items():
            status = check_stock(url)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if status != previous_status[name]:
                alert = f"📢 {name}: {status}\n{url}\n({timestamp})"
                print(alert)  # Console log
                if "ERROR" not in status and "UNKNOWN" not in status:
                    send_alert(alert)  # Telegram only for clear status changes
                previous_status[name] = status
            
            time.sleep(5)  # Delay between product checks
        
        time.sleep(20)  # Main check interval

if __name__ == "__main__":
    main()
