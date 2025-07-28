import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'
PINCODE = "400049"  # Set your delivery pincode here

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

# Check if product is in stock
def is_in_stock(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    out_of_stock_tag = soup.find("div", class_="out-of-stock-msg")
    return out_of_stock_tag is None

# Check pincode deliverability
def is_deliverable(driver):
    try:
        # Click the pincode button or delivery section
        pin_button_xpath = "//button[contains(text(),'Enter Pincode')] | //div[contains(@class,'check-delivery')]"
        pin_trigger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, pin_button_xpath))
        )
        driver.execute_script("arguments[0].click();", pin_trigger)

        # Enter pincode
        pin_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Pincode']"))
        )
        pin_input.clear()
        pin_input.send_keys(PINCODE)
        pin_input.send_keys(Keys.RETURN)

        # Wait for delivery status
        WebDriverWait(driver, 10).until(
            EC.any_of(
                EC.text_to_be_present_in_element((By.XPATH, "//div[contains(@class, 'delivery-msg')]"), "Available"),
                EC.text_to_be_present_in_element((By.XPATH, "//div[contains(@class, 'delivery-msg')]"), "Not Available")
            )
        )

        # Wait for page update
        time.sleep(2)
        page = driver.page_source
        return "Not Available for your pincode" not in page

    except Exception as e:
        print(f"[⚠️] Pincode check error: {e}")
        return False

# Main check logic
def check_stock(driver):
    products = load_products()
    for product in products:
        name = product['name']
        url = product['url']
        try:
            driver.get(url)
            time.sleep(3)  # Allow JS content to load
            page_source = driver.page_source

            if is_in_stock(page_source):
                if is_deliverable(driver):
                    print(f"[🟢 In Stock] {name}")
                    send_telegram_message(f"🟢 *{name}* is *IN STOCK* and *Deliverable*! \n[Buy Now]({url})")
                else:
                    print(f"[⚠️ Not Deliverable] {name}")
            else:
                print(f"[🔴 Out of Stock] {name}")
        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# Runner
if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot (Selenium) Started...")
    browser = setup_browser()
    try:
        while True:
            check_stock(browser)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    finally:
        browser.quit()
