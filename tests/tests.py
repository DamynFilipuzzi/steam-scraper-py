#  Command to run:
# pytest .\tests\tests.py --cov=app

import pytest
from unittest import mock
import os.path
import shutil
from app.apps_scraper import AppsScraper
from app.dlc_scraper import DlcScraper
from app.tags_creator import TagScraper
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

def test_apps_scraper():
  apps = AppsScraper.main()
  assert apps >= 100000

def test_file_apps_created():
  fileExists = os.path.isfile('./appdata/apps.json')
  assert fileExists == True

def test_dlc_scraper():
  dlc = DlcScraper.main()
  assert dlc >= 40000

def test_file_dlc_created():
  fileExists = os.path.isfile('./appdata/dlc.json')
  assert fileExists == True

def test_tags_scraper():
  tags = TagScraper.tagsScraper()
  assert tags != None

# https://stackoverflow.com/questions/35143055/how-to-mock-psycopg2-cursor-object
# @mock.patch('psycopg2.connect')
# def test_tags_store(self, mock_connect):
#   expected = [['fake', 'row', 1], ['fake', 'row', 2]]
  
#   # result of psycopg2.connect(**connection_stuff)
#   mock_con = mock_connect.return_value