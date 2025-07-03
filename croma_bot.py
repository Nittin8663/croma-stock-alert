import os
import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

def load_products_from_csv(csv_file):
    products = []
    try:
        with open(csv_file, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if "name" in row and "url" in row:
                    products.append({
                        "name": row["name"],
                        "url": row["url"]
                    })
    except Exception as e:
        print(f"❌ Failed to load products from CSV: {e}")
    return products

PRODUCTS = load_products_from_csv("product.csv")

def send_email(subject, message):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(message, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, EMAIL_TO, msg.as_string())
            print(f"✅ Email sent: {subject}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def check_croma_stock():
    print(f"🔄 Checking stock at {time.strftime('%Y-%m-%d %H:%M:%S')}")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    for product in PRODUCTS:
        try:
            driver.get(product["url"])
            time.sleep(3)
            body_text = driver.page_source.lower()

            if "sold out" in body_text or "notify me" in body_text:
                print(f"❌ Out of stock: {product['name']}")
            else:
                print(f"✅ In stock: {product['name']}")
                send_email(
                    subject=f"IN STOCK: {product['name']}",
                    message=f"{product['name']} is available now:\n{product['url']}"
                )
        except Exception as e:
            print(f"⚠️ Error checking {product['name']}: {e}")

    driver.quit()

if __name__ == "__main__":
    check_croma_stock()
