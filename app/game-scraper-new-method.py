import requests
import json
import time

    # "applist": {
    #     "apps": [
    #         {
    #             "appid": 2728750,
    #             "name": "Gozenyojinomanimani"
    #         },
    #         {
    #             "appid": 2728790,
    #             "name": "Pryzm Demo"
    #         },

start = time.time()
url = "https://api.steampowered.com/ISteamApps/GetAppList/v2/"

headers = {
  'Cookie': 'browserid=3435760192839891630; steamCountry=US%7C1f4fc49d289900c9524af2da53b32296'
}

response = requests.request("GET", url, headers=headers)
results = json.loads(response.text)

games = dict()
for game in results['applist']['apps']:
  steamId = game['appid']
  title = game['name']

  games[steamId] = {"Title": title}

print(len(games))

# with open('/appdata/games.json', 'w', encoding='utf-8') as f:
with open('appdata/games.json', 'w', encoding='utf-8') as f:
  json.dump(games, f, ensure_ascii=False, indent=4)
  
end = time.time()
length = end - start
print("It took", length, "seconds!")