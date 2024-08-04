#  Command to run:
# pytest .\tests\tests.py --cov=app --cov-report=html

import pytest
import os.path
import shutil
from app.apps_scraper import AppsScraper
from app.dlc_scraper import DlcScraper
from app.lib.utils import Utils

def test_general_working():
  assert "foo".upper() == "FOO"

# test create appdata folder on clean build
def test_create_appdata_util():
  # remove appdata if exists
  if (os.path.exists('./appdata')):
    shutil.rmtree('./appdata')
  
  # Create appdata directory
  Utils.checkIfDirectoryExists()
  assert os.path.exists('./appdata') == True

def test_apps_scraper_connects_to_endpoint():
  apps = AppsScraper.main()
  assert apps >= 100000

def test_file_apps_created():
  fileExists = os.path.isfile('./appdata/apps.json')
  assert fileExists == True

def test_dlc_scraper_connects_to_endpoint():
  dlc = DlcScraper.main()
  assert dlc >= 40000

def test_file_dlc_created():
  fileExists = os.path.isfile('./appdata/dlc.json')
  assert fileExists == True