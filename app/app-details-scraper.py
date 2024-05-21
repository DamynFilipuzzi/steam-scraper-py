import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import requests
import json
from tqdm import tqdm
import time
from datetime import datetime

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

def getNewApps():
  # Read data to insert from file
  file = open('/appdata/apps.json', encoding="utf-8")
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
    oldAppsList[app[1]] = ({"id:": app[0], "title": app[2], "type": app[3], "original_price": app[4], "discount_price": app[5], "last_modified": app[6], "price_change_number": app[7], "updated_at": app[8], "created_at": app[9]})
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

def getDetails(appData):
  if (appData != None):
    # Rate at which each request can be made. 
    rate = 1.5
    appTags = dict()
    appDetails = dict()
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
            desc = None
            shortDesc = None
            isMature = None
            currency = None
            originalPrice = None
            discountPrice = None
            positiveReviews = None
            totalReviews = None
            print('\r')
            print("App Data is empty for: ", app)
        else:
          hasDetails = False
          type = None
          isFree = None
          desc = None
          shortDesc = None
          isMature = None
          currency = None
          originalPrice = None
          discountPrice = None
          positiveReviews = None
          totalReviews = None
          print('\r')
          print("App has no details for: ", app)
      else:
        hasDetails = False
        type = None
        isFree = None
        desc = None
        shortDesc = None
        isMature = None
        currency = None
        originalPrice = None
        discountPrice = None
        positiveReviews = None
        totalReviews = None
        print('\r')
        print('Something Went wrong for: ', app)

      # Ensure that each request does not exceed the defined rate
      totalTime = time.time() - start
      delay = rate - totalTime
      if (delay > 0):
        time.sleep(delay)

      appDetails[app] = ({"HasDetails": hasDetails ,"Type": type, "IsMature": isMature, "IsFree": isFree, "Description": desc, "ShortDesc": shortDesc, "Currency": currency, "OriginalPrice": originalPrice, "DiscountPrice": discountPrice, "PositiveReviews": positiveReviews, "TotalReviews": totalReviews, "UpdatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})

  else:
    appDetails = None
  
  return (appDetails, appTags)

###############################################################################################
###############################################################################################

# Retrieves all old tags from db
oldTags = getTags()
# Retrieves all old Apps_tags from db
oldAppsTags = getAppsTags()
# Retrieves new apps from file
data = getNewApps()
# Retrieves old apps from db
oldAppsList = getOldApps()
# Get new and updated apps 
(newApps, updatedApps) = getNewAndUpdatedApps(data, oldAppsList)

# Retrieve New and updated app details 
print("Retrieving Info for ", len(newApps), "NEW Apps")
(newAppDetails, newAppsTags) = getDetails(newApps)

print("Retrieving Info for ", len(updatedApps), "Updated Apps")
(updatedAppDetails, updatedAppsTags) = getDetails(updatedApps)

# Write data to files
with open('/appdata/newAppDetails.json', 'w', encoding='utf-8') as f:
  json.dump(newAppDetails, f, ensure_ascii=False, indent=4)
with open('/appdata/updatedAppDetails.json', 'w', encoding='utf-8') as f:
  json.dump(updatedAppDetails, f, ensure_ascii=False, indent=4)
with open('/appdata/newAppsTags.json', 'w', encoding='utf-8') as f:
  json.dump(newAppsTags, f, ensure_ascii=False, indent=4)
with open('/appdata/updatedAppsTags.json', 'w', encoding='utf-8') as f:
  json.dump(updatedAppsTags, f, ensure_ascii=False, indent=4)