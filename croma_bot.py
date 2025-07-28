import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIG ===
CHECK_INTERVAL = 20  # seconds
PRODUCTS_FILE = 'products.json'
TELEGRAM_FILE = 'telegram.json'
# Define a longer timeout for page loading to ensure all elements are present
PAGE_LOAD_TIMEOUT = 15 # seconds - Increased timeout for more complex pages

# Load Telegram config
def load_telegram_config():
    try:
        with open(TELEGRAM_FILE, 'r') as f:
            data = json.load(f)
            return data.get('token'), data.get('chat_id')
    except FileNotFoundError:
        print(f"[❌] Error: {TELEGRAM_FILE} not found. Please create it with 'token' and 'chat_id'.")
        exit()
    except json.JSONDecodeError:
        print(f"[❌] Error: Could not decode JSON from {TELEGRAM_FILE}. Check file format.")
        exit()

TELEGRAM_TOKEN, TELEGRAM_CHAT_ID = load_telegram_config()

# Load product list
def load_products():
    try:
        with open(PRODUCTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[❌] Error: {PRODUCTS_FILE} not found. Please create it with your product list.")
        exit()
    except json.JSONDecodeError:
        print(f"[❌] Error: Could not decode JSON from {PRODUCTS_FILE}. Check file format.")
        exit()

# Send Telegram alert
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, data=data)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        print(f"[✅] Telegram message sent.")
    except requests.exceptions.RequestException as e:
        print(f"[❌] Error sending Telegram message: {e}")
    except Exception as e:
        print(f"[❌] An unexpected error occurred while sending message: {e}")

# Setup headless Chrome browser
def setup_browser():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')
    # Add user-agent to mimic a real browser, sometimes helps with bot detection
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    # Initialize WebDriver with options
    # Ensure you have chromedriver installed and in your PATH, or specify its path:
    # driver = webdriver.Chrome(executable_path='/path/to/chromedriver', options=options)
    driver = webdriver.Chrome(options=options)
    return driver

# Check stock from HTML
def is_in_stock(driver, url):
    """
    Checks if a product is in stock on the Croma page.
    This function now takes the WebDriver instance and the URL directly.
    It uses explicit waits for better reliability and more comprehensive checks.
    """
    try:
        # Wait for the page to load and for a common element to be present
        # This ensures we have a DOM to parse before proceeding
        WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.TAG_NAME, "body")) 
        )
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # --- Primary Checks: Look for explicit "Out of Stock" indicators ---
        # 1. Original out-of-stock-msg div
        out_of_stock_tag = soup.find("div", class_="out-of-stock-msg")
        if out_of_stock_tag:
            print("DEBUG: Found 'out-of-stock-msg' div.")
            return False

        # 2. Check for "Notify Me" button/text
        notify_me_button = soup.find("button", class_="notify-me-btn")
        if notify_me_button and "Notify Me" in notify_me_button.get_text(strip=True):
            print("DEBUG: Found 'Notify Me' button.")
            return False
            
        # 3. Check for specific text indicating unavailability in common areas (e.g., product status, price area)
        # These are common phrases for out-of-stock items. You might need to refine these based on Croma's exact wording.
        unavailable_texts = ["out of stock", "currently unavailable", "sold out", "not available"]
        for text in unavailable_texts:
            if text in page_source.lower():
                print(f"DEBUG: Found '{text}' in page source.")
                return False

        # --- Secondary Check: "Add to Cart" or "Buy Now" button status ---
        # This is often the most reliable positive indicator.
        add_to_cart_button = soup.find("button", class_="add-to-cart-button") 
        if add_to_cart_button:
            button_text = add_to_cart_button.get_text(strip=True).lower()
            
            # Check if the button is explicitly disabled by an attribute
            if 'disabled' in add_to_cart_button.attrs:
                print("DEBUG: Found 'Add to Cart' button with 'disabled' attribute.")
                return False
            
            # Check if the button's text indicates unavailability
            if any(text in button_text for text in unavailable_texts + ["notify me"]):
                print(f"DEBUG: 'Add to Cart' button text indicates unavailability: '{button_text}'.")
                return False
            
            # If the button exists, is not disabled, and its text doesn't indicate unavailability,
            # then it's likely in stock.
            print("DEBUG: Found enabled 'Add to Cart' button with positive text.")
            return True 
        
        # If no explicit "out of stock" indicator is found and no "add to cart" button
        # or the add to cart button is not clearly indicating stock, assume out of stock.
        print("DEBUG: No clear 'in stock' indicator found. Assuming out of stock.")
        return False

    except Exception as e:
        print(f"[❌] Error in is_in_stock for {url}: {e}")
        return False # Assume out of stock on error to be safe

# Main checking loop
def check_stock(driver):
    products = load_products()
    if not products:
        print("No products loaded. Please check products.json.")
        return

    for product in products:
        name = product.get('name', 'Unknown Product')
        url = product.get('url')

        if not url:
            print(f"[⚠️] Product '{name}' has no URL. Skipping.")
            continue

        print(f"Checking {name} at {url}...")
        try:
            driver.get(url)
            
            # Use a more targeted wait: wait for either an out-of-stock message, notify button, or add-to-cart button
            try:
                WebDriverWait(driver, PAGE_LOAD_TIMEOUT).until(
                    EC.presence_of_element_located((By.XPATH, 
                        "//div[contains(@class, 'out-of-stock-msg')] | //button[contains(@class, 'add-to-cart-button')] | //button[contains(@class, 'notify-me-btn')] | //*[contains(text(), 'out of stock')] | //*[contains(text(), 'currently unavailable')]"))
                )
            except Exception as e:
                print(f"    [⚠️] Timeout waiting for specific stock indicators on {name}. Proceeding with current page source. Error: {e}")

            if is_in_stock(driver, url): # Pass driver and url to the function
                print(f"[🟢 In Stock] {name}")
                send_telegram_message(f"🟢 *{name}* is *IN STOCK*! \n[Buy Now]({url})")
            else:
                print(f"[🔴 Out of Stock] {name}")
        except Exception as e:
            print(f"[❌] Error checking {name}: {e}")

# Runner
if __name__ == "__main__":
    print("🚀 Croma Stock Alert Bot (Selenium) Started...")
    browser = None 
    try:
        browser = setup_browser()
        while True:
            check_stock(browser)
            print(f"Waiting for {CHECK_INTERVAL} seconds before next check...")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("🛑 Bot stopped by user.")
    except Exception as e:
        print(f"[❌] An unhandled error occurred: {e}")
    finally:
        if browser:
            print("Closing browser...")
            browser.quit()
