import os
import csv
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from email_alert import send_email

load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

PRODUCT_FILE = "products.csv"

def load_product_list():
    products = []
    with open(PRODUCT_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            products.append({
                "name": row["name"],
                "url": row["url"]
            })
    return products

def check_croma_stock():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        driver.set_page_load_timeout(15)
    except WebDriverException as e:
        print(f"❌ Failed to start Chrome: {e}")
        return

    products = load_product_list()

    for product in products:
        name = product["name"]
        url = product["url"]
        print(f"🛒 Checking stock for: {name}")

        try:
            driver.get(url)
            time.sleep(2)  # Wait for page to render

            try:
                # Try to find "Add to Cart" or "Buy Now"
                atc = driver.find_element(By.XPATH, "//button[contains(text(),'Add to Cart') or contains(text(),'Buy Now')]")
                if atc and atc.is_enabled():
                    print(f"✅ In stock: {name}")
                    send_email(
                        subject=f"{name} is in stock!",
                        body=f"The product is in stock:\n{name}\n{url}",
                        to=EMAIL_TO
                    )
                    continue
            except:
                pass

            # Check for Out of Stock marker
            try:
                out_text = driver.find_element(By.XPATH, "//button[contains(text(),'Notify Me')]")
                if out_text:
                    print(f"❌ Out of stock: {name}")
            except:
                print(f"❓ Stock status unknown: {name}")

        except TimeoutException:
            print(f"⚠️ Timeout while loading: {url}")
        except Exception as e:
            print(f"⚠️ Error checking {name}: {e}")

    driver.quit()

if __name__ == "__main__":
    print(f"🔄 Checking stock at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    check_croma_stock()
