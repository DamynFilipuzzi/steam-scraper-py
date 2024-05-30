import os
from dotenv import load_dotenv
import psycopg2
import psycopg2.extras
import json

def getAppsWithLastPrice():
  # Get all apps from db
  load_dotenv()
  connection_string = os.getenv('DATABASE_URL_PYTHON')
  conn = psycopg2.connect(connection_string)
  cur = conn.cursor()
  cur.execute("""SELECT * FROM public."Apps" left join public."Prices" ON "Apps".steam_id = "Prices".steam_id WHERE "Prices".valid_to='9999-12-31T00:00:00.000Z'""")
  appsOld = cur.fetchall()
  oldAppsList = dict()
  for app in appsOld:
    oldAppsList[app[1]] = ({"id:": app[0], "title": app[2], "type": app[3], "last_modified": str(app[6]), "price_change_number": app[7], "updated_at": str(app[8]), "created_at": str(app[9]), "total_positive_reviews": app[10], 
                            "total_reviews": app[11], "price_id": app[12], "is_free": app[14], "currency": app[15], "original_price": app[16], "discount_price": app[17], "valid_from": str(app[18]), "valid_to": str(app[19])})
  cur.close()
  
  return oldAppsList

apps = getAppsWithLastPrice()

print(len(apps))

with open('appdata/testttttt.json', 'w', encoding='utf-8') as f:
  json.dump(apps, f, ensure_ascii=False, indent=4)