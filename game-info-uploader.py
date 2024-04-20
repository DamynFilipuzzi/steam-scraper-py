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
file = open('data/descriptions.json', encoding="utf-8")
data = json.load(file)

# Insert entry into games table if it does not exist. 
for e in tqdm(data, desc="Inserting Records..."):
  steamID = e

  if (data[e]['Description'] != None):
    desc = str(data[e]['Description'])
  else:
    desc = None
  
  if (data[e]['IsMature'] != None):
    isMature = bool(data[e]['IsMature'])
  else:
    isMature = None

  if (data[e]['TotalReviews'] != None):
    totalReviews = int(data[e]['TotalReviews'])
  else:
    totalReviews = None
  
  if (data[e]["TotalPositiveReviews"] != None):
    totalPositiveReviews = int(data[e]["TotalPositiveReviews"])
  else:
    totalPositiveReviews = None
  

  
  # Check if game exists in db
  cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Game_Info" WHERE steam_id = %s)''', (steamID,))
  result = cur.fetchone()[0]
  # if game_info does not exist then insert
  if (result is False):
    print('Inserting game. Steam ID: %s', steamID)
    cur.execute("""
      INSERT INTO "Game_Info" (steam_id, desc, is_mature, total_reviews, total_positive_reviews)
      VALUES (%s, %s, %s, %s, %s)
      """, (steamID, desc, isMature, totalReviews, totalPositiveReviews))
  else:
    print("Record Exists")

print("\nclosing\n")
conn.commit()
conn.close()