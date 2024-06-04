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
    products = page.query_selector_all('article[class="cor-offer-renderer-tile cor-link"]')
    for product in products:
        label = product.get_attribute('aria-label')
        name = label.split(',')[0]
        price = float(label.split(' ')[-1][:-1].replace(',', '.'))
        pattern = re.compile(r"red\s*bull.*?", re.IGNORECASE)
        # Suche nach dem Muster im Text
        match = re.search(pattern, name)
        if match and price < 0.99:
            message = f"Erfolgreiche Suche nach 'RedBull' mit einem Preis unter 1,0 €!"
            # SMS senden, wenn das gewünschte Produkt gefunden wurde
            send_sms(message)

    browser.close()
