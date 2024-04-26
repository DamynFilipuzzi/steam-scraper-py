import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import json
from tqdm import tqdm
import roman

# Read data to insert from file
file = open('data/data.json', encoding="utf-8")
data = json.load(file)

c=0
# Insert entry into games table if it does not exist.
for e in tqdm(data, desc="Tokenizing titles"):
  steamID = e
  title = str(data[e]['Title'])

  title = title.replace('™', '').replace('®', '').replace("'", '').replace(':', '').replace('-', '').replace('!', '')

  titleSplit = title.split(' ')
  
  i = 0
  for word in titleSplit:
    # TODO: REMOVE ACCENTS, AND Add acronyms for games. ei bg3, gta5
    if (word == ''):
      titleSplit.remove('')
    if (word == '&'):
      titleSplit.append('and')
    try:
      if (roman.fromRoman(word)):
        r = roman.fromRoman(word)
        titleSplit[i] = str(r)
    except roman.InvalidRomanNumeralError:
      pass

    i += 1

  print(titleSplit)
  c += 1
  if (c == 100):
    break
