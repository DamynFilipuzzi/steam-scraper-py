#  Command to run:
# pytest .\tests\tests.py --cov=app
# docker compose -p tester -f ./docker-compose-test.yml up --build --force-recreate --remove-orphans

import pytest
import os
from unittest import mock
import os.path
import shutil
from app.lib.utils import Utils, DB
from app.apps_scraper import AppsScraper
from app.dlc_scraper import DlcScraper
from app.tags_creator import TagScraper

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

def test_fail_job():
  assert False == True

# # https://stackoverflow.com/questions/35143055/how-to-mock-psycopg2-cursor-object
# @mock.patch('psycopg2.connect')
# def test_tags_store(self, mock_connect):
#   expected = [['fake', 'row', 1], ['fake', 'row', 2]]
  
#   # result of psycopg2.connect(**connection_stuff)
#   mock_con = mock_connect.return_value
#   mock_cur = mock_con.cursor.return_value  # result of con.cursor(cursor_factory=DictCursor)
#   mock_cur.fetchall.return_value = expected  # return this when calling cur.fetchall()

#   result = DB.getOldTagsID()
#   self.assertEqual(result, expected)