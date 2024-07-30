from collection import Collection
import urllib
from bs4 import BeautifulSoup
from ailla_bundle import  AillaBundle
import requests
import json

class AillaCollection(Collection):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.files = []

    def populate_bundles(self, hardlimit=10000):
        print(self.url)
        request_collection = requests.get(self.url)
        soup = BeautifulSoup(request_collection.content, 'html.parser')
        j = json.loads(soup.find('script',type="application/json").text)
        try:
            folders = j['props']['pageProps']['data']['folders'][:hardlimit]
            print(f" There are {len(folders)} bundles in {self.url}")
        except KeyError:
            print(f" no data on {self.url}")
            self.bundles = []
            return
        self.bundles = [AillaBundle(folder['title']['en'],
                                    folder['id']
                                    )
                    for folder
                    in folders]

