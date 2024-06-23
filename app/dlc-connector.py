import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from tqdm import tqdm
from datetime import datetime
import time
import requests

# Store Updated Apps
def storeUpdatedApps(updatedAppsList):
  dlcList = []
  for steamId in updatedAppsList:
    dlc_steam_id = updatedAppsList[steamId]['DlcSteamId']

    dlcList.append((dlc_steam_id, steamId))

  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """UPDATE "Apps" SET dlc_steam_id=%s WHERE steam_id=%s""", dlcList)
    conn.commit()
    print("Storing: {dlcList} updated apps.".format(dlcList=len(dlcList)))
  except Exception as error:
    print("Failed to store Updated App")
    print(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

def getOldApps():
  # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute("""SELECT * FROM "Apps" WHERE "type"='dlc' AND "dlc_steam_id" IS NULL;""")
  appsOld = cur.fetchall()
  oldAppsList = dict()
  for app in appsOld:
    oldAppsList[app[1]] = ({"id:": app[0], "title": app[2], "type": app[3], "last_modified": app[4], "price_change_number": app[5], "updated_at": app[6], "created_at": app[7], "total_positive_reviews": app[8], "total_reviews": app[9], "dlc_steam_id": app[10]})
  cur.close()

  return oldAppsList


# 1. get dlc with no parent app
dlc = getOldApps()
print(len(dlc))
rate = 1.5
dlcDict = dict()
for app in tqdm(dlc, desc="scraping DLC"):
  start = time.time()
  url = "https://store.steampowered.com/api/appdetails?appids={app}&cc=CA".format(app=app)
  response = requests.request("GET", url)
  # Check that status code is of type success
  if (response.status_code == 200 and len(response.text) > 0):
    results = json.loads(response.text)
    if (results[str(app)]['success'] == True):
      # Check that app has data.
      if ("data" in results[str(app)]):
        # Get info in data
        type = results[str(app)]['data']['type'] if results[str(app)]['data']['type'] != None else None
        # If app is dlc get the parent app id
        if (str(type) == 'dlc' and 'fullgame' in results[str(app)]['data']):
          dlcSteamId = int(results[str(app)]['data']['fullgame']['appid'])
        else:
          dlcSteamId = None
        
  # Ensure that each request does not exceed the defined rate
  totalTime = time.time() - start
  delay = rate - totalTime
  if (delay > 0):
    time.sleep(delay)
    
  dlcDict[app] = ({"DlcSteamId": dlcSteamId})

# 2. Store apps to temp file
with open('appdata/TempDlcTuple.json', 'w', encoding='utf-8') as f:
  json.dump(dlcDict, f, ensure_ascii=False, indent=4)

# 3. Upload updated dlc
storeUpdatedApps(dlcDict)