from playwright.sync_api import sync_playwright
from twilio.rest import Client
import os
import urllib.parse
from geopy.geocoders import Nominatim

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

product = "Red Bull"
zip_code = "85435"

# Initialize the geocoder
geolocator = Nominatim(user_agent="my_app")

# Get the location from the zip code
location = geolocator.geocode(zip_code + ", Germany")

# Funktion zum Senden einer SMS über Twilio
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

    if location:
        lat = location.latitude
        lng = location.longitude
        
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

                        # Check if the price is less than 0.99 euros and the store or product name matches the pattern
                        if price_value < 0.99 :
                            message = f"Deal alert! {store} offers Red Bull for only {price_text}!"
                            send_sms(message)
                            print(message)
                    except ValueError:
                        print(f"Could not convert price to float: {price_text}")

    else:
        print("Could not find coordinates for the given zip code")

    browser.close()