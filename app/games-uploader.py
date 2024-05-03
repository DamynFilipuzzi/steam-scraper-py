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
  result = cur.fetchone()[0]
  # if game does not exist then insert, otherwise update price if it differs from prev
  if (result is False):
    print('Inserting game. Steam ID: %s', steamID)
    cur.execute("""
      INSERT INTO "Games" (steam_id, title, original_price, discount_price)
      VALUES (%s, %s, %s, %s)
      """, (steamID, title, originalPrice, discountPrice))
  else:
    # TODO update price if it differs from prev
    print("Record Exists")

print("\nclosing\n")
conn.commit()
conn.close()