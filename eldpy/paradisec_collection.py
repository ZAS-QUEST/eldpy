from collection import Collection
import urllib
import requests
import json
import re
from bs4 import BeautifulSoup
from paradisec_bundle import  ParadisecBundle

class ParadisecCollection(Collection):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.files = []

    def populate_bundles(self):
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
        j = json.loads(content)
        for item in j['features']:
            name = item['properties']['name']
            url = item['properties']['url']
            languagestring = item['properties'].get('languages','')
            languages = re.findall('- ([a-z][a-z][a-z])', languagestring)
            # print(languagestring,languages)
            self.bundles.append(ParadisecBundle(name,url,languages))
