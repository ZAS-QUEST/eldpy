from eldpy.archives.collection import Collection
import urllib
from bs4 import BeautifulSoup
from eldpy.archives.ailla_bundle import  AillaBundle
import requests
import json

class AillaCollection(Collection):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.files = []

    def populate_bundles(self, limit=10000):
        print(f"fetching bundles for {self.name}, {self.url}")
        request_collection = requests.get(self.url)
        soup = BeautifulSoup(request_collection.content, 'html.parser')
        j = json.loads(soup.find('script',type="application/json").text)
        try:
            folders = j['props']['pageProps']['data']['folders'][:limit]
            print(f" Found {len(folders)} bundles")
        except KeyError:
            print(f" no data on {self.url}")
            self.bundles = []
            return
        self.bundles = [AillaBundle(folder['title']['en'],
                                    folder['id']
                                    )
                    for folder
                    in folders]

