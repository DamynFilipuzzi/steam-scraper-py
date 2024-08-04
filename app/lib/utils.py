import os

class Utils:
  def checkIfDirectoryExists():
    if (os.path.exists('./appdata') == False):
      os.mkdir('./appdata')