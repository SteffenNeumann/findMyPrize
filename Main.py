from playwright.sync_api import sync_playwright
from twilio.rest import Client
import os
import re

env_file_path = './twilio.env'
if os.path.exists(env_file_path):
    with open(env_file_path, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            os.environ[key] = value
# Lade die Umgebungsvariablen
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
RECIPIENT_PHONE_NUMBER = '+491735159382'

# Regex pattern for Red Bull products
pattern = re.compile(r'Red Bull', re.IGNORECASE)


# Funktion zum Senden einer SMS über Twilio
def send_sms(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=RECIPIENT_PHONE_NUMBER
    )


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Setze headless=True
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    page.goto('https://www.rewe.de/marktseite/moosinning/431024/rewe-markt-einfangstrasse-6/')
    page.wait_for_load_state('load', timeout=20000)
    page.goto('https://www.rewe.de/angebote/nationale-angebote/')

    page.wait_for_load_state('load', timeout=20000)
    products = page.query_selector_all('article[class="cor-offer-renderer-tile cor-link"]')
    for product in products:
        h3_element = product.query_selector('h3.cor-offer-information__title')
        if h3_element:
            link_element = h3_element.query_selector('a.cor-offer-information__title-link')
            if link_element:
                product_name = link_element.inner_text().strip()
                product_price = link_element.get_attribute('aria-label').split(',')[-1].strip()
                product_id = link_element.get_attribute('data-offer-id')

                # Use the regex pattern to check for Red Bull products
                if pattern.search(product_name):
                    # Extract the numeric price value
                    price_value = float(product_price.replace(',', '.').split()[-1])

                    # Check if the price is less than 0.99 euros
                    if price_value < 0.99:
                        message = f"Red Bull deal alert! {product_name} for only {product_price}!"
                        send_sms(message)

                # print(f"Product: {product_name}")
                # print(f"Price: {product_price}")
                # print(f"Product ID: {product_id}")
                # print("---")

    browser.close()
