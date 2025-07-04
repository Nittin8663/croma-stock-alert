import os
import csv
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from email_alert import send_email

# Load environment variables
load_dotenv()

EMAIL_TO = os.getenv("EMAIL_TO")
PRODUCT_FILE = "products.csv"

def load_product_list():
    print("🔄 Loading products from CSV...")
    products = []
    if not os.path.exists(PRODUCT_FILE):
        print(f"❌ File not found: {PRODUCT_FILE}")
        return products

    with open(PRODUCT_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            print(f"➡️ Found product: {row}")
            products.append({
                "name": row["name"],
                "u
