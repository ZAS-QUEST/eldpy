from collection import Collection
import urllib
import requests
import json
from bs4 import BeautifulSoup
from paradisec_bundle import  ParadisecBundle

class ParadisecCollection(Collection):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.files = []

    def populate_bundles(self):
        r = requests.get(self.url)
        content = r.content
        j = json.loads(content)
        for item in j['features']:
            name = item['properties']['name']
            url = item['properties']['url']
            languages = item['properties'].get('languages',[])
            self.bundles.append(ParadisecBundle(name,url,languages))
