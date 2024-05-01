import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from tqdm import tqdm

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

gamePrices = dict()
# Insert entry into games table if it does not exist.
for e in tqdm(data, desc="Extracting prices from games..."):
  steamID = e
  if (data[e]['OriginalPrice'] != None):
    if (data[e]['OriginalPrice'] != "Free"):
      originalPrice = data[e]['OriginalPrice'].replace(',', '')
      originalPrice = originalPrice.replace('.', '')
    else:
      originalPrice = 0
  else:
    originalPrice = None
  if (data[e]['DiscountPrice'] != None):
    if (data[e]['DiscountPrice'] != "Free"):
      discountPrice = data[e]['DiscountPrice'].replace(',', '')
      discountPrice = discountPrice.replace('.', '')
    else:
      discountPrice = 0
  else:
    discountPrice = None
  
  # Check if game exists in db
  cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Games" WHERE steam_id = %s)''', (steamID,))
  gameExists = cur.fetchone()[0]
  # Check if Price exists in db
  cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Price" WHERE steam_id = %s)''', (steamID,))
  priceExists = cur.fetchone()[0]
  if (gameExists is not False):
    if (priceExists is False):
      cur.execute('''INSERT INTO "Price" (steam_id, original_price, discount_price, valid_to) VALUES (%s, %s, %s, %s)''', (steamID, originalPrice, discountPrice, '9999-12-31'))
    else:
      print("Game Price exist. Doing nothing")
  else:
    print("Game Does not exist in DB")

print("\nclosing\n")
conn.commit()
conn.close()