import os
import sys
from dotenv import load_dotenv
import requests
import json
import time
from datetime import datetime
# Add the appropriate paths depending on the environment
if os.environ.get('DOCKERIZED'):
    from lib.utils import Utils
else:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from app.lib.utils import Utils

class AppsScraper:
  def main():
    start = time.time()
    load_dotenv()
    apiKey = os.getenv('STEAM_API_KEY')

    apps = dict()
    hasMoreResults = True
    lastAppId = ''
    while (hasMoreResults):
      url = "https://api.steampowered.com/IStoreService/GetAppList/v1/?key={key}&include_games=true&include_dlc=false&include_software=false&include_videos=false&include_hardware=false&max_results=50000&last_appid={lastID}&have_description_language=english".format(lastID=lastAppId, key=apiKey)
      response = requests.request("GET", url)
      results = json.loads(response.text)
      if ("apps" in results['response']):
        for game in results['response']['apps']:
          apps[game['appid']] = {"title": game['name'], "last_modified": game['last_modified'], "price_change_number": game['price_change_number'], "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        if ("have_more_results" in results['response']):
          if (results['response']["have_more_results"] == True):
            lastAppId = results['response']['last_appid']
          else:
            hasMoreResults = False
        else:
          hasMoreResults = False
      else:
        hasMoreResults = False

    Utils.checkIfDirectoryExists()
    relative_path = os.path.join('../appdata', 'apps.json')
    with open(relative_path, 'w', encoding='utf-8') as f:
      json.dump(apps, f, ensure_ascii=False, indent=4)

    end = time.time()
    length = end - start
    print("It took", length, "seconds!")
    print(len(apps))
    return len(apps)

if __name__ == '__main__':
  AppsScraper.main()