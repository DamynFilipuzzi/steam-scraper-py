import os
import sys
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from tqdm import tqdm
from datetime import datetime
import logging
import time
# Add the appropriate paths depending on the environment
if os.environ.get('DOCKERIZED'):
    from lib.utils import Utils, DB
else:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app.lib.utils import Utils, DB

def timing(f):
    def wrap(*args, **kwargs):
      time1 = time.time()
      ret = f(*args, **kwargs)
      time2 = time.time()
      print('{:s} function took {:.3f} ms \n'.format(f.__name__, (time2-time1)*1000.0))

      return ret
    return wrap

def getApps(apps, appDetails, isNew):
  appTuples = []
  for steamId in appDetails:
    # Only Store apps that have details
    if (appDetails[steamId]['HasDetails']):
      title = str(apps[steamId]['title'])
      type = str(appDetails[steamId]['Type'])
      dlcSteamId = int(appDetails[steamId]['DlcSteamId']) if appDetails[steamId]['DlcSteamId'] else None
      lastModified = int(apps[steamId]['last_modified'])
      priceChangeNumber = int(apps[steamId]['price_change_number'])
      updatedAt = apps[steamId]['updated_at']
      totalReviews = int(appDetails[steamId]['TotalReviews']) if appDetails[steamId]['TotalReviews'] else None
      positiveReviews = int(appDetails[steamId]['PositiveReviews']) if appDetails[steamId]['PositiveReviews'] else None
      # Due to the way query statement is written for updating records steam_id is stored as the last item in the tuple
      if (isNew):
        appTuples.append((steamId, title, type, lastModified, priceChangeNumber, updatedAt, totalReviews, positiveReviews, dlcSteamId))
      else:
        appTuples.append((title, type, lastModified, priceChangeNumber, updatedAt, totalReviews, positiveReviews, dlcSteamId, steamId))

  return appTuples

def getDetails(appDetails, isNew):
  appDetailTuples = []
  appReleaseDateTuple = []
  for steamId in appDetails:
    # Only Store apps that have details
    if (appDetails[steamId]['HasDetails']):
      description = str(appDetails[steamId]['Description']) if appDetails[steamId]['Description'] else None
      shortDescription = str(appDetails[steamId]['ShortDesc']) if appDetails[steamId]['ShortDesc'] else None
      isMature = bool(appDetails[steamId]['IsMature']) if appDetails[steamId]['IsMature'] == False or appDetails[steamId]['IsMature'] == True else None
      updatedAt = appDetails[steamId]['UpdatedAt']
      # Due to the way query statement is written for updating records steam_id is stored as the last item in the tuple
      if (isNew):
        appDetailTuples.append((steamId, description, shortDescription, isMature, updatedAt))
      else:
        appDetailTuples.append((description, shortDescription, isMature, updatedAt, steamId))
      
      # Store data for release date table.
      comingSoon = bool(appDetails[steamId]["Coming_Soon"]) if appDetails[steamId]["Coming_Soon"] == False or appDetails[steamId]["Coming_Soon"] == True else None
      releaseDate = str(appDetails[steamId]["ReleaseDate"]) if appDetails[steamId]["ReleaseDate"] else None
      appReleaseDateTuple.append((steamId, comingSoon, releaseDate))
  
  return (appDetailTuples, appReleaseDateTuple)

def getPrice(appDetails, apps=None):
  appPriceTuples = []
  # Apps should only be set to none when the info being passed is new and not already stored in the DB
  if (apps == None):
    for steamId in appDetails:
      # Only Store apps that have details
      if (appDetails[steamId]['HasDetails']):
        isFree = bool(appDetails[steamId]['IsFree']) if appDetails[steamId]['IsFree'] == False or appDetails[steamId]['IsFree'] == True else None
        currency = str(appDetails[steamId]['Currency']) if appDetails[steamId]['Currency'] else None
        originalPrice = int(appDetails[steamId]['OriginalPrice']) if appDetails[steamId]['OriginalPrice'] else None
        discountPrice = int(appDetails[steamId]['DiscountPrice']) if appDetails[steamId]['DiscountPrice'] else None
        validTo = '9999-12-31'
        appPriceTuples.append((steamId, isFree, currency, originalPrice, discountPrice, validTo))
  else:
    # Get updated Apps by id (used for query in the next step)
    steam_ids = []
    for steamId in appDetails:
      # Only Store apps that have details
      if (appDetails[steamId]['HasDetails']):
        steam_ids.append(int(steamId))
    
    # Get all old data for the Updated Apps
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    cur.execute("""SELECT * FROM public."Apps" left join public."Prices" ON "Apps".steam_id = "Prices".steam_id WHERE "Prices".valid_to='9999-12-31T00:00:00.000Z' AND "Apps".steam_id = ANY(%s)""", [steam_ids])

    results = cur.fetchall()
    cur.close()
    
    # TODO: FIX THIS IF STATEMENT. CURRENTLY NOT WORKING AS INTENDED. (PROOF AT: SELECT * FROM public."Prices" WHERE "steam_id"=2778580 ORDER BY id ASC )
    # Store the updated prices in the App Price Tuple
    for app in results:
      if (app[5] != apps[str(app[1])]['price_change_number'] and (app[15] != appDetails[steamId]['DiscountPrice'] or app[14] != appDetails[steamId]['OriginalPrice'])):
        steamId = str(app[1])
        isFree = bool(appDetails[steamId]['IsFree']) if appDetails[steamId]['IsFree'] == False or appDetails[steamId]['IsFree'] == True else None
        currency = str(appDetails[steamId]['Currency']) if appDetails[steamId]['Currency'] else None
        originalPrice = int(appDetails[steamId]['OriginalPrice']) if appDetails[steamId]['OriginalPrice'] else None
        discountPrice = int(appDetails[steamId]['DiscountPrice']) if appDetails[steamId]['DiscountPrice'] else None
        validTo = '9999-12-31'
        appPriceTuples.append((steamId, isFree, currency, originalPrice, discountPrice, validTo))

  return appPriceTuples

# Upload New Apps
@timing
def storeNewApps(newAppsList):
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Apps" (steam_id, title, type, last_modified, price_change_number, updated_at, total_reviews, total_positive_reviews, dlc_steam_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""", newAppsList)
    conn.commit()
    print("Storing: {lenNewApps} new apps.".format(lenNewApps=len(newAppsList)))
    logging.info("Storing: {lenNewApps} new apps.".format(lenNewApps=len(newAppsList)))
  except Exception as error:
    print('Failed to store New App')
    logging.info("Failed to store New App")
    logging.critical(newAppsList)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Upload New App Details
@timing
def storeNewAppDetails(newAppDetailsList):
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "App_Info" (steam_id, description, short_description, is_mature, updated_at) VALUES (%s, %s, %s, %s, %s)""", newAppDetailsList)
    conn.commit()
    print("Storing: {lenNewAppDetailsList} new app Details.".format(lenNewAppDetailsList=len(newAppDetailsList)))
    logging.info("Storing: {lenNewAppDetailsList} new app Details.".format(lenNewAppDetailsList=len(newAppDetailsList)))
  except Exception as error:
    print("Failed to store New App Details")
    logging.info("Failed to store New App Details")
    logging.critical(newAppDetailsList)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store New App Prices
@timing
def storeNewAppPrices(newAppPriceList):
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Prices" (steam_id, is_free, currency, original_price, discount_price, valid_to) VALUES (%s, %s, %s, %s, %s, %s)""", newAppPriceList)
    conn.commit()
    print("Storing: {lenNewAppPriceList} new app Prices.".format(lenNewAppPriceList=len(newAppPriceList)))
    logging.info("Storing: {lenNewAppPriceList} new app Prices.".format(lenNewAppPriceList=len(newAppPriceList)))
  except Exception as error:
    print("Failed to store New App Prices")
    logging.info("Failed to store New App Prices")
    logging.critical(newAppPriceList)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store Updated Apps
@timing
def storeUpdatedApps(updatedAppsList):
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """UPDATE "Apps" SET title=%s, type=%s, last_modified=%s, price_change_number=%s, updated_at=%s, total_reviews=%s, total_positive_reviews=%s, dlc_steam_id=%s WHERE steam_id=%s""", updatedAppsList)
    conn.commit()
    print("Storing: {lenUpdatedAppsList} updated apps.".format(lenUpdatedAppsList=len(updatedAppsList)))
    logging.info("Storing: {lenUpdatedAppsList} updated apps.".format(lenUpdatedAppsList=len(updatedAppsList)))
  except Exception as error:
    print("Failed to store Updated App")
    logging.info("Failed to store Updated App")
    logging.critical(updatedAppsList)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store Updated App Details
@timing
def storeUpdatedAppDetails(updatedAppDetailsList):
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """UPDATE "App_Info" SET description=%s, short_description=%s, is_mature=%s, updated_at=%s WHERE steam_id=%s""", updatedAppDetailsList)
    conn.commit()
    print("Storing: {lenUpdatedAppDetailsList} updated app Details.".format(lenUpdatedAppDetailsList=len(updatedAppDetailsList)))
    logging.info("Storing: {lenUpdatedAppDetailsList} updated app Details.".format(lenUpdatedAppDetailsList=len(updatedAppDetailsList)))
  except Exception as error:
    print("Failed to store Updated App Details")
    logging.info("Failed to store Updated App Details")
    logging.critical(updatedAppDetailsList)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store Updated App prices
@timing
def storeUpdatedAppPrices(updatedAppPriceList):
  # get new tuple containing only ((valid_to, steam_id))
  updateTuple = []
  for price in updatedAppPriceList:
    updateTuple.append((datetime.now(), price[0]))
  
  # 1. Update old price data. ONLY Setting the value of valid_to to the current datetime.
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """UPDATE "Prices" SET valid_to=%s WHERE steam_id=%s""", updateTuple)
    conn.commit()
    print("Storing: {lenUpdateTuple} updated app Prices.".format(lenUpdateTuple=len(updateTuple)))
    logging.info("Storing: {lenUpdateTuple} updated app Prices.".format(lenUpdateTuple=len(updateTuple)))
  except Exception as error:
    print("Failed to store Updated App Prices")
    logging.info("Failed to store Updated App Prices")
    logging.critical(updateTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()
  
  # 2. Insert New Price data replacing the previously stored one with the field valid_to == '9999-12-31'
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Prices" (steam_id, is_free, currency, original_price, discount_price, valid_to) VALUES (%s, %s, %s, %s, %s, %s)""", updatedAppPriceList)
    conn.commit()
    print("Storing: {lenUpdatedAppPriceList} new UPDATED app Prices.".format(lenUpdatedAppPriceList=len(updatedAppPriceList)))
    logging.info("Storing: {lenUpdatedAppPriceList} new UPDATED app Prices.".format(lenUpdatedAppPriceList=len(updatedAppPriceList)))
  except Exception as error:
    print("Failed to store New App Prices")
    logging.info("Failed to store New App Prices")
    logging.critical(updatedAppPriceList)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store New App Tags
@timing
def storeNewAppsTags(tags):
  appTagsTuple = []
  for app in tags:
    for tag in tags[app]:
      appTagsTuple.append((int(app), int(tag)))

  # Insert into Apps_Tags table
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Apps_Tags" (steam_id, tag_id) VALUES (%s, %s)""", appTagsTuple)
    conn.commit()
    print("Storing: {appTagsTuple} new Apps_Tags.".format(appTagsTuple=len(appTagsTuple)))
    logging.info("Storing: {appTagsTuple} new Apps_Tags.".format(appTagsTuple=len(appTagsTuple)))
  except Exception as error:
    print("Failed to store New Apps_tags")
    logging.info("Failed to store New Apps_tags")
    logging.critical(appTagsTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store New screenshots
@timing
def storeOrUpdateScreenshots(screenshots):
  appsScreenshotsTuple = []
  for app in screenshots:
    for order in screenshots[app]:
      appsScreenshotsTuple.append((int(app), int(order), screenshots[app][order]['path_thumbnail'], screenshots[app][order]['path_full']))

  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Screenshots" (steam_id, image_order, path_thumbnail, path_full) VALUES (%s, %s, %s, %s) ON CONFLICT (steam_id, image_order) DO UPDATE SET (steam_id, image_order, path_thumbnail, path_full) = ROW(EXCLUDED.steam_id, EXCLUDED.image_order, EXCLUDED.path_thumbnail, EXCLUDED.path_full)""", appsScreenshotsTuple)
    conn.commit()
    print("Storing: {appsScreenshotsTuple} Screenshots.".format(appsScreenshotsTuple=len(appsScreenshotsTuple)))
    logging.info("Storing: {appsScreenshotsTuple} screenshots.".format(appsScreenshotsTuple=len(appsScreenshotsTuple)))
  except Exception as error:
    print("Failed to store screenshots")
    logging.info("Failed to store screenshots")
    # logging.critical(appsScreenshotsTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store New or Updated Videos
@timing
def storeOrUpdateVideos(videos):
  appsVideosTuple = []
  for app in videos:
    for id in videos[app]:
      appsVideosTuple.append((int(app), int(id), videos[app][id]['video_name']))

  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Videos" (steam_id, video_id, video_name) VALUES (%s, %s, %s) ON CONFLICT (video_id) DO UPDATE SET (steam_id, video_id, video_name) = ROW(EXCLUDED.steam_id, EXCLUDED.video_id, EXCLUDED.video_name)""", appsVideosTuple)
    conn.commit()
    print("Storing: {appsVideosTuple} Videos.".format(appsVideosTuple=len(appsVideosTuple)))
    logging.info("Storing: {appsVideosTuple} Videos.".format(appsVideosTuple=len(appsVideosTuple)))
  except Exception as error:
    print("Failed to store Videos")
    logging.info("Failed to store Videos")
    logging.critical(appsVideosTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store or update Release Date
@timing
def storeOrUpdateReleaseDate(appsReleaseDatesTuple):
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "ReleaseDate" (steam_id, coming_soon, release_date) VALUES (%s, %s, %s) ON CONFLICT (steam_id) DO UPDATE SET (steam_id, coming_soon, release_date) = ROW(EXCLUDED.steam_id, EXCLUDED.coming_soon, EXCLUDED.release_date)""", appsReleaseDatesTuple)
    conn.commit()
    print("Storing: {appsReleaseDatesTuple} AppsReleaseDates.".format(appsReleaseDatesTuple=len(appsReleaseDatesTuple)))
    logging.info("Storing: {appsReleaseDatesTuple} AppsReleaseDates.".format(appsReleaseDatesTuple=len(appsReleaseDatesTuple)))
  except Exception as error:
    print("Failed to store AppsReleaseDates")
    logging.info("Failed to store AppsReleaseDates")
    logging.critical(appsReleaseDatesTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

def getOldDevelopers():
  # Get all Developers from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * From "Developers"')
  devsOld = cur.fetchall()
  oldDevsList = dict()
  for devs in devsOld:
    oldDevsList[devs[1]] = devs[0]
  
  return oldDevsList

def getOldAppsDevelopers():
  # Get all Developers from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * From "Apps_Developers"')
  devsOld = cur.fetchall()
  oldAppsDevsList = dict()
  for devs in devsOld:
    oldAppsDevsList.setdefault(devs[0], {})[devs[1]] = ({"steam_id": devs[1]})
  
  return oldAppsDevsList

# Store New Developers
@timing
def storeNewDevelopers(developersList):
  developersTuple = []
  for dev in developersList:
    developersTuple.append((dev,))
  
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Developers" (developer_name) VALUES (%s)""", developersTuple)
    conn.commit()
    print("Storing: {developersTuple} Developers.".format(developersTuple=len(developersTuple)))
    logging.info("Storing: {developersTuple} Developers.".format(developersTuple=len(developersTuple)))
  except Exception as error:
    print("Failed to store Developers")
    logging.info("Failed to store Developers")
    logging.critical(developersTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store Apps_Developers and Developers if Developer does not exist in DB.
@timing
def storeAppsDevelopers(newAppsDevelopers):
  oldDevs = getOldDevelopers()
  devsToStore = list()
  # Get Developers Not currently in DB
  for app in newAppsDevelopers:
    for dev in newAppsDevelopers[app]:
      if (dev not in oldDevs and dev not in devsToStore):
        devsToStore.append(dev)
  # Store new Developers
  storeNewDevelopers(devsToStore)
  # Get updated data for Developers (Id's for recently created Developers).
  oldDevs = getOldDevelopers()
  oldAppsDevs = getOldAppsDevelopers()
  appsDevelopersTuple = []
  for app in newAppsDevelopers:
    for dev in newAppsDevelopers[app]:
      if (dev in oldDevs):
        if (oldDevs[dev] in oldAppsDevs):
          if (int(app) not in oldAppsDevs[oldDevs[dev]]):
            appsDevelopersTuple.append((int(oldDevs[dev]), int(app)))
        else:
          appsDevelopersTuple.append((int(oldDevs[dev]), int(app)))
  # Store Apps_Developers
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Apps_Developers" (developer_id, steam_id) VALUES (%s, %s)""", appsDevelopersTuple)
    conn.commit()
    print("Storing: {appsDevelopersTuple} Apps_Developers.".format(appsDevelopersTuple=len(appsDevelopersTuple)))
    logging.info("Storing: {appsDevelopersTuple} Apps_Developers.".format(appsDevelopersTuple=len(appsDevelopersTuple)))
  except Exception as error:
    print("Failed to store Apps_Developers")
    logging.info("Failed to store Apps_Developers")
    logging.critical(appsDevelopersTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

def getOldPublishers():
  # Get all Publishers from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * From "Publishers"')
  pubsOld = cur.fetchall()
  oldPubsList = dict()
  for pubs in pubsOld:
    oldPubsList[pubs[1]] = pubs[0]
  
  return oldPubsList

def getOldAppsPublishers():
  # Get all Developers from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * From "Apps_Publishers"')
  pubsOld = cur.fetchall()
  oldAppsPubsList = dict()
  for pubs in pubsOld:
    oldAppsPubsList.setdefault(pubs[0], {})[pubs[1]] = ({"steam_id": pubs[1]})
  
  return oldAppsPubsList

# Store New Publisher
@timing
def storeNewPublishers(publishersList):
  publishersTuple = []
  for pub in publishersList:
    publishersTuple.append((pub,))
  
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Publishers" (publisher_name) VALUES (%s)""", publishersTuple)
    conn.commit()
    print("Storing: {publishersTuple} Publishers.".format(publishersTuple=len(publishersTuple)))
    logging.info("Storing: {publishersTuple} Publishers.".format(publishersTuple=len(publishersTuple)))
  except Exception as error:
    print("Failed to store Publishers")
    logging.info("Failed to store Publishers")
    logging.critical(publishersTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

# Store Apps_Publishers and Publishers if Publishers does not exist in DB.
@timing
def storeAppsPublishers(newAppsPublishers):
  oldPubs = getOldPublishers()
  pubsToStore = list()
  # Get Publishers Not currently in DB
  for app in newAppsPublishers:
    for pub in newAppsPublishers[app]:
      if (pub not in oldPubs and pub not in pubsToStore):
        pubsToStore.append(pub)
  # Store new Publishers
  storeNewPublishers(pubsToStore)
  # Get updated data for Publishers (Id's for recently created Publishers).
  oldPubs = getOldPublishers()
  oldAppsPubs = getOldAppsPublishers()
  appsPublishersTuple = []
  for app in newAppsPublishers:
    for pub in newAppsPublishers[app]:
      if (pub in oldPubs):
        if (oldPubs[pub] in oldAppsPubs):
          if (int(app) not in oldAppsPubs[oldPubs[pub]]):
            appsPublishersTuple.append((int(oldPubs[pub]), int(app)))
        else:
          appsPublishersTuple.append((int(oldPubs[pub]), int(app)))
  # Store Apps_Publishers
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "Apps_Publishers" (publisher_id, steam_id) VALUES (%s, %s)""", appsPublishersTuple)
    conn.commit()
    print("Storing: {appsPublishersTuple} Apps_Publishers.".format(appsPublishersTuple=len(appsPublishersTuple)))
    logging.info("Storing: {appsPublishersTuple} Apps_Publishers.".format(appsPublishersTuple=len(appsPublishersTuple)))
  except Exception as error:
    print("Failed to store Apps_Publishers")
    logging.info("Failed to store Apps_Publishers")
    logging.critical(appsPublishersTuple)
    logging.critical(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

def storeGameApps():
  logging.info("Storing Apps-Games")
  # Get all Apps Details
  relative_path = os.path.join(Utils.getSubDirectory(), 'apps.json')
  file = open(relative_path, encoding="utf-8")
  apps = json.load(file)
  # Get New Apps Details
  relative_path = os.path.join(Utils.getSubDirectory(), 'newAppDetails.json')
  file = open(relative_path, encoding="utf-8")
  newAppDetails = json.load(file)
  # Get Updated App Details
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedAppDetails.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppDetails = json.load(file)
  # Get New Tags
  relative_path = os.path.join(Utils.getSubDirectory(), 'newAppsTags.json')
  file = open(relative_path, encoding="utf-8")
  newAppsTags = json.load(file)
  # Get Updated Tags
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedAppsTags.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsTags = json.load(file)
  # Get new Screenshots
  relative_path = os.path.join(Utils.getSubDirectory(), 'newAppsScreenshots.json')
  file = open(relative_path, encoding="utf-8")
  newAppsScreenshots = json.load(file)
  # Get updated Screenshots
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedAppsScreenshots.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsScreenshots = json.load(file)
  # Get new Videos
  relative_path = os.path.join(Utils.getSubDirectory(), 'newAppsVideos.json')
  file = open(relative_path, encoding="utf-8")
  newAppsVideos = json.load(file)
  # Get updated Videos
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedAppsVideos.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsVideos = json.load(file)
  # Get new App Developers
  relative_path = os.path.join(Utils.getSubDirectory(), 'newAppDevelopers.json')
  file = open(relative_path, encoding="utf-8")
  newAppsDevelopers = json.load(file)
  # Get Updated App Developers
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedAppDevelopers.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsDevelopers = json.load(file)
  # Get new App Publishers
  relative_path = os.path.join(Utils.getSubDirectory(), 'newAppPublishers.json')
  file = open(relative_path, encoding="utf-8")
  newAppsPublishers = json.load(file)
  # Get Updated App Publishers
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedAppPublishers.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsPublishers = json.load(file)

  # Get App Tuples
  newAppsList = getApps(apps, newAppDetails, isNew=True)
  updatedAppsList = getApps(apps, updatedAppDetails, isNew=False)

  # Get App Details Tuples
  newAppDetailsList, newAppReleaseDateList = getDetails(newAppDetails, isNew=True)
  updatedAppDetailsList, updatedAppReleaseDateList = getDetails(updatedAppDetails, isNew=False)

  # Get App Price Tuples
  newAppPriceList = getPrice(newAppDetails, apps=None)
  updatedAppPriceList = getPrice(updatedAppDetails, apps=apps)

  storeNewApps(newAppsList)
  storeNewAppDetails(newAppDetailsList)
  storeNewAppPrices(newAppPriceList)
  # ***storeUpdatedAppPrices() MUST RUN BEFORE storeUpdatedApps() Otherwise the price_change_number will be altered before validation step***
  storeUpdatedAppPrices(updatedAppPriceList)
  storeUpdatedApps(updatedAppsList)
  storeUpdatedAppDetails(updatedAppDetailsList)
  storeNewAppsTags(newAppsTags)
  storeNewAppsTags(updatedAppsTags)
  storeOrUpdateScreenshots(newAppsScreenshots)
  storeOrUpdateScreenshots(updatedAppsScreenshots)
  storeOrUpdateVideos(newAppsVideos)
  storeOrUpdateVideos(updatedAppsVideos)
  storeOrUpdateReleaseDate(newAppReleaseDateList)
  storeOrUpdateReleaseDate(updatedAppReleaseDateList)
  storeAppsDevelopers(newAppsDevelopers)
  storeAppsDevelopers(updatedAppsDevelopers)
  storeAppsPublishers(newAppsPublishers)
  storeAppsPublishers(updatedAppsPublishers)

def storeDLCApps():
  logging.info("Storing Apps-DLC")
  # Get all Apps Details
  relative_path = os.path.join(Utils.getSubDirectory(), 'dlc.json')
  file = open(relative_path, encoding="utf-8")
  apps = json.load(file)
  # Get New Apps Details
  relative_path = os.path.join(Utils.getSubDirectory(), 'newDLCAppDetails.json')
  file = open(relative_path, encoding="utf-8")
  newAppDetails = json.load(file)
  # Get Updated App Details
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedDLCAppDetails.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppDetails = json.load(file)
  # Get New Tags
  relative_path = os.path.join(Utils.getSubDirectory(), 'newDLCAppsTags.json')
  file = open(relative_path, encoding="utf-8")
  newAppsTags = json.load(file)
  # Get Updated Tags
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedDLCAppsTags.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsTags = json.load(file)
  # Get new Screenshots
  relative_path = os.path.join(Utils.getSubDirectory(), 'newDLCScreenshots.json')
  file = open(relative_path, encoding="utf-8")
  newAppsScreenshots = json.load(file)
  # Get updated Screenshots
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedDLCScreenshots.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsScreenshots = json.load(file)
  # Get new Videos
  relative_path = os.path.join(Utils.getSubDirectory(), 'newDLCVideos.json')
  file = open(relative_path, encoding="utf-8")
  newAppsVideos = json.load(file)
  # Get updated Videos
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedDLCVideos.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsVideos = json.load(file)
  # Get new App Developers
  relative_path = os.path.join(Utils.getSubDirectory(), 'newDLCDevelopers.json')
  file = open(relative_path, encoding="utf-8")
  newAppsDevelopers = json.load(file)
  # Get Updated App Developers
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedDLCDevelopers.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsDevelopers = json.load(file)
  # Get new App Publishers
  relative_path = os.path.join(Utils.getSubDirectory(), 'newDLCPublishers.json')
  file = open(relative_path, encoding="utf-8")
  newAppsPublishers = json.load(file)
  # Get Updated App Publishers
  relative_path = os.path.join(Utils.getSubDirectory(), 'updatedDLCPublishers.json')
  file = open(relative_path, encoding="utf-8")
  updatedAppsPublishers = json.load(file)

    # Get App Tuples
  newAppsList = getApps(apps, newAppDetails, isNew=True)
  updatedAppsList = getApps(apps, updatedAppDetails, isNew=False)

  # Get App Details Tuples
  newAppDetailsList, newAppReleaseDateList = getDetails(newAppDetails, isNew=True)
  updatedAppDetailsList, updatedAppReleaseDateList = getDetails(updatedAppDetails, isNew=False)

  # Get App Price Tuples
  newAppPriceList = getPrice(newAppDetails, apps=None)
  updatedAppPriceList = getPrice(updatedAppDetails, apps=apps)

  storeNewApps(newAppsList)
  storeNewAppDetails(newAppDetailsList)
  storeNewAppPrices(newAppPriceList)
  # ***storeUpdatedAppPrices() MUST RUN BEFORE storeUpdatedApps() Otherwise the price_change_number will be altered before validation step***
  storeUpdatedAppPrices(updatedAppPriceList)
  storeUpdatedApps(updatedAppsList)
  storeUpdatedAppDetails(updatedAppDetailsList)
  storeNewAppsTags(newAppsTags)
  storeNewAppsTags(updatedAppsTags)
  storeOrUpdateScreenshots(newAppsScreenshots)
  storeOrUpdateScreenshots(updatedAppsScreenshots)
  storeOrUpdateVideos(newAppsVideos)
  storeOrUpdateVideos(updatedAppsVideos)
  storeOrUpdateReleaseDate(newAppReleaseDateList)
  storeOrUpdateReleaseDate(updatedAppReleaseDateList)
  storeAppsDevelopers(newAppsDevelopers)
  storeAppsDevelopers(updatedAppsDevelopers)
  storeAppsPublishers(newAppsPublishers)
  storeAppsPublishers(updatedAppsPublishers)

#########################################################################################
#########################################################################################
#########################################################################################

def main():
  relative_path = os.path.join(Utils.getSubDirectory(), 'errors.log')
  logging.basicConfig(filename=relative_path, filemode='a', format='%(asctime)s, %(filename)s, %(funcName)s, %(lineno)d, %(levelname)s, %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',  level=logging.DEBUG)
  storeGameApps()
  storeDLCApps()
  

if __name__ == '__main__':
  main()