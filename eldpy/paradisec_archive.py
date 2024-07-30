import re
import urllib
import pprint
import json
import humanize
import requests
from collections import Counter, defaultdict
from bs4 import BeautifulSoup

from paradisec_collection import  ParadisecCollection
from paradisec_bundle import  ParadisecBundle
from paradisec_file import  ParadisecFile



class ParadisecArchive:

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []

    def populate_collections(self, hardlimit=1000):
        r = requests.get(f"https://catalog.paradisec.org.au/collections/search?page=1&per_page={hardlimit}")
        content = r.content
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find_all('table')[-1]
        trs = table.find_all('tr')
        for tr in trs:
            tds = tr.find_all('td')
            collection_name = tds[1].text
            collection_link = "https://catalog.paradisec.org.au/" + tds[7].find('a')['href']
            self.collections.append(ParadisecCollection(collection_name, collection_link))

    def populate_bundles(self, hardlimit=10000):
        print("populating bundles")
        for collection in self.collections:
            print(collection.name)
            if collection.bundles == []:
                collection.populate_bundles()
            self.bundles += collection.bundles

    def populate_files(self,hardlimit=10000):
        print(f"populating files from {len(self.collections)} collections")
        for i, collection in enumerate(self.collections):
            print(f"{i+1}/{len(self.collections)}")
            if collection.bundles == []:
                collection.populate_bundles()
            for bundle in collection.bundles:
                if bundle.files == []:
                    bundle.populate_files()
                self.files += bundle.files



    def run(self):
        self.populate_collections()
        self.write_json(add='_c')
        self.populate_bundles()
        self.write_json(add='_b')
        self.populate_files()
        self.write_json(add='_f')



    def write_json(self, add=''):
        archive_dict = {}
        for collection in self.collections:
            collection_dict = {'name':collection.name, 'url':collection.url,'bundles':{}}
            for bundle in collection.bundles:
                bundle_dict = {
                    'name'  : bundle.name,
                    'url' : bundle.url,
                    'files' : [file_.__dict__ for file_ in bundle.files],
                    'languages' : bundle.languages,
                }
                collection_dict['bundles'][bundle.name] = bundle_dict
            archive_dict[collection.name] = collection_dict
        with open(f'paradisec_copy{add}.json', 'w') as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))
