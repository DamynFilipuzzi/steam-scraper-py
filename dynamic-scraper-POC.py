import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import json

# Run google chrome in headless mode (no browser popup)
options = Options()
options.add_argument('--headless')

# Set up the Chrome WebDriver
driver = webdriver.Chrome(options=options)

# Navigate to Google Search
driver.get("https://store.steampowered.com/search/?category1=998&supportedlang=english&hidef2p=1&ndl=1&ignore_preferences=1")
# Define the number of times to scroll
scroll_count = 5000

# Simulate continuous scrolling using JavaScript
for _ in range(scroll_count):
  driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
  time.sleep(2)  # Wait for the new results to load

# Get the page source after scrolling
page_source = driver.page_source

# Parse the page source with BeautifulSoup
soup = BeautifulSoup(page_source, "html.parser")

# Extract and print search results
search_results = soup.find_all(class_="search_result_row")
games = dict()
counter = 0
for result in search_results:
  title = result.find(class_ = "title")
  title = title.text.strip()
  # Check if entry is a package of games. If a package then store package ID rather than enum ID's
  # TODO REDESIGN DB TO HANDLE BUNDLES also side not url change from /app/ to /sub/
  # Uses /sub/ data-ds-packageid="401587"
  # NOTE CURRENTLY NOT PULLING BUNDLE GAMES: WOULD NEED TO USE THIS URL IF GOING TO DO THAT: https://store.steampowered.com/search/?ignore_preferences=1&category1=998%2C996&supportedlang=english&hidef2p=1&ndl=1 
  # OR
  # USES /bundle/ data-ds-bundleid="18052"

  if (result.get("data-ds-packageid") is not None):
    id = result.get("data-ds-packageid")
  else:
    id = result.get("data-ds-appid")

  rating = result.find(class_ = "search_review_summary")
  ratingStringBreakdown = str(rating)
  ratingStringBreakdown = re.findall(r'\d+',ratingStringBreakdown)
  
  if (len(ratingStringBreakdown) != 0):
    ratingStr = ratingStringBreakdown[0]
    # remove first element in list (removes rating percentage)
    ratingStringBreakdown.remove(ratingStringBreakdown[0])
    index = 0
    numOfReviews = ''
    for e in ratingStringBreakdown:
      numOfReviews += ratingStringBreakdown[index]
      index += 1
  else:
    ratingStr = None
    numOfReviews = None

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
  
  games[counter] = ({"Title": title, "SteamId": id, "RatingPercent": ratingStr, "NumOfReviews": numOfReviews, "OriginalPrice": price, "DiscountPrice": discPrice})
  counter += 1

# Close the WebDriver
driver.quit()
# print(games)
# print(data)
with open('data/data.json', 'w', encoding='utf-8') as f:
  json.dump(games, f, ensure_ascii=False, indent=4)

print(len(games))