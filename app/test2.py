import os
import json
from tqdm import tqdm

print("Test2: read games File")

# Read data to insert from file
if (os.path.isfile('/appdata/games.json')):
  file = open('/appdata/games.json', encoding="utf-8")
  data = json.load(file)
  
  # Insert entry into games table if it does not exist. 
  for e in tqdm(data, desc="Inserting Records..."):
    pass
  
  print(len(data))
else:
  print('failed to find games.json')
print("\nclosing\n")