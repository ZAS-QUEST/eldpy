from collection import Collection
import urllib
import requests
import json
import re
from bs4 import BeautifulSoup
from paradisec_bundle import  ParadisecBundle
from archive import LIMIT

class ParadisecCollection(Collection):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.files = []

    def populate_bundles(self, limit=LIMIT):
        try:
            r = requests.get(self.url)
        except requests.exceptions.ConnectionError:
            time.sleep(5)
            try:
                r = requests.get(self.url)
            except requests.exceptions.ConnectionError:
                    print(f"could not download bundles for {self.url}")
                    return
        content = r.content
        # print(content)
        soup = BeautifulSoup(content, "html.parser")
        tables = soup.find_all('table')
        trs = tables[0].find_all('tr')
        languagelinks = trs[8].find_all('a')
        languages = [l['href'].split('/')[-1] for l in languagelinks]
        # j = json.loads(content)
        bundles = tables[2].find_all('tr')[1:]
        for bundle in bundles[:limit]:
            tds = bundle.find_all('td')
            bundle_name = tds[1].text
            try:
                bundle_url = 'https://catalog.paradisec.org.au' + tds[2].find('a')['href']
            except TypeError:
                print(f'no URL for {bundle_name} in {self.name}')
                bundle_url = ''
            self.bundles.append(ParadisecBundle(bundle_name,bundle_url,languages))
