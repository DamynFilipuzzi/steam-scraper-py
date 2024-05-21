import json
from tqdm import tqdm
import roman
import unidecode

# Read data to insert from file
# TODO: use newAppDetails.json to verify instead of all apps from apps.json
file = open('appdata/apps.json', encoding="utf-8")
data = json.load(file)

gameTag = dict()
# Insert entry into games table if it does not exist.
for e in tqdm(data, desc="Tokenizing titles"):
  steamID = e
  title = str(data[e]['title'])
  
  title = title.strip()
  title = title.replace('™', '').replace('®', '').replace("'", '').replace(':', '').replace('-', ' ').replace('!', '')

  titleSplit = title.split(' ')
  
  # Remove empty fields
  # TODO: FIX. Not working
  for word in titleSplit:
    if (word == ''):
      titleSplit.remove('')

  i = 0
  for word in titleSplit:
    if (word == '&'):
      titleSplit.append('and')

    # Remove accents from string
    titleSplit[i] = unidecode.unidecode(word)

    # If string is roman numeral convert to int 
    try:
      if (roman.fromRoman(word)):
        r = roman.fromRoman(word)
        titleSplit[i] = str(r)
    except roman.InvalidRomanNumeralError:
      pass

    i += 1
  gameTag[steamID] = titleSplit

with open('appdata/appTags.json', 'w', encoding='utf-8') as f:
  json.dump(gameTag, f, ensure_ascii=False, indent=4)

print(len(gameTag))