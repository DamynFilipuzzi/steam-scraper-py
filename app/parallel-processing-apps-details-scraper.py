from multiprocessing import Process, Manager 
import os
from dotenv import load_dotenv
import requests
import json
from fp.fp import FreeProxy
import time
import psycopg2
import psycopg2.extras
from requests_ip_rotator import ApiGateway

RATE = 1.5

def getTags():
  # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * FROM "Tags"')
  tagsOld = cur.fetchall()
  oldTagsList = dict()
  for tag in tagsOld:
    oldTagsList[tag[2]] = ({"id:": tag[0], "tag_id": tag[1], "tag_name": tag[2]})
  cur.close()
  
  return oldTagsList

def getAppsTags():
  # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * FROM "Apps_Tags"')
  appsTagsOld = cur.fetchall()
  cur.close()
  oldAppsTagsList = dict()
  for tag in appsTagsOld:
    oldAppsTagsList.setdefault(tag[0], {})[tag[1]] = 0
  
  return oldAppsTagsList

def getAppsScreenshots():
  # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * FROM "Screenshots"')
  appsScreenshotsOld = cur.fetchall()
  cur.close()
  oldAppsScreenshotsList = dict()
  for screenshot in appsScreenshotsOld:
    oldAppsScreenshotsList.setdefault(screenshot[1], {})[screenshot[2]] = ({"path_thumbnail": screenshot[3], "path_full": screenshot[4]})
  
  return oldAppsScreenshotsList

def getNewApps(path):
  # Read data to insert from file
  file = open(path, encoding="utf-8")
  data = json.load(file)

  return data

def getOldApps():
  # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * FROM "Apps"')
  appsOld = cur.fetchall()
  oldAppsList = dict()
  for app in appsOld:
    oldAppsList[app[1]] = ({"id:": app[0], "title": app[2], "type": app[3], "last_modified": app[4], "price_change_number": app[5], "updated_at": app[6], "created_at": app[7], "total_positive_reviews": app[8], "total_reviews": app[9], "dlc_steam_id": app[10]})
  cur.close()

  return oldAppsList

def getNewAndUpdatedApps(data, oldAppsList):
  # Return a list of apps that are new or have changed
  newApps = dict()
  updatedApps = dict()
  for app in data:
    if (int(app) not in oldAppsList):
      newApps[app] = ({"title": data[app]['title'], "last_modified": data[app]['last_modified'], "price_change_number": data[app]['price_change_number']})
    elif (data[app]['title'] != oldAppsList[int(app)]['title'] or data[app]['last_modified'] != oldAppsList[int(app)]['last_modified'] or data[app]['price_change_number'] != oldAppsList[int(app)]['price_change_number']):
      updatedApps[app] = ({"title": data[app]['title'], "last_modified": data[app]['last_modified'], "price_change_number": data[app]['price_change_number']})

  return (newApps, updatedApps)

def getAppDetails(id, queue, resultsQueue):
  load_dotenv()
  c = 0
  # Create gateway object and initialise in AWS
  gateway = ApiGateway("https://store.steampowered.com/{id}".format(id=id), access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), access_key_secret=os.getenv('AWS_SECRET_ACCESS_KEY'), regions=['us-west-1'])
  gateway.start()
  # Assign gateway to session
  session = requests.Session()
  session.mount("https://store.steampowered.com/{id}".format(id=id), gateway)
  # for i in range(50):
  while(queue.empty() == False):
    start = time.time()
    # Send request (IP will be randomized)
    # response = session.get("https://store.steampowered.com/api/appdetails?appids=%s&cc=CA", queue.get())
    response = session.get(queue.get())
    c += 1
    if (response.status_code != 200):
      print('####')
      print('ID: ', id, " - BIG FAIL")
      print(response.status_code)
      print('####')
    else:
      print('ID: ', id, ' - Success', ' - Count: ', c )
      results = json.loads(response.text)
      if (results[str(730)]['success'] == True and "data" in results[str(730)]):
        type = results[str(730)]['data']['type'] if results[str(730)]['data']['type'] != None else None
        resultsQueue.put({"ID": id, 'StatusCode': response.status_code, 'Type': type})
    # Ensure that each request does not exceed the defined rate
    totalTime = time.time() - start
    delay = RATE - totalTime
    if (delay > 0):
      time.sleep(delay)
  
  gateway.shutdown()
  return c

def createList():
  print()

def createThreads():
  with Manager() as manager:
    urlQueue = manager.Queue()
    for i in range(5000):
      urlQueue.put("https://store.steampowered.com/api/appdetails?appids=730&cc=CA")
    threads = 10
    print('creating ' , threads, ' processes')

    resultsQueue = manager.Queue()
    jobs = []
    for id in range(threads):
      process = Process(target=getAppDetails, args=[id, urlQueue, resultsQueue])
      jobs.append(process)
    # Start the processes
    for j in jobs:
      time.sleep(6)
      j.start()

    # Ensure all of the processes have finished
    for j in jobs:
      print(j)
      j.join()
    
    print('Results size: ',   resultsQueue.qsize())

# def getGameDetails():
#   # Retrieves all old tags from db
#   oldTags = getTags()
#   # Retrieves all old Apps_tags from db
#   oldAppsTags = getAppsTags()
#   # Retrieves new apps from file
#   data = getNewApps('appdata/apps.json')
#   # Retrieves old apps from db
#   oldAppsList = getOldApps()
#   # Get new and updated apps 
#   (newApps, updatedApps) = getNewAndUpdatedApps(data, oldAppsList)

#   # Retrieve New and updated app details 
#   print("Retrieving Info for ", len(newApps), "NEW GAME Apps")
#   (newAppDetails, newAppsTags, newAppsScreenshots) = createThreads(newApps, oldTags, oldAppsTags)

#   print("Retrieving Info for ", len(updatedApps), "Updated GAME Apps")
#   (updatedAppDetails, updatedAppsTags, updatedAppsScreenshots) = createThreads(updatedApps, oldTags, oldAppsTags)

  # Write data to files
  # with open('/appdata/newAppDetails.json', 'w', encoding='utf-8') as f:
  #   json.dump(newAppDetails, f, ensure_ascii=False, indent=4)
  # with open('/appdata/updatedAppDetails.json', 'w', encoding='utf-8') as f:
  #   json.dump(updatedAppDetails, f, ensure_ascii=False, indent=4)
  # with open('/appdata/newAppsTags.json', 'w', encoding='utf-8') as f:
  #   json.dump(newAppsTags, f, ensure_ascii=False, indent=4)
  # with open('/appdata/updatedAppsTags.json', 'w', encoding='utf-8') as f:
  #   json.dump(updatedAppsTags, f, ensure_ascii=False, indent=4)
  # with open('/appdata/newAppsScreenshots.json', 'w', encoding='utf-8') as f:
  #   json.dump(newAppsScreenshots, f, ensure_ascii=False, indent=4)
  # with open('/appdata/updatedAppsScreenshots.json', 'w', encoding='utf-8') as f:
  #   json.dump(updatedAppsScreenshots, f, ensure_ascii=False, indent=4)

def main():
  # getGameDetails()
  createThreads()

if __name__ == '__main__':
  main()