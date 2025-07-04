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
    if not os.path.exists(PRODUCT_FILE):
        print(f"❌ Product file not found: {PRODUCT_FILE}")
        return products
    with open(PRODUCT_FILE, new_
