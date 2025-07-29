import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from selenium import webdriver  # Backup for dynamic content
import random

# Load Telegram config
with open('telegram.json') as f:
    config = json.load(f)
TOKEN = config['token']
CHAT_ID = config['chat_id']

# Products to track
PRODUCTS = {
    "Vivo X200 FE 5G": "https://www.croma.com/vivo-x200-fe-5g-12gb-ram-256gb-frost-blue-/p/316890",
    "Vivo Y300 5G": "https://www.croma.com/vivo-y300-5g-8gb-ram-128gb-rom-emerald-green-/p/311901"
}

# Rotating headers to prevent blocking
HEADERS = {
    "User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    ]),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.croma.com/"
}

def send_alert(message):
    """Send Telegram notification"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print(f"Telegram alert failed: {e}")

def check_stock(url):
    """Check stock status with Croma-specific selectors"""
    try:
        # Random delay to mimic human behavior
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Croma-specific selectors (updated July 2025)
        add_to_cart = soup.find("button", class_="pdp-add-to-cart")
        notify_me = soup.find("button", text="Notify Me")  # Out of stock indicator
        
        if add_to_cart and "Add to Cart" in add_to_cart.text:
            return "IN STOCK"
        elif notify_me:
            return "OUT OF STOCK"
        
        # Fallback to Selenium if requests fails
        return check_stock_selenium(url)
            
    except Exception as e:
        return f"ERROR: {str(e)}"

def check_stock_selenium(url):
    """Backup method for JavaScript-heavy pages"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in background
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        # Selenium selectors (same logic as BeautifulSoup)
        try:
            if driver.find_element_by_css_selector("button.pdp-add-to-cart"):
                return "IN STOCK"
            elif driver.find_element_by_xpath("//button[contains(text(),'Notify Me')]"):
                return "OUT OF STOCK"
        finally:
            driver.quit()
            
        return "UNKNOWN (Selenium couldn't detect status)"
    except Exception as e:
        return f"SELENIUM ERROR: {str(e)}"

def main():
    print(f"🚀 Tracking {len(PRODUCTS)} products. Press Ctrl+C to stop.")
    previous_status = {name: None for name in PRODUCTS}
    
    while True:
        for name, url in PRODUCTS.items():
            status = check_stock(url)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if status != previous_status[name]:
                alert = f"📢 {name}: {status}\n{url}\n({timestamp})"
                print(alert)
                if "ERROR" not in status:
                    send_alert(alert)
                previous_status[name] = status
            
            time.sleep(random.uniform(3, 7))  # Random delay between products
        
        time.sleep(20)  # Main check interval

if __name__ == "__main__":
    main()
