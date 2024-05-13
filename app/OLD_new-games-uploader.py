import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from tqdm import tqdm
from datetime import datetime

TABLE_NAME = 'Games'

# Load .env file
load_dotenv()

# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL_PYTHON')

# connect to database
conn = psycopg2.connect(connection_string)
cur = conn.cursor()
cur.execute('SELECT "steam_id" FROM "Games"')
# Get all currently stored games in db for comparison
# pyscopg2 return default on fetch all.
# credit to https://stackoverflow.com/a/51285087 for solution
allIds = [r[0] for r in cur.fetchall()]
print(len(allIds))

# Read data to insert from file
# file = open('/appdata/data.json', encoding="utf-8")
file = open('appdata/data.json', encoding="utf-8")
data = json.load(file)
print(len(data))

games = []
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
  
  # # Check if game exists in db
  # cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Games" WHERE steam_id = %s)''', (steamID,))
  # resultGame = cur.fetchone()[0]
  # if(resultGame):
  #   c +=1
  
  if ((int(steamID) not in allIds) == True):
    games.append((steamID, title, originalPrice, discountPrice))
    # 10351

  # cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Price" WHERE steam_id = %s AND valid_to = %s)''', (steamID, '9999-12-31'))
  # resultPrice = cur.fetchone()[0]
  # # ogPrice = int(price[2]) if price[2] else None
  # # dprice = int(price[3]) if price[3] else None
  # originalPrice = int(originalPrice) if originalPrice else None
  # discountPrice = int(discountPrice) if discountPrice else None
  
  # # Check if game exists in db
  # cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Games" WHERE steam_id = %s)''', (steamID,))
  # resultGame = cur.fetchone()[0]
  # # if game does not exist then insert, otherwise update price if it differs from prev
  # if (resultGame is False):
  #   # Insert into games table
  #   cur.execute("""
  #     INSERT INTO "Games" (steam_id, title, original_price, discount_price)
  #     VALUES (%s, %s, %s, %s)
  #     """, (steamID, title, originalPrice, discountPrice))
  #   # Insert into Price Table
  #   cur.execute("""INSERT INTO "Price" (steam_id, original_price, discount_price, valid_to) VALUES (%s, %s, %s, %s)""", (steamID, originalPrice, discountPrice, '9999-12-31'))
  # else:
  #   # Retrieve price data
  #   cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Price" WHERE steam_id = %s AND valid_to = %s)''', (steamID, '9999-12-31'))
  #   resultPrice = cur.fetchone()[0]
  #   if (resultPrice is not False):
  #     # check if there is a difference in original_price or discount price and insert new price entry if it does differ
  #     cur.execute('''SELECT * FROM "Price" WHERE steam_id = %s AND valid_to = %s''', (steamID, '9999-12-31'))
  #     price = cur.fetchone()
  #     if (price[2] != originalPrice | price[3] != discountPrice):
  #       print("Updating old record and creating new price data")
  #       # Update old price 'valid_to' to be now(). Then Insert new price with valid_to = '9999-12-31'
  #       cur.execute("""UPDATE "Price" SET valid_to = %s WHERE id = %s""", (datetime.now(), price[0]))
  #       cur.execute("""INSERT INTO "Price" (steam_id, original_price, discount_price, valid_to) VALUES (%s, %s, %s, %s)""", (steamID, originalPrice, discountPrice, '9999-12-31'))
  #   else:
  #     print('something went wrong...')

# print(games)
print(len(games))
psycopg2.extras.execute_batch(cur, """INSERT INTO "Games" (steam_id, title, original_price, discount_price) VALUES (%s, %s, %s, %s)""",
                                      games)
conn.commit()

print("\nclosing\n")
conn.close()