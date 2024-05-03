import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.wait import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from tqdm import tqdm

# Get all game IDs store in data.json
def getAllGameIds():
  file = open('data/data.json', encoding="utf-8")
  data = json.load(file)
  i = 0
  steamIds = dict()
  for e in data:
    steamIds[i] = e
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

def getReviews(soup, driver):
  # init array of size 2
  reviews = [0] * 2
  try:
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "review_summary_num_reviews")))
    element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "review_summary_num_positive_reviews")))
    reviews[0] = soup.find("input", {"id": "review_summary_num_reviews"}).get("value")
    reviews[1] = soup.find("input", {"id": "review_summary_num_positive_reviews"}).get("value")
  except TimeoutException:
    print("failed to find reviews")
    return reviews
  return reviews



##########################################
################## main ##################
##########################################



gameIds= getAllGameIds()
driver = init()

gamesInfo = dict()
for g in tqdm(gameIds.values(), desc="Scraping game info..."):
  # Set each url and get html content for that game
  url = "https://store.steampowered.com/app/" + str(g)
  print(url)
  driver.get(url)

  # Check if game is hidden behind mature block
  mature = checkMatureContent()
  if (mature):
    accessMatureContent()
  
  if (mature != None):
    try:
      element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "game_area_description")))
      page_source = driver.page_source
      soup = BeautifulSoup(page_source, "html.parser")
      search_results = soup.find("div", {"id": "game_area_description"})
      reviews = getReviews(soup, driver)
      gamesInfo[g] = ({"Description": str(search_results), "IsMature": mature, "TotalReviews": int(reviews[0]), "TotalPositiveReviews": int(reviews[1])})
    except TimeoutException:
      print("failed to find descriptions")
      gamesInfo[g] = ({"Description": None, "IsMature": None, "TotalReviews": 0, "TotalPositiveReviews": 0})
      pass
  else:
    gamesInfo[g] = ({"Description": None, "IsMature": None, "TotalReviews": 0, "TotalPositiveReviews": 0})
  
  # Needed in order to check if subsequent games are mature
  driver.delete_all_cookies()

driver.quit()

with open('data/descriptions.json', 'w', encoding='utf-8') as f:
  json.dump(gamesInfo, f, ensure_ascii=False, indent=4)

print(len(gamesInfo))