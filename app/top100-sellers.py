import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import json
from tqdm import tqdm

URL = "https://store.steampowered.com/charts/mostplayed"
# URL = "https://store.steampowered.com/charts/topselling/CA"

# Run google chrome in headless mode (no browser popup)
options = Options()
options.add_argument("start-maximized")
options.add_argument("enable-automation")
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-browser-side-navigation")
options.add_argument("--disable-gpu")

# Set up the Chrome WebDriver
driver = webdriver.Chrome(options=options)
driver.get(URL)
time.sleep(5)

# Get the page source
page_source = driver.page_source
driver.quit()

# Parse the page source with BeautifulSoup
soup = BeautifulSoup(page_source, "html.parser")

search_results = soup.find_all(href=re.compile("https://store.steampowered.com/app/"))

for row in search_results:
  # print(row)
  print(re.search('/app/(.+?)/', str(row)).group(1))

print('Total returned: ', len(search_results))
