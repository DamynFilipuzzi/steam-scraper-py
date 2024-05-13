import requests
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os
import psycopg2
import psycopg2.extras

headers = {
  'Cookie': 'browserid=3561858445947467491; steamCountry:CA%7Cb3495110b69ce3b66ffa45eaed107e4b='
}
rate = 1.5

# Read data to insert from file
# file = open('/appdata/data.json', encoding="utf-8")
file = open('appdata/data.json', encoding="utf-8")
data = json.load(file)

print(len(data))

# Load .env file
load_dotenv()
# Get the connection string from the environment variable
connection_string = os.getenv('DATABASE_URL_PYTHON')
# connect to database
conn = psycopg2.connect(connection_string)
cur = conn.cursor()

games = dict()
for game in tqdm(data, desc="Inserting Records..."):
  # Check if game info exists in db and if game_info exists
  # TODO: Implement check that revalidates data based on a last updated field
  cur.execute('''SELECT EXISTS ( SELECT 1 FROM "Game_Info" WHERE steam_id = %s)''', (game,))
  gameInfoExists = cur.fetchone()[0]
  if (gameInfoExists is  not False):
    start = time.time()
    # get new URL
    url = "https://store.steampowered.com/api/appdetails?appids=" + str(game)
    response = requests.request("GET", url, headers=headers)
    response.encoding = 'utf-8-sig'
    results = json.loads(response.text)
    # TODO if results are null (usually an 429 error: Too many requests) pause and retry in x amount of time
    if (results[str(game)]['success'] == True):
      type = results[str(game)]['data']['type']
      if (results[str(game)]['data']['about_the_game'] != None):
        desc = results[str(game)]['data']['about_the_game']
      else:
        desc = None
      if (results[str(game)]['data']['required_age'] == 0):
        mature = False
      else:
        mature = True
      # Get Reviews
      reviewsUrl = 'https://store.steampowered.com/appreviews/' + str(game) + '?json=1'
      reviewsResponse = requests.request("GET", reviewsUrl, headers=headers)
      reviewsResponse.encoding = 'utf-8-sig'
      reviewsResults = json.loads(reviewsResponse.text)
      if (reviewsResults['success'] == True):
        totalReviews = reviewsResults['query_summary']['total_reviews']
        positiveReviews = reviewsResults['query_summary']['total_positive']
      else:
        totalReviews = None
        positiveReviews = None
    else:
      desc = None
      type = None

    games[game] = ({"Description": desc, "IsMature": mature, "TotalReviews": totalReviews, "TotalPositiveReviews": positiveReviews})
    totalTime = time.time() - start
    delay = rate - totalTime
    if (delay > 0):
      print(delay)
      time.sleep(delay)
  else:
    print('Info already exists... skipping')


print(len(games))
# with open('/appdata/info.json', 'w', encoding='utf-8') as f:
with open('appdata/info.json', 'w', encoding='utf-8') as f:
  json.dump(games, f, ensure_ascii=False, indent=4)