import os
from dotenv import load_dotenv
import requests
import json
import time
from datetime import datetime

start = time.time()
payload = {}
headers = {
  'Cookie': 'Cookie_1=value; browserid=3435760192849254767; steamCountry=CA%7Cb3495110b69ce3b66ffa45eaed107e4b'
}
load_dotenv()
apiKey = os.getenv('STEAM_API_KEY')

apps = dict()
hasMoreResults = True
lastAppId = ''
while (hasMoreResults):
  url = "https://api.steampowered.com/IStoreService/GetAppList/v1/?key={key}&include_games=true&include_dlc=false&include_software=false&include_videos=false&include_hardware=false&max_results=50000&last_appid={lastID}&have_description_language=english".format(lastID=lastAppId, key=apiKey)
  response = requests.request("GET", url, headers=headers, data=payload)
  results = json.loads(response.text)
  if ("apps" in results['response']):
    for game in results['response']['apps']:
      apps[game['appid']] = {"title": game['name'], "last_modified": game['last_modified'], "price_change_number": game['price_change_number'], "updated_at": datetime.now()}
    if ("have_more_results" in results['response']):
      if (results['response']["have_more_results"] == True):
        lastAppId = results['response']['last_appid']
      else:
        hasMoreResults = False
    else:
      hasMoreResults = False
  else:
    hasMoreResults = False

with open('/appdata/apps.json', 'w', encoding='utf-8') as f:
  json.dump(apps, f, ensure_ascii=False, indent=4)

end = time.time()
length = end - start
print("It took", length, "seconds!")
print(len(apps))

