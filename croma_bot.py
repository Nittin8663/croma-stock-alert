import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os

# Load product URLs
with open('products.json', 'r') as f:
    products = json.load(f)

# Load Telegram bot config
with open('telegram.json', 'r') as f:
    telegram_config = json.load(f)

TELEGRAM_BOT_TOKEN = telegram_config['bot_token']
TELEGRAM_CHAT_ID = telegram_config['chat_id']

from telegram import Bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1920,1080')
options.add_argument('--disable-gpu')

print("🚀 Croma Stock Alert Bot Started...")

def is_deliverable(driver):
    try:
        # Click on change pincode or check delivery
        change_pin = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div.delivery-check'))
        )
        change_pin.click()

        # Wait for input to appear and enter pincode
        pincode_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Enter Pincode']"))
        )
        pincode_input.clear()
        pincode_input.send_keys("400049")
        pincode_input.send_keys(Keys.RETURN)

        time.sleep(3)
        page_source = driver.page_source
        if "Not Available for your pincode" in page_source:
            return False
        return True
    except Exception:
        return False

def check_stock(product):
    name = product['name']
    url = product['url']

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)
        time.sleep(5)

        add_to_cart_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'Add to Cart')]")

        if add_to_cart_buttons:
            if is_deliverable(driver):
                message = f"[🟢 In Stock] {name}"
                print(message)
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            else:
                print(f"[❌ Not Deliverable] {name}")
        else:
            print(f"[🔴 Out of Stock] {name}")

        driver.quit()

    except WebDriverException as e:
        print(f"[⚠️] Failed to fetch {name} - {e}")
        try:
            driver.quit()
        except:
            pass

while True:
    for product in products:
        check_stock(product)
    time.sleep(60)
