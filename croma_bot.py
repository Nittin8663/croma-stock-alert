import time, json, requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

CHECK_INTERVAL = 20
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'

def load_telegram_config():
    with open(TELEGRAM_FILE, 'r') as f:
        d = json.load(f)
    return d['token'], d['chat_id']

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

def load_products():
    with open(PRODUCTS_FILE, 'r') as f:
        return json.load(f)

def send_telegram_message(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("[❌] Telegram Error:", e)

def setup_browser():
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920x1080')
    return webdriver.Chrome(options=opts)

def is_in_stock(driver):
    try:
        for xpath in ["//button[contains(text(), 'Add to Cart')]", "//button[contains(text(), 'Buy Now')]"]:
            btn = driver.find_element(By.XPATH, xpath)
            txt = btn.text.lower()
            if 'notify' in txt or 'sold out' in txt:
                continue
            if btn.is_displayed() and btn.is_enabled():
                return True
        return False
    except:
        return False

def check_stock(driver):
    for p in load_products():
        name, url = p['name'], p['url']
        try:
            driver.get(url); time.sleep(3)
            if is_in_stock(driver):
                print(f"[🟢 In Stock] {name}")
                send_telegram_message(f"🟢 *{name}* is *IN STOCK*! \n[Buy Now]({url})")
            else:
                print(f"[🔴 Out of Stock] {name}")
        except Exception as e:
            print("[❌]", name, "error:", e)

if __name__ == "__main__":
    print("🚀 Bot started...")
    drv = setup_browser()
    try:
        while True:
            check_stock(drv)
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Stopped")
    finally:
        drv.quit()
