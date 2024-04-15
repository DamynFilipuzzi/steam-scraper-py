import requests
from bs4 import BeautifulSoup
import re

URL = "https://store.steampowered.com/search/"
page = requests.get(URL)

soup = BeautifulSoup(page.content, "html.parser")

results = soup.find_all(class_="search_result_row")

data = []
for result in results:
  title = result.find(class_ = "title")
  title = title.text.strip()
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
    ratingStr = 'NULL'
    numOfReviews = 'NULL'

  price = result.find(class_ = 'discount_original_price')
  if (price != None):
    price = price.text.strip()
    price = price.split(' ')
    if (len(price) > 1):
      price = price[1]
    else:
      price = price[0]
  else:
    price = 'NULL'

  discPrice = result.find(class_ = "discount_final_price")
  if (discPrice != None):
    discPrice = discPrice.text.strip()
    discPrice = discPrice.split(' ')
    if (len(discPrice) > 1):
      discPrice = discPrice[1]
    else:
      discPrice = discPrice[0]
  else:
    discPrice = 'NULL'
  
  release_date = result.find(class_ = "search_released")
  release_date = release_date.text.strip()
  if (len(release_date) == 0):
    release_date = 'NULL'
  
  data += [[title, ratingStr, numOfReviews, price, discPrice, release_date]]

print(data)