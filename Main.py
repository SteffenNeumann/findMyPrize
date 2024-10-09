from playwright.sync_api import sync_playwright
import os
from geopy.geocoders import Nominatim
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

geolocator = Nominatim(user_agent="my_user_agent")
city ="Erding"
country ="Germany"
product = "Joghurt"

loc = geolocator.geocode(city+','+ country)
my_long=loc.longitude
my_lat=loc.latitude

load_dotenv()

EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL')


def send_email(subject, message):
    sender_email = EMAIL_ADDRESS
    sender_password = EMAIL_PASSWORD
    receiver_email = RECIPIENT_EMAIL
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, sender_password)
    text = msg.as_string()
    server.sendmail(sender_email, receiver_email, text)
    server.quit()


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()

    url = f"https://www.meinprospekt.de/webapp/?query={product}&lat={my_lat}&lng={my_long}"
    
    page.goto(url)
    page.wait_for_load_state('load', timeout=20000)

    offer_section = page.wait_for_selector('.search-group-grid-content', timeout=30000)

    if not offer_section:
        output = f"No Product {product} found"
    else:
        products = offer_section.query_selector_all('.card.card--offer.slider-preventClick')
        output = ""
        for product in products:
            store_element = product.query_selector('.card__subtitle')
            price_element = product.query_selector('.card__prices-main-price')

            if store_element and price_element:
                store = store_element.inner_text().strip()
                price_text = price_element.inner_text().strip()

                try:
                    price_value = float(price_text.replace('€', '').replace(',', '.').strip())
                    if price_value < 0.99:
                        subject = "Deal Alert!"
                        product_name_element = product.query_selector('.card__title')
                        if product_name_element:
                            product_name = product_name_element.inner_text().strip()
                        else:
                            product_name = "Unknown Product"
                        
                        message = f"Deal alert! {store} offers {product_name} for only {price_text}!"
                        send_email(subject, message)
                        output += message + "\n"
                except ValueError:
                    print(f"Could not convert price to float: {price_text}")

    browser.close()

    # Store the information in a log file
    log_file_path = '/Users/steffen/Lokal/CronJobs/logfile.log'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - {output}\n"

    with open(log_file_path, 'a') as log_file:
        log_file.write(log_entry)

print(output)
