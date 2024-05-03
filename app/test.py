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
result = cur.fetchall()
print ('Test 1: Connect to DB')
print (len(result))

with open('games.json', 'w', encoding='utf-8') as f:
  f.write('works')

print(os.path.isfile('games.json'))

print("\nclosing\n")
conn.close()