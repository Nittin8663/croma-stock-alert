import requests
from bs4 import BeautifulSoup
import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import random

# Load Telegram config
with open('telegram.json') as f:
    config = json.load(f)
TOKEN = config['token']
CHAT_ID = config['chat_id']

# Products to track (updated with your URLs)
PRODUCTS = {
    "Vivo Y300 (Emerald Green)": "https://www.croma.com/vivo-y300-5g-8gb-ram-128gb-rom-emerald-green-/p/311901",
    "Vivo Y400 Pro (Freestyle White)": "https://www.croma.com/vivo-y400-pro-5g-8gb-ram-256gb-freestyle-white-/p/316365"
}

# Enhanced detection parameters
STOCK_PARAMS = {
    "in_stock": {
        "element": "button",
        "class": "pdp-add-to-cart",
        "text": "Add to Cart"
    },
    "out_of_stock": {
        "element": "button",
        "class": "out-of-stock-btn",
        "text": "Notify Me"
    }
}

def get_headers():
    return {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.croma.com/"
    }

def send_alert(message):
    """Send Telegram notification with retry logic"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for attempt in range(3):
        try:
            response = requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
            if response.status_code == 200:
                return True
        except Exception as e:
            print(f"⚠️ Telegram alert failed (attempt {attempt + 1}): {str(e)}")
            time.sleep(2)
    return False

def check_stock_web(url):
    """Primary check using requests + BeautifulSoup"""
    try:
        time.sleep(random.uniform(1, 3))  # Random delay
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check IN STOCK
        in_stock_btn = soup.find(
            STOCK_PARAMS["in_stock"]["element"],
            class_=STOCK_PARAMS["in_stock"]["class"],
            text=lambda t: t and STOCK_PARAMS["in_stock"]["text"] in t
        )
        if in_stock_btn:
            return "IN STOCK"
        
        # Check OUT OF STOCK
        out_of_stock_btn = soup.find(
            STOCK_PARAMS["out_of_stock"]["element"],
            class_=STOCK_PARAMS["out_of_stock"]["class"],
            text=lambda t: t and STOCK_PARAMS["out_of_stock"]["text"] in t
        )
        if out_of_stock_btn:
            return "OUT OF STOCK"
            
        # Debug save
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        return "UNKNOWN (No matching elements found)"
        
    except Exception as e:
        return f"WEB ERROR: {str(e)}"

def check_stock_selenium(url):
    """Fallback check using Selenium"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)
        driver.get(url)
        
        # Selenium detection with explicit waits
        try:
            if driver.find_element_by_css_selector(f"button.{STOCK_PARAMS['in_stock']['class']}"):
                return "IN STOCK"
        except:
            pass
            
        try:
            if driver.find_element_by_css_selector(f"button.{STOCK_PARAMS['out_of_stock']['class']}"):
                return "OUT OF STOCK"
        except:
            pass
            
        # Final visual check
        driver.save_screenshot("debug.png")
        html = driver.page_source
        with open("debug_selenium.html", "w", encoding="utf-8") as f:
            f.write(html)
        return "UNKNOWN (See debug files)"
        
    except Exception as e:
        return f"SELENIUM ERROR: {str(e)}"
    finally:
        try:
            driver.quit()
        except:
            pass

def check_stock(url):
    """Main check with priority logic"""
    # First try standard web request
    status = check_stock_web(url)
    
    # If unclear or error, try Selenium
    if "UNKNOWN" in status or "ERROR" in status:
        new_status = check_stock_selenium(url)
        if "UNKNOWN" not in new_status:  # Prefer Selenium result if definitive
            status = new_status
            
    return status

def main():
    print(f"🔍 Monitoring {len(PRODUCTS)} products | Ctrl+C to stop")
    print("Stock Parameters:", STOCK_PARAMS)
    previous_status = {name: None for name in PRODUCTS}
    
    while True:
        for name, url in PRODUCTS.items():
            try:
                current_status = check_stock(url)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Only alert on status changes
                if current_status != previous_status[name]:
                    message = f"🔄 {name}: {current_status}\n{url}\n{timestamp}"
                    print(message)
                    if "UNKNOWN" not in current_status:  # Skip unknown states
                        send_alert(message)
                    previous_status[name] = current_status
                
                # Random delay between product checks (3-8s)
                time.sleep(random.uniform(3, 8))
                
            except Exception as e:
                print(f"⚠️ Critical error checking {name}: {str(e)}")
                time.sleep(60)  # Wait longer after errors
        
        # Main cycle delay (20-30s)
        time.sleep(random.uniform(20, 30))

if __name__ == "__main__":
    main()
