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
# connect to database
conn = psycopg2.connect(connection_string)
cur = conn.cursor()
cur.execute('''SELECT * FROM "Games"''')
results = cur.fetchall()
print ('Test 1: Connect to DB')
print (len(results))

games = dict()
for game in results:
  steamId = game[1]
  title = game[2]
  oPrice = game[3]
  dPrice = game[4]
  games[steamId] = ({"Title": title, "OriginalPrice": oPrice, "DiscountPrice": dPrice})

with open('/appdata/games.json', 'w', encoding='utf-8') as f:
  json.dump(games, f, ensure_ascii=False, indent=4)

print(os.path.isfile('/appdata/games.json'))
print(len(games))

print("\nclosing\n")
conn.close()