import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import time
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import sys
from fp.fp import FreeProxy

def getApps():
    # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute('SELECT * FROM "Apps"')
  appsOld = cur.fetchall()
  apps = dict()
  for app in appsOld:
    apps[app[1]] = ({"id:": app[0], "title": app[2], "type": app[3], "original_price": app[4], "discount_price": app[5], "last_modified": app[6], "price_change_number": app[7], "updated_at": app[8], "created_at": app[9]})
  cur.close()
  
  return apps

def getTop100(URL, updatedAt, proxy, topSeller=False):
  # Run google chrome in headless mode (no browser popup)
  options = Options()
  options.add_argument("start-maximized")
  options.add_argument("enable-automation")
  options.add_argument("--headless")
  options.add_argument("--no-sandbox")
  options.add_argument("--disable-dev-shm-usage")
  options.add_argument("--disable-browser-side-navigation")
  options.add_argument("--disable-gpu")
  options.add_argument(f'--proxy-server={proxy}')

  # Set up the Chrome WebDriver
  driver = webdriver.Chrome(options=options)
  driver.get(URL)
  time.sleep(5)

  # Get the page source
  page_source = driver.page_source
  driver.close()

  # Parse the page source with BeautifulSoup
  soup = BeautifulSoup(page_source, "html.parser")

  appIds = getApps()  
  results = dict()
  search_results = soup.find_all('tr')
  counter = 1
  for row in search_results:
    tdCount = 0
    tds = row.find_all('td')
    id = 0
    current = 0
    peak = 0
    for td in tds:
      if (topSeller):
        if (tdCount == 2):
          try:
            id = int(re.search('/app/(.+?)/', str(td)).group(1))
          except Exception:
            # pass on bundles, packages
            pass
      else:
        if (tdCount == 2):
          id = int(re.search('/app/(.+?)/', str(td)).group(1))
        if (tdCount == 4):
          current = int(re.search('>(.+?)<', str(td)).group(1).replace(',',''))
        if (tdCount == 5):
          peak = int(re.search('>(.+?)<', str(td)).group(1).replace(',',''))
      tdCount += 1
    
    if (topSeller):
      if (id != 0):
        if (int(id) in appIds):
          results[id] = {"app_order": counter, "updated_at": updatedAt}
          counter += 1
    else:
      if (id != 0 and current != 0 and peak != 0):
        if (int(id) in appIds):
          results[id] = results[id] = {"app_order": counter, "current": current, "peak": peak, "updated_at": updatedAt}
          counter += 1

  return results

def truncateTable(table):
    try:
      load_dotenv()
      connection_string = os.getenv('DATABASE_URL_PYTHON')
      conn = psycopg2.connect(connection_string)
      cur = conn.cursor()
      cur.execute('Truncate table "{table}"'.format(table=table))
      conn.commit()
      print("Truncated table: ", table)
    except Exception as error:
      print("Failed to store to truncate table: ")
      print(error)
      sys.exit(1)

def storeMostPlayed(values):
  mpList = []
  for steamId in values:
    mpList.append((steamId, values[steamId]['app_order'], values[steamId]['current'], values[steamId]['peak'], values[steamId]['updated_at']))

  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "MostPlayed" (steam_id, app_order, current, peak, updated_at) VALUES (%s, %s, %s, %s, %s)""", mpList)
    conn.commit()
    print("Storing: {mpList} new MostPlayed.".format(mpList=len(mpList)))
  except Exception as error:
    print("Failed to store New MostPlayed")
    print(mpList)
    print(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()

def storeTopSelling(values):
  tsList = []
  for steamId in values:
    tsList.append((steamId, values[steamId]['app_order'], values[steamId]['updated_at']))
  
  try:
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    psycopg2.extras.execute_batch(cur, """INSERT INTO "TopSellers" (steam_id, app_order, updated_at) VALUES (%s, %s, %s)""", tsList)
    conn.commit()
    print("Storing: {tsList} new TopSelling.".format(tsList=len(tsList)))
  except Exception as error:
    print("Failed to store New TopSelling")
    print(tsList)
    print(error)
    sys.exit(1)
  finally:
    print("\nclosing\n")
    conn.close()


def main():
  counter = 0
  # Get Proxy
  while True:
    try:
      proxy = FreeProxy(https=True).get()
      print(proxy)
      updatedAt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
      URL = "https://store.steampowered.com/charts/mostplayed"
      resultsMostPlayed = getTop100(URL, updatedAt, proxy, False)
      URL = "https://store.steampowered.com/charts/topselling/CA"
      resultsTopSelling = getTop100(URL, updatedAt, proxy, True)
      print('Most Played: ', len(resultsMostPlayed))
      print('Top Selling: ', len(resultsTopSelling))
      if (len(resultsMostPlayed) != 0 and len(resultsTopSelling) != 0):
        print("success")
        truncateTable("MostPlayed")
        storeMostPlayed(resultsMostPlayed)
        truncateTable("TopSellers")
        storeTopSelling(resultsTopSelling)
        break
      else:
        print("fail retrying")
    except Exception as error:
      print(error)

    counter += 1
    if (counter == 10):
      break

if __name__ == '__main__':
  main()