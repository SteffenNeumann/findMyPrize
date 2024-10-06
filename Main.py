from playwright.sync_api import sync_playwright
from twilio.rest import Client
import os
import urllib.parse
import requests

env_file_path = './twilio.env'
if os.path.exists(env_file_path):
    with open(env_file_path, 'r') as f:
        for line in f:
            key, value = line.strip().split('=')
            os.environ[key] = value

# Load environment variables
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
RECIPIENT_PHONE_NUMBER = '+491735159382'

product = "Red Bull"
zip_code = "85435"

def get_coordinates(zip_code, country="Germany"):
    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        "postalcode": zip_code,
        "country": country,
        "format": "json"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    return None

# Function to send SMS via Twilio
def send_sms(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=RECIPIENT_PHONE_NUMBER
    )

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    coordinates = get_coordinates(zip_code)
    if coordinates:
        lat, lng = coordinates
        
        encoded_query = urllib.parse.quote(product)
        
        flexible_url = f"https://www.meinprospekt.de/webapp/?query={encoded_query}&lat={lat}&lng={lng}"
        
        page.goto(flexible_url)
        page.wait_for_load_state('load', timeout=20000)

        # Select the section with the offers
        offer_section = page.query_selector('section[data-testid="OfferGrid"]')

        if offer_section:
            products = offer_section.query_selector_all('div.flex.cursor-pointer.flex-col.justify-between.rounded-lg.border.border-gray.bg-white.text-dark')
            for product in products:
                store_element = product.query_selector('.truncate.text-sm.text-dark1')
                price_element = product.query_selector('.text-md.font-bold.text-primary')

                if store_element and price_element:
                    store = store_element.inner_text().strip()
                    price_text = price_element.inner_text().strip()

                    try:
                        # Convert price to float
                        price_value = float(price_text.replace('€', '').replace(',', '.').strip())

                        # Check if the price is less than 0.99 euros
                        if price_value < 0.99:
                            message = f"Deal alert! {store} offers Red Bull for only {price_text}!"
                            send_sms(message)
                            print(message)
                    except ValueError:
                        print(f"Could not convert price to float: {price_text}")

    else:
        print("Could not find coordinates for the given zip code")

    browser.close()