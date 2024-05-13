import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from tqdm import tqdm
from datetime import datetime

# Load .env file
load_dotenv()

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL_PYTHON')

# connect to vercel hosted database
conn = psycopg2.connect(connection_string)
cur = conn.cursor()

# Read data to insert from file
# file = open('/appdata/games.json', encoding="utf-8")
file = open('appdata/data.json', encoding="utf-8")
data = json.load(file)

# Insert entry into games table if it does not exist. 
for e in tqdm(data, desc="Inserting Records..."):
  steamID = e
  title = str(data[e]['Title'])
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
  resultGame = cur.fetchone()[0]
  # if game does not exist then insert, otherwise update price if it differs from prev
  if (resultGame is False):
    # Insert into games table
    cur.execute("""
      INSERT INTO "Games" (steam_id, title, original_price, discount_price)
      VALUES (%s, %s, %s, %s)
      """, (steamID, title, originalPrice, discountPrice))
    # Insert into Price Table
    cur.execute("""INSERT INTO "Price" (steam_id, original_price, discount_price, valid_to) VALUES (%s, %s, %s, %s)""", (steamID, originalPrice, discountPrice, '9999-12-31'))
  else:
    # Retrieve price data
    cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Price" WHERE steam_id = %s AND valid_to = %s)''', (steamID, '9999-12-31'))
    resultPrice = cur.fetchone()[0]
    if (resultPrice is not False):
      # check if there is a difference in original_price or discount price and insert new price entry if it does differ
      cur.execute('''SELECT * FROM "Price" WHERE steam_id = %s AND valid_to = %s''', (steamID, '9999-12-31'))
      price = cur.fetchone()
      ogPrice = int(price[2]) if price[2] else None
      dprice = int(price[3]) if price[3] else None
      originalPrice = int(originalPrice) if originalPrice else None
      discountPrice = int(discountPrice) if discountPrice else None
      if (ogPrice != originalPrice or dprice != discountPrice):
        print("Updating old record and creating new price data")
        print("Old Orig Price: ",originalPrice, " New Orig Price: ", ogPrice)
        print("Old disc Price: ",discountPrice, " New disc Price: ", dprice)
        # Update old price 'valid_to' to be now(). Then Insert new price with valid_to = '9999-12-31'
        cur.execute("""UPDATE "Price" SET valid_to = %s WHERE id = %s""", (datetime.now(), price[0]))
        cur.execute("""INSERT INTO "Price" (steam_id, original_price, discount_price, valid_to) VALUES (%s, %s, %s, %s)""", (steamID, originalPrice, discountPrice, '9999-12-31'))
      else:
        print('No Change do nothing')
    else:
      print('something went wrong...')

print("\nclosing\n")
conn.commit()
conn.close()