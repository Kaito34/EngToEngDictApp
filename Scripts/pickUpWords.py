import requests
from bs4 import BeautifulSoup
import csv
import sys
import pandas as pd
import numpy as np
import logging
import traceback
import os
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

search_url = f"https://sites.google.com/view/meld-lsm/home"
print(f"search_url = {search_url}")

# リンク内容を取得
# if error: requests.exceptions.ConnectionError:('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
# The issue is that the website filters out requests without a proper User-Agent, so just use a random one from MDN:
url = requests.get(search_url,headers={
"User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36"
})
soup = BeautifulSoup(url.text, "html.parser")

for i in soup.find_all('p'):
    print(i.get_text())

# 難易度の高そうな単語のみ抽出