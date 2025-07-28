import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

CHECK_INTERVAL = 20  # seconds
PINCODE = "400049"

# Load Telegram config
with open('telegram.json', 'r') as f:
    data = json.load(f)
    TELEGRAM_TOKEN = data['token']
    TELEGRAM_CHAT_ID = data['chat_id']

# Hardcoded products
PRODUCTS = [
    {
        "name": "Y300-Silver",
        "url": "https://www.croma.com/vivo-y300-5g-8gb-ram-128gb-rom-titanium-silver-/p/311900"
    },
    {
        "name": "Y400",
        "url": "https://www.croma.com/vivo-x200-fe-5g-12gb-ram-256gb-frost-blue-/p/316890"
    }
]

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"[❌] Telegram error: {e}")

def setup_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    return webdriver.Chrome(options=options)

def check_stock_and_delivery(driver):
    for product in PRODUCTS:
        name = product['name']
        url = product['url']
        print(f"🔍 Checking {name}...")
        try:
            driver.get(url)
            time.sleep(4)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            out_of_stock = soup.find("div", class_="out-of-stock-msg")
            in_stock = out_of_stock is None

            # Try to locate and enter pincode
            delivery_status = "⚠️ Pincode input not found"
            try:
                input_field = None
                # Try known selectors
                try:
                    input_field = driver.find_element(By.ID, "pincode-check")
                except:
                    try:
                        input_field = driver.find_element(By.XPATH, '//input[contains(@placeholder, "Enter Pincode")]')
                    except:
                        try:
                            input_field = driver.find_element(By.CSS_SELECTOR, 'input[type="tel"]')
                        except:
                            input_field = None

                if input_field:
                    input_field.clear()
                    input_field.send_keys(PINCODE)
                    input_field.send_keys(Keys.ENTER)
                    time.sleep(3)

                    page = BeautifulSoup(driver.page_source, 'html.parser')
                    deliverable = not bool(page.find(string=lambda t: "not deliverable" in t.lower() or "unavailable" in t.lower()))
                    delivery_status = "✅ Deliverable" if deliverable else "❌ Not deliverable"
                else:
                    print(f"[⚠️] Pincode input not found on {name}")

            except Exception as e:
                print(f"[⚠️] Error with pincode input: {e}")

            # Final message
            if in_stock and delivery_status == "✅ Deliverable":
                print(f"[🟢 IN STOCK & DELIVERABLE] {name}")
                send_telegram(f"🟢 *{name}* is *IN STOCK & DELIVERABLE*! \n[Buy Now]({url})")
            elif in_stock:
                print(f"[🟡 In Stock but ❌ Not Deliverable] {name}")
            else:
                print(f"[🔴 Out of Stock] {name}")

        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot Started...")
    driver = setup_browser()
    try:
        while True:
            check_stock_and_delivery(driver)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    finally:
        driver.quit()
