import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from types import SimpleNamespace
from datetime import datetime

# Load .env file
load_dotenv()

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL_PYTHON')

# connect to vercel hosted database
conn = psycopg2.connect(connection_string)
cur = conn.cursor()

# Read data to insert from file
file = open('data/data.json', encoding="utf-8")
data = json.load(file)

# Insert entry into games table if it does not exist. 
for e in data.values():
  steamID = int(e['SteamId'])
  title = str(e['Title'])
  ratingPercentage = None if e['RatingPercent'] == None else int(e['RatingPercent'])
  numOfReviews = None if e['NumOfReviews'] == None else int(e['NumOfReviews'])
  if (e['OriginalPrice'] != None):
    if (e['OriginalPrice'] != "Free"):
      originalPrice = e['OriginalPrice'].replace(',', '')
      originalPrice = originalPrice.replace('.', '')
    else:
      originalPrice = None
  else:
    originalPrice = None
  if (e['DiscountPrice'] != None):
    if (e['DiscountPrice'] != "Free"):
      discountPrice = e['DiscountPrice'].replace(',', '')
      discountPrice = discountPrice.replace('.', '')
    else:
      discountPrice = None
  else:
    discountPrice = None
  
  # Check if game exists in db
  cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Games" WHERE steam_id = %s)''', (steamID,))
  result = cur.fetchone()[0]
  # if game does not exist then insert, otherwise TODO update price if it differs from prev
  if (result is False):
    print('Inserting game. Steam ID: %s', steamID)
    cur.execute("""
      INSERT INTO "Games" (steam_id, title, rating_percentage, number_of_reviews, original_price, discount_price)
      VALUES (%s, %s, %s, %s, %s, %s)
      """, (steamID, title, ratingPercentage, numOfReviews, originalPrice, discountPrice))
  else:
    print("Record Exists")

print("\nclosing\n")
conn.commit()
conn.close()