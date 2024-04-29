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
file = open('data/tags.json', encoding="utf-8")
data = json.load(file)

# Insert entry into games table if it does not exist.
for e in tqdm(data, desc="Inserting Records..."):
  steamID = e
  for tag in data[e]:
    # Check if game and game_tags already Exist in db and
    cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Games" WHERE steam_id = %s)''', (steamID,))
    gameExists = cur.fetchone()[0]
    cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Game_Tags" WHERE steam_id = %s AND tag = %s)''', (steamID, tag))
    gameTagsExists = cur.fetchone()[0]
    if (gameExists is not False):
      if (gameTagsExists is False):
        cur.execute('''INSERT INTO "Game_Tags" (steam_id, tag) VALUES (%s, %s)''', (steamID, tag))
      else:
        print("Game Tag exist. Doing nothing")
    else:
      print("Game Does not exist in DB")


print("\nclosing\n")
conn.commit()
conn.close()