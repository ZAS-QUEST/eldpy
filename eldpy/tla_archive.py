import re
import urllib
import pprint
import json
import humanize
import requests
from collections import Counter, defaultdict
from bs4 import BeautifulSoup

from tla_collection import  TLACollection
from tla_bundle import  TLABundle
from tla_file import  TLAFile



class TLAArchive:

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []


    def populate_collections(self, pagelimit=4, hardlimit=10000):
        print("populating collections")
        self.collections = self.get_tla_collections(pagelimit=pagelimit, hardlimit=hardlimit)

    def get_tla_collections(self, pagelimit=4, hardlimit=10000):
        collections = []
        for i in range(pagelimit):
            catalogpage = f'https://archive.mpi.nl/tla/islandora/object/tla%253A1839_00_0000_0000_0001_305B_C?page={i+1}'
            print(f"reading {catalogpage}")
            r = requests.get(catalogpage)
            content = r.content
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a')
            collections += [TLACollection(l['title'], f"https://archive.mpi.nl{l['href']}") for l in links if l.get('title') and '305B_C' not in l['href'] and l.get('href','').startswith("/tla/isl")]
        if len(collections) >= hardlimit:
            collections = collections[:hardlimit]
        print(f"finished. There are {len(collections)} collections")
        return collections



    def populate_bundles(self, hardlimit=10000, languages=True):
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
        self.populate_collections(pagelimit=4)
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
        with open(f'tla_copy{add}.json', 'w') as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))
