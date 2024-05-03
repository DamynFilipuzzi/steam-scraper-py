import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from tqdm import tqdm

print("Test2: read games File")

# Read data to insert from file
if (os.path.isfile('games.json')):
  file = open('games.json', encoding="utf-8")
  data = json.load(file)
  
  # Insert entry into games table if it does not exist. 
  for e in tqdm(data, desc="Inserting Records..."):
    print(e, data[e]['Title'], data[e]['OriginalPrice'], data[e]['DiscountPrice'])
  
else:
  print('failed to find games.json')
print("\nclosing\n")