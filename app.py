import json
import time
import threading
import requests
from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

PRODUCTS_FILE = "products.json"
CONFIG_FILE = "config.json"

# ---------- Helpers ----------
def load_products():
    try:
        with open(PRODUCTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

def load_config():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

cfg = load_config()
CHECK_INTERVAL = int(cfg.get("CHECK_INTERVAL", 60))
TELEGRAM_BOT_TOKEN = cfg["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = cfg["TELEGRAM_CHAT_ID"]

def send_telegram_message(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
    except Exception as e:
        print("Telegram send error:", e)

def make_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=chrome_options)

PRICE_SELECTORS = [
    "div.Nx9bqj.CxhGGd",   # current common price selector
    "div._30jeq3._16Jk6d", # older layout fallback
]

def extract_price(driver):
    for sel in PRICE_SELECTORS:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            raw = el.text.strip().replace("₹", "").replace(",", "")
            if raw.isdigit():
                return int(raw)
            # handle things like "46,999*"
            digits = "".join(ch for ch in raw if ch.isdigit())
            if digits:
                return int(digits)
        except Exception:
            continue
    return None

# ---------- Background price checker ----------
def price_checker_loop():
    while True:
        products = load_products()
        if not products:
            time.sleep(CHECK_INTERVAL)
            continue

        try:
            driver = make_driver()  # one Chrome session per cycle for speed
        except Exception as e:
            print("Chrome start error:", e)
            time.sleep(CHECK_INTERVAL)
            continue

        try:
            for p in products:
                if not p.get("enabled", True):
                    continue
                name = p.get("name", "Unknown")
                url = p["url"]
                target = int(p["target_price"])

                print(f"Checking price for: {name}\nLink: {url}")
                try:
                    driver.get(url)
                    time.sleep(4)  # allow render
                    price = extract_price(driver)
                    if price:
                        print(f"Current price: ₹{price}")
                        if price <= target:
                            send_telegram_message(f"📢 Price Alert! {name} is now ₹{price}\n{url}")
                            print("Alert sent to Telegram!")
                    else:
                        print("Price not found (selector/layout changed).")
                except Exception as e:
                    print(f"Error fetching price for {name}: {e}")
        finally:
            driver.quit()

        time.sleep(CHECK_INTERVAL)

# ---------- Flask app ----------
app = Flask(__name__)

@app.route("/")
def home():
    products = load_products()
    return render_template("index.html", products=products, interval=CHECK_INTERVAL)

@app.route("/add", methods=["POST"])
def add_product():
    data = request.form
    name = data.get("name", "").strip()
    url = data.get("url", "").strip()
    target = data.get("target_price", "").strip()
    if not (name and url and target.isdigit()):
        return jsonify({"ok": False, "msg": "Invalid form data"}), 400
    products = load_products()
    products.append({
        "name": name,
        "url": url,
        "target_price": int(target),
        "enabled": True
    })
    save_products(products)
    return jsonify({"ok": True})

@app.route("/delete", methods=["POST"])
def delete_product():
    idx = request.json.get("index", None)
    products = load_products()
    if idx is None or idx < 0 or idx >= len(products):
        return jsonify({"ok": False, "msg": "Invalid index"}), 400
    products.pop(idx)
    save_products(products)
    return jsonify({"ok": True})

@app.route("/toggle", methods=["POST"])
def toggle_product():
    idx = request.json.get("index", None)
    products = load_products()
    if idx is None or idx < 0 or idx >= len(products):
        return jsonify({"ok": False, "msg": "Invalid index"}), 400
    products[idx]["enabled"] = not products[idx].get("enabled", True)
    save_products(products)
    return jsonify({"ok": True, "enabled": products[idx]["enabled"]})

@app.route("/update_price", methods=["POST"])
def update_price():
    idx = request.json.get("index", None)
    new_price = request.json.get("target_price", None)
    products = load_products()
    if (
        idx is None or new_price is None or
        idx < 0 or idx >= len(products)
    ):
        return jsonify({"ok": False, "msg": "Invalid data"}), 400
    try:
        products[idx]["target_price"] = int(new_price)
    except ValueError:
        return jsonify({"ok": False, "msg": "Price must be a number"}), 400
    save_products(products)
    return jsonify({"ok": True})

if __name__ == "__main__":
    # Start background checker
    t = threading.Thread(target=price_checker_loop, daemon=True)
    t.start()
    # Web GUI
    app.run(host="0.0.0.0", port=5000)
