import re
import time
import csv
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, WebDriverException

chromedriver_path = 'C:/Users/nicop/anaconda3/scraping/mpscraper/chromedriver.exe'

# Setup the Chrome Driver using Service
service = Service(chromedriver_path)
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')  # Disable SSL certificate errors
driver = webdriver.Chrome(service=service, options=options)
driver.get("https://www.marktplaats.nl/l/telecommunicatie/mobiele-telefoons-apple-iphone/#q:iphone+8|offeredSince:Vandaag|searchInTitleAndDescription:true")
driver.maximize_window()

listings_data = []
seen_descriptions = set()  # Set to track seen descriptions

def is_valid_price(price):
    return re.match(r"^\€\s*\d+,\d{2}$", price) is not None

def check_next_page():
    try:
        next_page_button = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.hz-Link.hz-Button--primary i.hz-SvgIconArrowRight"))
        )
                
        ActionChains(driver).move_to_element(next_page_button).perform()
        time.sleep(1)
        
        if next_page_button.get_attribute('aria-disabled') == 'true':
            return False
        next_page_button.click()
        return True
    except (TimeoutException, NoSuchElementException, WebDriverException) as e:
        print(f"Next page not found or clickable: {e}")
        return False

try:
    wait = WebDriverWait(driver, 2)
    iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[id^='sp_message_iframe_']")))
    driver.switch_to.frame(iframe)
    accepteren_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@title='Accepteren']")))
    accepteren_button.click()
    driver.switch_to.default_content()

    page_number = 1  # Track the current page number for debugging

    while True:
        print(f"Scraping page {page_number}...")
        listings = WebDriverWait(driver, 1).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".hz-Listing.hz-Listing--list-item:not(.hz-Listing--hz-Listing--cas)"))
        )
        for i in range(len(listings)):
            try:
                listing = WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, f"li.hz-Listing.hz-Listing--list-item:nth-of-type({i + 1})"))
                )
                ActionChains(driver).move_to_element(listing).perform()
                time.sleep(.1)

                # Check for sub-images and skip the listing if sub-images are found
                try:
                    sub_images = listing.find_element(By.CSS_SELECTOR, ".hz-Listing-sub-images")
                    print(f"Skipping listing {i + 1} due to presence of sub-images.")
                    continue
                except NoSuchElementException:
                    pass

                price = driver.execute_script("return arguments[0].querySelector('.hz-Listing-price').innerText;", listing)
                if not is_valid_price(price):
                    continue

                description_snippet = driver.execute_script("return arguments[0].querySelector('.hz-Listing-description').innerText;", listing)
                # Check for 'used products' or 'garantie' in the description and skip the listing if found
                if 'used products' in description_snippet.lower() or 'garantie' in description_snippet.lower():
                    print(f"Skipping listing {i + 1} due to 'used products' in description.")
                    continue

                # Check for duplicate descriptions and skip if found
                if description_snippet in seen_descriptions:
                    print(f"Skipping listing {i + 1} due to duplicate description.")
                    continue

                # Skip if price is €0
                if price.replace('\xa0', ' ').strip() == '€ 0,00':
                    print(f"Skipping listing {i + 1} due to price being €0.")
                    continue

                # Add the description to the set of seen descriptions
                seen_descriptions.add(description_snippet)

                link = listing.find_element(By.CSS_SELECTOR, "a.hz-Link.hz-Link--block.hz-Listing-coverLink").get_attribute('href')
                title = listing.find_element(By.CSS_SELECTOR, "h3.hz-Listing-title").text.lower()  # Updated selector

                try:
                    if '8' in title and 'plus' in title and 'iphone' in title:
                        modeltype = 'iPhone 8 Plus'
                    elif 'iphone' in title and '8' in title:
                        modeltype = 'iPhone 8'
                    else:
                        modeltype = None

                except (TimeoutException, NoSuchElementException):
                    modeltype = None

                # Parse the description or title for storage capacity
                if '64' in title or '64' in description_snippet:
                    capacity = '64GB'
                elif '128' in title or '128' in description_snippet:
                    capacity = '128GB'
                elif '256' in title or '256' in description_snippet:
                    capacity = '256GB'
                elif '512' in title or '512' in description_snippet:
                    capacity = '512GB'
                elif '1TB' in title or '1TB' in description_snippet:
                    capacity = '1TB'
                else:
                    capacity = None

                if modeltype:
                    model = f"{modeltype} {capacity}"
                    price = price.replace('\xa0', ' ').strip()
                    listings_data.append({
                        'modeltype': modeltype,
                        'capacity': capacity,
                        'price': price,
                        'description': description_snippet,
                        'link': link
                    })

            except StaleElementReferenceException:
                print(f"StaleElementReferenceException encountered on listing {i + 1}. Retrying...")
                continue  # Skip this listing and try the next one
            except Exception as e:
                print(f"Error processing listing {i + 1}: {e}")

        if not check_next_page():
            print("No further pages or action failed.")
            break

        page_number += 1  # Increment the page number

except Exception as e:
    print(f"An error occurred: {e}")

driver.quit()

# Print all collected listings data
for data in listings_data:
    print(data)

# Define the directory where you want to save the CSV files
output_dir = r'C:\Users\nicop\anaconda3\Scraping\mpscraper\ScrapeFiles'

# Ensure the output directory exists, if not, create it
os.makedirs(output_dir, exist_ok=True)

# Define the CSV file name with the current date
date_str = datetime.now().strftime('%Y-%m-%d')
filename = os.path.join(output_dir, f'iphone_8_{date_str}.csv')

# Open the CSV file for writing
with open(filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Write the header row
    writer.writerow(['Date','Model','Capacity', 'Price', 'Link', 'Description'])

    # Write data rows
    for data in listings_data:
        writer.writerow([date_str, data['modeltype'], data['capacity'], data['price'], data.get('description', 'No Description Provided'), data['link']])

print(f'Data written to CSV file: {filename}')
