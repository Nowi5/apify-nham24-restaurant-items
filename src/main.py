from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import urllib
import time
import re

from apify import Actor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions

# To run this Actor locally, you need to have the Selenium Chromedriver installed.
# https://www.selenium.dev/documentation/webdriver/getting_started/install_drivers/
# When running on the Apify platform, it is already included in the Actor's Docker image.


async def main():
    async with Actor:
        # Read the Actor input
        actor_input = await Actor.get_input() or {}
        urls = actor_input.get('urls')
        location = actor_input.get('location')

        if not urls:
            Actor.log.info('No  URLs specified in actor input, exiting...')
            await Actor.exit()

        # Enqueue the starting URLs in the default request queue
        default_queue = await Actor.open_request_queue()
        for url in urls:
            url = url.get('url')
            Actor.log.info(f'Enqueuing {url} ...')
            await default_queue.add_request({ 'url': url})

        # Get location
        Actor.log.info('Get location for: ' + location)
        place_id = get_place_id(location)

        if place_id:
            lat, lng = get_lat_lng(place_id)
            print("Latitude:", lat)
            print("Longitude:", lng)
        else:
            Actor.log.info('Location coudn\'t be determined.')
            await Actor.exit()

        # Launch a new Selenium Chrome WebDriver
        Actor.log.info('Launching Chrome WebDriver...')
        chrome_options = ChromeOptions()
    #    if Actor.config.headless:
    #        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        driver = webdriver.Chrome(options=chrome_options)

        driver.get('https://nham24.com') 

        # Add the specified cookie
        cookie = {"name": "NEXT_LOCALE", "value": "en"}
        driver.add_cookie(cookie)

        cookie_location = {
            "name": "LOCATION", 
            "value": '{"address":"' + location + '","lat":"' + str(lat) + '","lng":"' + str(lng) + '"}'
        }
        driver.add_cookie(cookie_location)

        # Process the requests in the queue one by one
        while request := await default_queue.fetch_next_request():
            url = request['url']
            Actor.log.info(f'Scraping {url} ...')

            try:
                # Open the URL in the Selenium WebDriver
                driver.get(url)
                title = driver.title

                # wait to load the page
                element_present = EC.presence_of_element_located((By.ID, 'mainSection'))
                WebDriverWait(driver, 10).until(element_present)

                # Scroll to the end of the page
                last_height = driver.execute_script("return document.body.scrollHeight")

                while True:
                    # Scroll to the bottom of the page
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    
                    # Wait to load the page
                    time.sleep(2)  # adjust time as needed
                    
                    # Calculate new scroll height and compare with the previous
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height

                # Get the mainSection element
                main_section = driver.find_element(By.ID, 'mainSection')

                # Find each div with id starting with "section_" inside the mainSection
                section_divs = main_section.find_elements(By.CSS_SELECTOR, 'div[id^="section_"]')

                # Get the count of items and log them
                item_count = len(section_divs)
                Actor.log.info(f'Located {item_count} items.')


                # Loop through and process each div
                for div in section_divs:
                    section_data = extract_section_data(div)
                    await Actor.push_data({ 'url': url, 'title': title, 'item': section_data})               
                
            except:
                Actor.log.exception(f'Cannot extract data from {url}.')
            finally:
                await default_queue.mark_request_as_handled(request)

        driver.quit()

def extract_section_data(section):
    # Extract the background image URL from the inline styles
    background_image_element = section.find_element(By.CSS_SELECTOR, 'div[style*="background-image"]')
    style = background_image_element.get_attribute('style')
    background_image_url = ''
    if 'background-image' in style:
        background_image_url = style.split('url("')[1].split('")')[0]

    # Extract the name of the item
    name_element = section.find_element(By.CSS_SELECTOR, '.textgray-700.text-sm.font-medium')
    name = name_element.text.strip() if name_element else ''

    # Extract the price of the item
    price_element = section.find_element(By.CSS_SELECTOR, '.textgray-700.text-base.font-medium')
    price = price_element.text.strip() if price_element else ''

    return {
        'name': name,
        'price': price,
        'background_image_url': background_image_url
    }

def get_place_id(search_term, url_template="https://v3.nham24.com/api/v1/explore/place/autocomplete?input={}"):
    # Encode the search term for URL
    encoded_search = urllib.parse.quote(search_term)

    # Call the URL with the search term
    url = url_template.format(encoded_search)
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse JSON and extract the first result's place_id
        results = response.json()
        first_result = results[0]
        return first_result['place_id']
    else:
        print("Error:", response.status_code)
        return None

def get_lat_lng(place_id, url_template="https://v3.nham24.com/api/v1/explore/place/details?fields=formatted_address,geometry/location,name,place_id,type&place_id={}"):
    # Call the details URL with the place_id
    url = url_template.format(place_id)
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        details = response.json()
        location = details["geometry"]["location"]
        return location["lat"], location["lng"]
    else:
        print("Error:", response.status_code)
        return None, None