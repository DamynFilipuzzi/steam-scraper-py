import time
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Get all game IDs store in data.json
def getAllGameIds():
  file = open('data/data.json', encoding="utf-8")
  data = json.load(file)
  i = 0
  steamIds = dict()
  for e in data.values():
    steamIds[i] = e['SteamId']
    i += 1
  return steamIds

def init():
  # Run google chrome in headless mode (no browser popup)
  # TODO: Add Headless browsing later once confident in system
  # options = Options()
  # options.add_argument('--headless')

  driver = webdriver.Chrome()
  return driver

# check if on mature content warning page
def checkMatureContent():
  # Check if login blocked
  try:
    driver.find_element(By.ID, 'error_box')
    print("Login Blocked")
    return None
  except NoSuchElementException:
    pass

  # If not login restricted then bypass age gate
  try:
    driver.find_element(By.ID, 'app_agegate')
    print("Mature Content")
    return True
  except NoSuchElementException:
    print("Not Mature")
  return False

# If game is blocked behind mature wall set client age and view 
def accessMatureContent():
  driver.find_element(By.ID, "ageYear").send_keys("2000")
  driver.find_element(By.ID, "view_product_page_btn").click()


gameIds= getAllGameIds()
driver = init()

for g in gameIds.values():
  # Set each url and get html content for that game
  url = "https://store.steampowered.com/app/" + str(g)
  # url = "https://store.steampowered.com/app/2273420"
  print(url)
  driver.get(url)

  # Check if game is hidden behind mature block
  mature = checkMatureContent()
  if (mature):
    accessMatureContent()
  
  if (mature != None):
    # TODO scrape description and anything
    try:
      element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "game_area_description")))
    finally:
      page_source = driver.page_source
      soup = BeautifulSoup(page_source, "html.parser")
      search_results = soup.find("div", {"id": "game_area_description"})
      print(search_results.prettify(encoding="utf8"))
  
  # Needed in order to check if subsequent games are mature
  driver.delete_all_cookies()

driver.close()