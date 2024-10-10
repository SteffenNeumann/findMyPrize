from playwright.sync_api import sync_playwright
import os
from geopy.geocoders import Nominatim
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from dataclasses import dataclass
import sqlite3

geolocator = Nominatim(user_agent="my_user_agent")
city = "Erding"
country = "Germany"

loc = geolocator.geocode(city + "," + country)
my_long = loc.longitude
my_lat = loc.latitude

load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

def init_db():
    conn = sqlite3.connect('deals.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS deals
                 (timestamp TEXT, product TEXT, store TEXT, price REAL, target_price REAL)''')
    conn.commit()
    conn.close()

def log_deal(product, store, price, target_price):
    conn = sqlite3.connect('deals.db')
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO deals VALUES (?, ?, ?, ?, ?)",
              (timestamp, product, store, price, target_price))
    conn.commit()
    conn.close()

def send_email(subject, message):
    sender_email = EMAIL_ADDRESS
    sender_password = EMAIL_PASSWORD
    receiver_email = RECIPIENT_EMAIL

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(message, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()

@dataclass
class Product:
    name: str
    target_price: float

PRODUCTS_AND_PRICES = [
    Product("Crema d'Oro", 11.00),
    Product("Hafermilch", 0.98),
    Product("Red Bull", 0.90),
]

init_db()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    for item in PRODUCTS_AND_PRICES:
        product = item.name
        target_price = item.target_price
        url = f"https://www.meinprospekt.de/webapp/?query={product}&lat={my_lat}&lng={my_long}"

        page.goto(url)
        page.wait_for_load_state("load", timeout=20000)
        offer_section = page.wait_for_selector(
            ".search-group-grid-content", timeout=30000
        )
        if not offer_section:
            output = f"No Product {product} found"
        else:
            products = offer_section.query_selector_all(
                ".card.card--offer.slider-preventClick"
            )
            output = ""
            for product_element in products:
                store_element = product_element.query_selector(".card__subtitle")
                price_element = product_element.query_selector(
                    ".card__prices-main-price"
                )
                if store_element and price_element:
                    store = store_element.inner_text().strip()
                    price_text = price_element.inner_text().strip()
                    try:
                        price_value = float(
                            price_text.replace("€", "").replace(",", ".").strip()
                        )
                        if price_value <= target_price:
                            subject = "Deal Alert!"
                            product_name_element = product_element.query_selector(
                                ".card__title"
                            )
                            if product_name_element:
                                product_name = product_name_element.inner_text().strip()
                            else:
                                product_name = "Unknown Product"

                            message = f"Deal alert! {store} offers {product_name} for {price_text}! (Target price: €{target_price:.2f})"
                            send_email(subject, message)
                            log_deal(product_name, store, price_value, target_price)
                            output += message + "\n"
                    except ValueError:
                        print(f"Could not convert price to float: {price_text}")
        print(output)
    browser.close()
