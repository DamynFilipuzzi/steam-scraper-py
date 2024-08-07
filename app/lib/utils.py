import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras

class Utils:
  def checkIfDirectoryExists():
    if (os.path.exists('./appdata') == False):
      os.mkdir('./appdata')
  
  # Return all tags currently in the DB indexed by tag_id
  def getOldTagsID():
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    cur.execute('SELECT * FROM "Tags"')
    tagsOld = cur.fetchall()
    oldTagsList = dict()
    for tag in tagsOld:
      oldTagsList[tag[1]] = ({"id": tag[0], "tag_name": tag[2]})
    cur.close()
  
    return oldTagsList
  
  # Return all tags currently in the DB indexed by tag_name
  def getOldTagsName():
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
  
  # Return all Apps_Tags indexed by: {steam_id: {tag_id: {0}}}
  def getAppsTags():
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
  
  # Return all Screenshots indexed by: {steam_id: {image_order(id relative to app): {path_thumbnail: ... , path_full: ...}}} 
  def getAppsScreenshots():
    load_dotenv()
    connection_string = os.getenv('DATABASE_URL_PYTHON')
    conn = psycopg2.connect(connection_string)
    cur = conn.cursor()
    cur.execute('SELECT * FROM "Screenshots"')
    appsScreenshotsOld = cur.fetchall()
    cur.close()
    oldAppsScreenshotsList = dict()
    for screenshot in appsScreenshotsOld:
      oldAppsScreenshotsList.setdefault(screenshot[1], {})[screenshot[4]] = ({"path_thumbnail": screenshot[2], "path_full": screenshot[3]})

    return oldAppsScreenshotsList
  
  def getSubDirectory():
    subDirectory = 'appdata'
    if os.environ.get('DOCKERIZED'):
      subDirectory = '../appdata'
    return subDirectory
