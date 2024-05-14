import requests
import json
import time

start = time.time()
payload = {}
headers = {}

apps = dict()
hasMoreResults = True
lastAppId = ''
while (hasMoreResults):
  url = "https://api.steampowered.com/IStoreService/GetAppList/v1/?key=B395DF29FCF1147B70EA8EC0FEED516F&include_games=true&include_dlc=false&include_software=false&include_videos=false&include_hardware=false&max_results=10&last_appid={lastID}&have_description_language=english".format(lastID=lastAppId)
  response = requests.request("GET", url, headers=headers, data=payload)
  results = json.loads(response.text)
  if ("apps" in results['response']):
    for game in results['response']['apps']:
      apps[game['appid']] = {"title": game['name'], "last_modified": game['last_modified'], "price_change_number": game['price_change_number']}
    if ("have_more_results" in results['response']):
      if (results['response']["have_more_results"] == True):
        lastAppId = results['response']['last_appid']
      else:
        hasMoreResults = False
    else:
      hasMoreResults = False
  else:
    hasMoreResults = False

with open('appdata/apps.json', 'w', encoding='utf-8') as f:
  json.dump(apps, f, ensure_ascii=False, indent=4)

end = time.time()
length = end - start
print("It took", length, "seconds!")
print(len(apps))

