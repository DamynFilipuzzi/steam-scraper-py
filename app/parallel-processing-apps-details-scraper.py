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
from fp.fp import FreeProxy

RATELIMIT = 1.5
THREADS = 10

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

def getAppDetails(id, appQueue, appsDetails, appsTags, appsScreenshots, oldTags, oldAppsTags, oldAppsScreenshots, oldApps):
  load_dotenv()
  # Create gateway object and initialise in AWS
  gateway = ApiGateway("https://store.steampowered.com/{id}".format(id=id), access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), access_key_secret=os.getenv('AWS_SECRET_ACCESS_KEY'), regions=['us-west-1'])
  gateway.start()
  # Assign gateway to session
  session = requests.Session()
  session.mount("https://store.steampowered.com/{id}".format(id=id), gateway)
  while(appQueue.empty() == False):
    start = time.time()
    appId = appQueue.get()
    response = session.get('https://httpbin.org/ip')
    print('thread: ', id , ' code: ', response.status_code, ' text IP: ', response.text)
    # # Send request (IP will be randomized)
    # response = session.get("https://store.steampowered.com/api/appdetails?appids={app}&cc=CA".format(app=appId))
    # if (response.status_code == 200 and len(response.text) > 0):
    #   print('Thread ID: ', id, ' - Success - AppId: ', appId)
    #   results = json.loads(response.text)
    #   if (results[str(appId)]['success'] == True):
    #     if ("data" in results[str(appId)]):
    #       # Get info in data
    #       hasDetails = True
    #       type = results[str(appId)]['data']['type'] if results[str(appId)]['data']['type'] != None else None
    #       # If app is dlc get the parent app id and if app is in database
    #       if (str(type) == 'dlc'):
    #         if ('fullgame' in results[str(appId)]['data']):
    #           parentApp = int(results[str(appId)]['data']['fullgame']['appid'])
    #           if (parentApp in oldApps):
    #             dlcSteamId = parentApp
    #           else:
    #             # check new apps for parent app
    #             file = open('/appdata/newAppDetails.json', encoding="utf-8")
    #             newAppDetails = json.load(file)
    #             if (parentApp in newAppDetails):
    #               if (newAppDetails[parentApp]['HasDetails'] == True):
    #                 dlcSteamId = parentApp
    #               else:
    #                 dlcSteamId = None
    #             else:
    #               dlcSteamId = None
    #         else:
    #           dlcSteamId = None
    #       else:
    #         dlcSteamId = None
          
    #       isFree = results[str(appId)]['data']['is_free'] if results[str(appId)]['data']['is_free'] != None else None
    #       desc = results[str(appId)]['data']['about_the_game'] if results[str(appId)]['data']['about_the_game'] != None else None
    #       shortDesc = results[str(appId)]['data']['short_description'] if results[str(appId)]['data']['short_description'] != None else None
    #       isMature = False if results[str(appId)]['data']['required_age'] == 0 else True
    #       # Get info in Price_Overview
    #       if ("price_overview" in results[str(appId)]['data']): 
    #         currency = results[str(appId)]['data']['price_overview']['currency'] if results[str(appId)]['data']['price_overview']['currency'] != None else None
    #         originalPrice = results[str(appId)]['data']['price_overview']['initial'] if results[str(appId)]['data']['price_overview']['initial'] != None else None
    #         discountPrice = results[str(appId)]['data']['price_overview']['final'] if results[str(appId)]['data']['price_overview']['final'] != None else None
    #       else:
    #         currency = None
    #         originalPrice = None
    #         discountPrice = None
          
    #       # get AppTags
    #       if ('genres' in results[str(appId)]['data']):
    #         for tag in results[str(appId)]['data']['genres']:
    #           if (tag['description'] in oldTags):
    #             tagId = int(oldTags[tag['description']]['tag_id'])
    #             if (int(appId) in oldAppsTags):
    #               if (int(tagId) not in oldAppsTags[int(appId)]):
    #                 # appTags.setdefault(appId, {})[oldTags[tag['description']]['tag_id']] = tag['description']
    #                 appsTags.put({'AppId': appId, 'TagId': oldTags[tag['description']]['tag_id'], 'TagDesc': tag['description']})
    #             else:
    #               # appTags.setdefault(appId, {})[oldTags[tag['description']]['tag_id']] = tag['description']
    #               appsTags.put({'AppId': appId, 'TagId': oldTags[tag['description']]['tag_id'], 'TagDesc': tag['description']})
          
    #       # get Screenshots
    #       if ("screenshots" in results[str(appId)]['data']):
    #         for image in results[str(appId)]['data']['screenshots']:
    #           if (int(appId) in oldAppsScreenshots):
    #             if (image['id'] in oldAppsScreenshots[int(appId)]):
    #               if (image['path_thumbnail'] not in oldAppsScreenshots[int(appId)][image['id']]['path_thumbnail'] or image['path_full'] not in oldAppsScreenshots[int(appId)][image['id']]['path_full']):
    #                 # either the thumbnail or full_path is different at the current order id. store screenshots
    #                 # appScreenshots.setdefault(appId, {})[image['id']] = ({"path_thumbnail": image['path_thumbnail'], "path_full": image['path_full']})
    #                 appsScreenshots.put({'AppId': appId, 'ImageId': image['id'], 'PathThumbnail': image['path_thumbnail'], 'PathFull': image['path_full']})
    #             else:
    #               # id does not exist in old screenshots. store new id screenshots.
    #               # appScreenshots.setdefault(appId, {})[image['id']] = ({"path_thumbnail": image['path_thumbnail'], "path_full": image['path_full']})
    #               appsScreenshots.put({'AppId': appId, 'ImageId': image['id'], 'PathThumbnail': image['path_thumbnail'], 'PathFull': image['path_full']})
    #           else:
    #             # app does not exist in old screenshots. store new apps screenshots.
    #             # appScreenshots.setdefault(appId, {})[image['id']] = ({"path_thumbnail": image['path_thumbnail'], "path_full": image['path_full']})
    #             appsScreenshots.put({'AppId': appId, 'ImageId': image['id'], 'PathThumbnail': image['path_thumbnail'], 'PathFull': image['path_full']})
          
    #       # Query AppReviews
    #       # Send request for reviews (IP will be randomized)
    #       response = session.get("https://store.steampowered.com/appreviews/{app}?json=1&purchase_type=all&language=english".format(app=appId))
    #       if (response.status_code == 200 and len(response.text) > 0):
    #         reviewsResults = json.loads(response.text)
    #         if (reviewsResults['success'] == 1):
    #           if ("query_summary" in reviewsResults):
    #             if ('total_positive' in reviewsResults['query_summary']):
    #               positiveReviews = reviewsResults['query_summary']['total_positive'] if reviewsResults['query_summary']['total_positive'] != None else None
    #             else:
    #               positiveReviews = None
    #             if ('total_reviews' in reviewsResults['query_summary']):
    #               totalReviews = reviewsResults['query_summary']['total_reviews'] if reviewsResults['query_summary']['total_reviews'] != None else None
    #             else:
    #               totalReviews = None
    #           else:
    #             positiveReviews = None
    #             totalReviews = None
    #         else:
    #           # AppReviews has no details.
    #           positiveReviews = None
    #           totalReviews = None
    #       else:
    #         positiveReviews = None
    #         totalReviews = None

    #       appsDetails.put({"ID": id, 'StatusCode': response.status_code, 'SteamID': appId, 'HasDetails': hasDetails, 'Type': type, "IsMature": isMature, "IsFree": isFree, "Description": desc, "ShortDesc": shortDesc, 'DlcSteamID': dlcSteamId, 'Currency': currency, 'DiscountPrice': discountPrice, 'OriginalPrice': originalPrice, 'PositiveReviews': positiveReviews, 'TotalReviews': totalReviews})
    #     else:
    #       appsDetails.put({"ID": id, 'StatusCode': response.status_code, 'SteamID': appId, 'HasDetails': False, 'Type': None, "IsMature": None, "IsFree": None, "Description": None, "ShortDesc": None, 'DlcSteamID': None, 'Currency': None, 'DiscountPrice': None, 'OriginalPrice': None, 'PositiveReviews': None, 'TotalReviews': None})
    #   else:
    #     appsDetails.put({"ID": id, 'StatusCode': response.status_code, 'SteamID': appId, 'HasDetails': False, 'Type': None, "IsMature": None, "IsFree": None, "Description": None, "ShortDesc": None, 'DlcSteamID': None, 'Currency': None, 'DiscountPrice': None, 'OriginalPrice': None, 'PositiveReviews': None, 'TotalReviews': None})
    # else:
    #   appsDetails.put({"ID": id, 'StatusCode': response.status_code, 'SteamID': appId, 'HasDetails': False, 'Type': None, "IsMature": None, "IsFree": None, "Description": None, "ShortDesc": None, 'DlcSteamID': None, 'Currency': None, 'DiscountPrice': None, 'OriginalPrice': None, 'PositiveReviews': None, 'TotalReviews': None})
    # # Ensure that each request does not exceed the defined rate
    totalTime = time.time() - start
    delay = RATELIMIT - totalTime
    if (delay > 0):
      time.sleep(delay)
  
  # shutdown gateway and return
  gateway.shutdown()
  return

def createThreads(apps):
  oldTags = getTags()
  oldAppsTags = getAppsTags()
  oldAppsScreenshots = getAppsScreenshots()
  oldApps = getOldApps()
  
  with Manager() as manager:
    # store apps in a shared Queue
    appQueue = manager.Queue()
    for app in apps:
      appQueue.put(app)

    print('creating ' , THREADS, ' processes')

    appsDetails = manager.Queue()
    appsTags = manager.Queue()
    appsScreenshots = manager.Queue()
    jobs = []
    for id in range(THREADS):
      process = Process(target=getAppDetails, args=[id, appQueue, appsDetails, appsTags, appsScreenshots, oldTags, oldAppsTags, oldAppsScreenshots, oldApps])
      jobs.append(process)

    # Start the processes
    for j in jobs:
      # Sleep is required for ensuring api gateway does not return error code 429 when trying to create too many gateways in a short burst
      time.sleep(6)
      j.start()

    # Ensure all of the processes have finished
    for j in jobs:
      print(j)
      j.join()
    
    print('Apps Details size: ', appsDetails.qsize(), ' Assert output correct size: ', (appsDetails.qsize() == len(apps)))
    for i in range(appsDetails.qsize()):
      # appDetails[app] = ({"HasDetails": hasDetails ,"Type": type, "IsMature": isMature, "IsFree": isFree, "Description": desc, "ShortDesc": shortDesc, "Currency": currency, "OriginalPrice": originalPrice, "DiscountPrice": discountPrice, "PositiveReviews": positiveReviews, "TotalReviews": totalReviews, "DlcSteamId": dlcSteamId, "UpdatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
      app = appsDetails.get()
      print(app)

    print('Apps Tags size: ', appsTags.qsize())
    print('Apps Screenshots size: ', appsScreenshots.qsize())

    return (appsDetails, appsTags, appsScreenshots)

def getGameDetails():
  # Retrieves new apps from file
  data = getNewApps('appdata/apps.json')
  # Retrieves old apps from db
  oldAppsList = getOldApps()
  # Get new and updated apps 
  (newApps, updatedApps) = getNewAndUpdatedApps(data, oldAppsList)

  # Retrieve New and updated app details 
  # print("Retrieving Info for ", len(newApps), "NEW GAME Apps")
  # (newAppDetails, newAppsTags, newAppsScreenshots) = createThreads(newApps)

  print("Retrieving Info for ", len(updatedApps), "Updated GAME Apps")
  (updatedAppDetails, updatedAppsTags, updatedAppsScreenshots) = createThreads(updatedApps)

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
  # user = 'iqfubfcm'
  # password = 'kpeex49n4fe3'
  # proxy = 'http://38.154.227.167:5868'
  # 'https://user:password@proxyip:port'
  response = requests.get('https://httpbin.org/ip')
  print('Code: ', response.status_code, ' text IP: ', response.text)
  
  response = requests.get('http://httpbin.org/ip', proxies={'http': 'http://iqfubfcm:kpeex49n4fe3@38.154.227.167:5868'})
  print('Code: ', response.status_code, ' text IP: ', response.text)
  # proxy = FreeProxy().get()
  # print(proxy)
  # # getGameDetails()
  # response = requests.request('GET', 'https://httpbin.org/ip', proxies={'http': proxy, 'https': proxy})
  # print('thread: ', id , ' code: ', response.status_code, ' text IP: ', response.text)
  # response = requests.request('GET', 'https://httpbin.org/ip')
  # print('thread: ', id , ' code: ', response.status_code, ' text IP: ', response.text)
  

if __name__ == '__main__':
  main()