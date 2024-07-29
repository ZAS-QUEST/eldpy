import requests
import json

import re
import urllib
import pprint
import json

from collections import Counter, defaultdict
from bs4 import BeautifulSoup

from ailla_collection import  AillaCollection
# from ailla_bundle import  AillaBundle
# from ailla_file import  AillaFile

class AillaArchive:

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []

    def populate_collections(self,hardlimit=10000):
        print("populating AILLA collections")
        r = requests.get("https://ailla-backend-prod.gsc1-pub.lib.utexas.edu/collections/all")
        collection_list = json.loads(r.content)[:hardlimit]
        for collection in collection_list:
            id_ = collection['id']
            url = f"https://ailla.utexas.org/collections/{id_}"
            name = collection['title']['en']
            self.collections.append(AillaCollection(name, url))


    def populate_bundles(self, hardlimit=10000):
        print("populating bundles")
        for collection in self.collections:
            print(collection.name)
            if collection.bundles == []:
                collection.populate_bundles(hardlimit=hardlimit)
            self.bundles += collection.bundles


    def write_json(self, add=''):
        archive_dict = {}
        for collection in self.collections:
            collection_dict = {'name':collection.name, 'url':collection.url,'bundles':{}}
            for bundle in collection.bundles:
                bundle_dict = {
                    'name'  : bundle.name,
                    'url' : bundle.url,
                    'files' : [file_.__dict__ for file_ in bundle.files]
                }
                collection_dict['bundles'][bundle.name] = bundle_dict
            archive_dict[collection.name] = collection_dict
        with open(f'ailla_copy{add}.json', 'w') as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))


    def run(self):
        self.populate_collections()
        self.write_json(add='_c')
        self.populate_bundles()
        self.write_json(add='_b')
        # self.populate_files()
        # self.write_json(add='_f')




