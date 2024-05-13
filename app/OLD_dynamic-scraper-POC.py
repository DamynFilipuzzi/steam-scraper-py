import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
from tqdm import tqdm

rate = 2

# Run google chrome in headless mode (no browser popup)
options = Options()
options.add_argument("start-maximized")
options.add_argument("enable-automation")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-browser-side-navigation")
options.add_argument("--disable-gpu")

# Set up the Chrome WebDriver
driver = webdriver.Chrome(options=options)

# Navigate to Google Search
# driver.get("https://store.steampowered.com/search/?category1=998&supportedlang=english&hidef2p=1&ndl=1&ignore_preferences=1")
driver.get("https://store.steampowered.com/search/?ignore_preferences=1&category1=998%2C21%2C990%2C996&ndl=1")
# Define the number of times to scroll
scroll_count = 10000

# Simulate continuous scrolling using JavaScript
for _ in tqdm(range(scroll_count), desc="Scrolling..."):
  start = time.time()
  print('loading page: %s', _)
  driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
  totalTime = time.time() - start
  delay = rate - totalTime
  if (delay > 0):
    time.sleep(delay)

# Get the page source after scrolling
page_source = driver.page_source

# Parse the page source with BeautifulSoup
soup = BeautifulSoup(page_source, "html.parser")

# Extract and print search results
search_results = soup.find_all(class_="search_result_row")
games = dict()
for result in tqdm(search_results, desc="Loading to memory..."):
  title = result.find(class_ = "title")
  title = title.text.strip()
  # Check if entry is a package of games. If a package then store package ID rather than enum ID's
  # TODO REDESIGN DB TO HANDLE BUNDLES also side not url change from /app/ to /sub/
  # Uses /sub/ data-ds-packageid="401587"
  # NOTE CURRENTLY NOT PULLING BUNDLE GAMES: WOULD NEED TO USE THIS URL IF GOING TO DO THAT: https://store.steampowered.com/search/?ignore_preferences=1&category1=998%2C996&supportedlang=english&hidef2p=1&ndl=1 
  # OR
  # TODO USES /bundle/ data-ds-bundleid="18052"

  if (result.get("data-ds-packageid") is not None):
    id = result.get("data-ds-packageid")
    # For now Skip if package. TODO store in bundles db
    pass
  else:
    id = result.get("data-ds-appid")

    price = result.find(class_ = 'discount_original_price')
    if (price != None):
      price = price.text.strip()
      price = price.split(' ')
      if (len(price) > 1):
        price = price[1]
      else:
        price = price[0]
    else:
      price = None

    discPrice = result.find(class_ = "discount_final_price")
    if (discPrice != None):
      discPrice = discPrice.text.strip()
      discPrice = discPrice.split(' ')
      if (len(discPrice) > 1):
        discPrice = discPrice[1]
      else:
        discPrice = discPrice[0]
    else:
      discPrice = None

    games[id] = ({"Title": title, "OriginalPrice": price, "DiscountPrice": discPrice})

# Close the WebDriver
driver.quit()

with open('/appdata/data.json', 'w', encoding='utf-8') as f:
# with open('appdata/data.json', 'w', encoding='utf-8') as f:
  json.dump(games, f, ensure_ascii=False, indent=4)

print(len(games))