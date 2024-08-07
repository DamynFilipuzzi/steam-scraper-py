import os
import sys
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import requests
import json
from tqdm import tqdm
import time
from datetime import datetime
# Add the appropriate paths depending on the environment
if os.environ.get('DOCKERIZED'):
    from lib.utils import Utils
else:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app.lib.utils import Utils


# Rate at which each request can be made. 
RATE = 1.5

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

def getAppsVideos():
  # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * FROM "Videos"')
  appsVideosOld = cur.fetchall()
  cur.close()
  oldAppsVideosList = dict()
  for video in appsVideosOld:
    oldAppsVideosList.setdefault(video[1], {})[video[2]] = ({"video_name": video[3]})
  
  return oldAppsVideosList

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

def getOldDevelopers():
  # Get all Developers from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute("""SELECT "Developers".id, "Apps_Developers".steam_id, "Developers".developer_name FROM public."Developers" LEFT JOIN public."Apps_Developers" ON "Developers".id = "Apps_Developers".developer_id""")
  devsOld = cur.fetchall()
  oldDevsList = dict()
  for app in devsOld:
    # oldDevsList[app[1]] = ({"developer_id": app[0], "developer_name": app[2]})
    oldDevsList.setdefault(app[1], {})[app[2]] = ({"developer_id": app[0]})
  cur.close()

  return oldDevsList

def getOldPublishers():
  # Get all Publishers from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute("""SELECT "Publishers".id, "Apps_Publishers".steam_id, "Publishers".Publisher_name FROM public."Publishers" LEFT JOIN public."Apps_Publishers" ON "Publishers".id = "Apps_Publishers".Publisher_id""")
  pubsOld = cur.fetchall()
  oldPubsList = dict()
  for app in pubsOld:
    # oldPubsList[app[1]] = ({"Publisher_id": app[0], "Publisher_name": app[2]})
    oldPubsList.setdefault(app[1], {})[app[2]] = ({"publisher_id": app[0]})
  cur.close()

  return oldPubsList

def getDetails(appData, oldTags, oldAppsTags):
  if (appData != None):
    # Get old data for comparison.
    oldAppsScreenshots = getAppsScreenshots()
    oldApps = getOldApps()
    oldAppsVideos = getAppsVideos()
    oldAppsDevelopers = getOldDevelopers()
    oldAppsPublishers = getOldPublishers()

    # TODO: Condense these into one.
    appScreenshots = dict()
    appVideos = dict()
    appTags = dict()
    appDetails = dict()
    appDevelopers = dict()
    appPublishers = dict()

    for app in tqdm(appData, desc="Retrieving App Details..."):
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
            hasDetails = True
            type = results[str(app)]['data']['type'] if results[str(app)]['data']['type'] != None else None

            # If app is dlc get the parent app id and if app is in database
            if (str(type) == 'dlc'):
              if ('fullgame' in results[str(app)]['data']):
                parentApp = int(results[str(app)]['data']['fullgame']['appid'])
                if (parentApp in oldApps):
                  dlcSteamId = parentApp
                else:
                  # check new apps for parent app
                  relative_path = os.path.join('../appdata', 'newAppDetails.json')
                  file = open(relative_path, encoding="utf-8")
                  newAppDetails = json.load(file)
                  if (parentApp in newAppDetails):
                    if (newAppDetails[parentApp]['HasDetails'] == True):
                      dlcSteamId = parentApp
                    else:
                      dlcSteamId = None
                  else:
                    dlcSteamId = None
              else:
                dlcSteamId = None
            else:
              dlcSteamId = None

            isFree = results[str(app)]['data']['is_free'] if results[str(app)]['data']['is_free'] != None else None
            desc = results[str(app)]['data']['about_the_game'] if results[str(app)]['data']['about_the_game'] != None else None
            shortDesc = results[str(app)]['data']['short_description'] if results[str(app)]['data']['short_description'] != None else None
            isMature = False if results[str(app)]['data']['required_age'] == 0 else True
            # Get info in Price_Overview
            if ("price_overview" in results[str(app)]['data']): 
              currency = results[str(app)]['data']['price_overview']['currency'] if results[str(app)]['data']['price_overview']['currency'] != None else None
              originalPrice = results[str(app)]['data']['price_overview']['initial'] if results[str(app)]['data']['price_overview']['initial'] != None else None
              discountPrice = results[str(app)]['data']['price_overview']['final'] if results[str(app)]['data']['price_overview']['final'] != None else None
            else:
              currency = None
              originalPrice = None
              discountPrice = None
            
            # get AppTags
            if ('genres' in results[str(app)]['data']):
              for tag in results[str(app)]['data']['genres']:
                if (tag['description'] in oldTags):
                  tagId = int(oldTags[tag['description']]['tag_id'])
                  if (int(app) in oldAppsTags):
                    if (int(tagId) not in oldAppsTags[int(app)]):
                      appTags.setdefault(app, {})[oldTags[tag['description']]['tag_id']] = tag['description']
                  else:
                    appTags.setdefault(app, {})[oldTags[tag['description']]['tag_id']] = tag['description']
            
            # get Screenshots
            # TODO: Test this block: old code was incorrectly formating oldAppsScreenshots
            if ("screenshots" in results[str(app)]['data']):
              for image in results[str(app)]['data']['screenshots']:
                if (int(app) in oldAppsScreenshots):
                  if (image['id'] in oldAppsScreenshots[int(app)]):
                    if (image['path_thumbnail'] not in oldAppsScreenshots[int(app)][image['id']]['path_thumbnail'] or image['path_full'] not in oldAppsScreenshots[int(app)][image['id']]['path_full']):
                      # either the thumbnail or full_path is different at the current order id. store screenshots
                      appScreenshots.setdefault(app, {})[image['id']] = ({"path_thumbnail": image['path_thumbnail'], "path_full": image['path_full']})
                  else:
                    # id does not exist in old screenshots. store new id screenshots.
                    appScreenshots.setdefault(app, {})[image['id']] = ({"path_thumbnail": image['path_thumbnail'], "path_full": image['path_full']})
                else:
                  # app does not exist in old screenshots. store new apps screenshots.
                  appScreenshots.setdefault(app, {})[image['id']] = ({"path_thumbnail": image['path_thumbnail'], "path_full": image['path_full']})
            
            # Get Videos
            if ("movies" in results[str(app)]['data']):
              for video in results[str(app)]['data']['movies']:
                if (int(app) in oldAppsVideos):
                  if (video['id'] not in oldAppsVideos[int(app)]):
                    # id does not exist in old videos. store new id videos.
                    appVideos.setdefault(app, {})[video['id']] = ({"video_name": video['name']})
                else:
                  # app does not exist in old videos. store new apps videos.
                  appVideos.setdefault(app, {})[video['id']] = ({"video_name": video['name']})
            
            # Get ReleaseDate 
            if ("release_date" in results[str(app)]['data']):
              if ("coming_soon" in results[str(app)]["data"]["release_date"]):
                comingSoon = bool(results[str(app)]["data"]["release_date"]["coming_soon"])
              else:
                comingSoon = None
              if ("date" in results[str(app)]["data"]["release_date"]):
                releaseDate = str(results[str(app)]["data"]["release_date"]["date"])
              else:
                releaseDate = None
            else:
              comingSoon = None
              releaseDate = None
            
            # Get Developers
            devs = []
            if ("developers" in results[str(app)]['data']):
              for developer in results[str(app)]['data']["developers"]:
                if (int(app) in oldAppsDevelopers):
                  if (developer not in str(oldAppsDevelopers[int(app)])):
                    # Developer does not exist for app. Add to devs array.
                    devs.append(developer)
                else:
                  # App doesn't exist in db so store the developer
                  devs.append(developer)
            # Remove duplicates & Store Results (Rare edge case. Steam_ID: 2342690)
            if (len(devs) > 0):
              appDevelopers[app] = list(set(devs))

            # Get Publishers
            pubs = []
            if ("publishers" in results[str(app)]['data']):
              for publisher in results[str(app)]['data']["publishers"]:
                if (int(app) in oldAppsPublishers):
                  if (publisher not in str(oldAppsPublishers[int(app)])):
                    # Publisher does not exist for app. Add to pubs array.
                    pubs.append(publisher)
                else:
                  # App doesn't exist in db so store the publisher
                  pubs.append(publisher)
            # Remove duplicates & Store Results (Rare edge case. Steam_ID: 2342690)
            if (len(pubs) > 0):
              appPublishers[app] = list(set(pubs))

            # Query AppReviews
            reviewsUrl = "https://store.steampowered.com/appreviews/{app}?json=1&purchase_type=all&language=english".format(app=app)
            reviewsResponse = requests.request("GET", reviewsUrl)
            if (reviewsResponse.status_code == 200 and len(reviewsResponse.text) > 0):
              reviewsResults = json.loads(reviewsResponse.text)
              if (reviewsResults['success'] == 1):
                if ("query_summary" in reviewsResults):
                  if ('total_positive' in reviewsResults['query_summary']):
                    positiveReviews = reviewsResults['query_summary']['total_positive'] if reviewsResults['query_summary']['total_positive'] != None else None
                  else:
                    positiveReviews = None
                  if ('total_reviews' in reviewsResults['query_summary']):
                    totalReviews = reviewsResults['query_summary']['total_reviews'] if reviewsResults['query_summary']['total_reviews'] != None else None
                  else:
                    totalReviews = None
                else:
                  positiveReviews = None
                  totalReviews = None
              else:
                # AppReviews has no details.
                positiveReviews = None
                totalReviews = None
                print('\r')
                print("AppReviews has no details for: ", app)
            else:
              positiveReviews = None
              totalReviews = None
              print('\r')
              print('Something Went wrong for: ', app)
          else:
            hasDetails = False
            type = None
            isFree = None
            comingSoon = None
            releaseDate = None
            desc = None
            shortDesc = None
            isMature = None
            currency = None
            originalPrice = None
            discountPrice = None
            positiveReviews = None
            totalReviews = None
            dlcSteamId = None
            print('\r')
            print("App Data is empty for: ", app)
        else:
          hasDetails = False
          type = None
          isFree = None
          comingSoon = None
          releaseDate = None
          desc = None
          shortDesc = None
          isMature = None
          currency = None
          originalPrice = None
          discountPrice = None
          positiveReviews = None
          totalReviews = None
          dlcSteamId = None
          print('\r')
          print("App has no details for: ", app)
      else:
        hasDetails = False
        type = None
        isFree = None
        comingSoon = None
        releaseDate = None
        desc = None
        shortDesc = None
        isMature = None
        currency = None
        originalPrice = None
        discountPrice = None
        positiveReviews = None
        totalReviews = None
        dlcSteamId = None
        print('\r')
        print('Something Went wrong for: ', app)

      # Ensure that each request does not exceed the defined rate
      totalTime = time.time() - start
      delay = RATE - totalTime
      if (delay > 0):
        time.sleep(delay)

      appDetails[app] = ({"HasDetails": hasDetails ,"Type": type, "IsMature": isMature, "IsFree": isFree, "Coming_Soon": comingSoon, "ReleaseDate": releaseDate, "Description": desc, "ShortDesc": shortDesc, "Currency": currency, "OriginalPrice": originalPrice, "DiscountPrice": discountPrice, "PositiveReviews": positiveReviews, "TotalReviews": totalReviews, "DlcSteamId": dlcSteamId, "UpdatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

  else:
    appDetails = None
  
  return (appDetails, appTags, appScreenshots, appVideos, appDevelopers, appPublishers)

def getGameDetails():
  # Retrieves all old tags from db
  oldTags = Utils.getOldTagsName()
  # Retrieves all old Apps_tags from db
  oldAppsTags = Utils.getAppsTags()
  # Retrieves new apps from file
  relative_path = os.path.join('../appdata', 'apps.json')
  data = getNewApps(relative_path)
  # Retrieves old apps from db
  oldAppsList = getOldApps()
  # Get new and updated apps 
  (newApps, updatedApps) = getNewAndUpdatedApps(data, oldAppsList)

  # Retrieve New and updated app details 
  print("Retrieving Info for ", len(newApps), "NEW GAME Apps")
  (newAppDetails, newAppsTags, newAppsScreenshots, newAppsVideos, newAppDevelopers, newAppPublishers) = getDetails(newApps, oldTags, oldAppsTags)

  print("Retrieving Info for ", len(updatedApps), "Updated GAME Apps")
  (updatedAppDetails, updatedAppsTags, updatedAppsScreenshots, updatedAppsVideos, updatedAppDevelopers, updatedAppPublishers) = getDetails(updatedApps, oldTags, oldAppsTags)

  # Write data to files
  relative_path = os.path.join('../appdata', 'newAppDetails.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppDetails, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedAppDetails.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppDetails, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newAppsTags.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppsTags, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedAppsTags.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppsTags, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newAppsScreenshots.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppsScreenshots, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedAppsScreenshots.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppsScreenshots, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newAppsVideos.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppsVideos, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedAppsVideos.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppsVideos, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newAppDevelopers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppDevelopers, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedAppDevelopers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppDevelopers, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newAppPublishers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppPublishers, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedAppPublishers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppPublishers, f, ensure_ascii=False, indent=4)

def getDLCDetails():
  # Retrieves all old tags from db
  oldTags = Utils.getOldTagsName()
  # Retrieves all old Apps_tags from db
  oldAppsTags = Utils.getAppsTags()
  # Retrieves new apps from file
  relative_path = os.path.join('../appdata', 'dlc.json')
  data = getNewApps(relative_path)
  # Retrieves old apps from db
  oldAppsList = getOldApps()
  # Get new and updated apps 
  (newApps, updatedApps) = getNewAndUpdatedApps(data, oldAppsList)

  # Retrieve New and updated app details 
  print("Retrieving Info for ", len(newApps), "NEW DLC Apps")
  (newAppDetails, newAppsTags, newAppsScreenshots, newAppsVideos, newAppDevelopers, newAppPublishers) = getDetails(newApps, oldTags, oldAppsTags)

  print("Retrieving Info for ", len(updatedApps), "Updated DLC Apps")
  (updatedAppDetails, updatedAppsTags, updatedAppsScreenshots, updatedAppsVideos, updatedAppDevelopers, updatedAppPublishers) = getDetails(updatedApps, oldTags, oldAppsTags)

  # Write data to files
  relative_path = os.path.join('../appdata', 'newDLCAppDetails.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppDetails, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedDLCAppDetails.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppDetails, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newDLCAppsTags.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppsTags, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedDLCAppsTags.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppsTags, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newDLCScreenshots.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppsScreenshots, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedDLCScreenshots.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppsScreenshots, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newDLCVideos.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppsVideos, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedDLCVideos.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppsVideos, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newDLCDevelopers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppDevelopers, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedDLCDevelopers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppDevelopers, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'newDLCPublishers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(newAppPublishers, f, ensure_ascii=False, indent=4)
  relative_path = os.path.join('../appdata', 'updatedDLCPublishers.json')
  with open(relative_path, 'w', encoding='utf-8') as f:
    json.dump(updatedAppPublishers, f, ensure_ascii=False, indent=4)

###############################################################################################
###############################################################################################
def main():
  getGameDetails()
  getDLCDetails()

if __name__ == '__main__':
  main()