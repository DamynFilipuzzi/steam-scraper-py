import requests
import json
import os
import sys
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import logging
# Add the appropriate paths depending on the environment
if os.environ.get('DOCKERIZED'):
    from lib.utils import Utils, DB
else:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app.lib.utils import Utils, DB

class TagScraper:
  # Scrape all apps
  def tagsScraper():
    load_dotenv()
    apiKey = os.getenv('STEAM_API_KEY')
    oldTagsList = DB.getOldTagsID()

    URL = 'https://api.steampowered.com/IStoreService/GetMostPopularTags/v1/?key={key}'.format(key=apiKey)
    response = requests.get(URL)

    tagsList = dict()
    if (response.status_code != 200 and len(response.text) > 0):
      print('Error scraping tags')
      exit()
    else:
      results = json.loads(response.text)
      for tag in results['response']['tags']:
        # Only store the new tags found in tagsList
        if (tag['tagid'] not in oldTagsList):
          tagsList[tag['tagid']] = {'tag_name': tag['name']}

    Utils.checkIfDirectoryExists()
    relative_path = os.path.join(Utils.getSubDirectory(), 'tags.json')
    with open(relative_path, 'w', encoding='utf-8') as f:
      json.dump(tagsList, f, ensure_ascii=False, indent=4)

    return tagsList

  # Upload All New Tags
  def storeNewTags(tagsList):
    # Prepare tags for batch upload
    newTagsTuple = []
    for tagId in tagsList:
      newTagsTuple.append((int(tagId), str(tagsList[tagId]['tag_name'])))

    # try to store tags
    try:
      load_dotenv()
      connection_string = os.getenv('DATABASE_URL_PYTHON')
      conn = psycopg2.connect(connection_string)
      cur = conn.cursor()
      psycopg2.extras.execute_batch(cur, """INSERT INTO "Tags" (tag_id, tag_name) VALUES (%s, %s)""", newTagsTuple)
      conn.commit()
      print("Storing: {tagsList} new Tags.".format(tagsList=len(newTagsTuple)))
    except Exception as error:
      print('Failed to store New Tags')
      logging.info("Failed to store New Tags")
      logging.critical(newTagsTuple)
      logging.critical(error)
      sys.exit(1)
    finally:
      print("\nclosing\n")
      conn.close()

  def main():
    tagsList = TagScraper.tagsScraper()
    relative_path = os.path.join(Utils.getSubDirectory(), 'errors.log')
    logging.basicConfig(filename=relative_path, filemode='a', format='%(asctime)s, %(filename)s, %(funcName)s, %(lineno)d, %(levelname)s, %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',  level=logging.DEBUG)
    TagScraper.storeNewTags(tagsList)

if __name__ == '__main__':
  TagScraper.main()