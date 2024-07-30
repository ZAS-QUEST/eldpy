import requests
import json

import re
import urllib
import pprint
import json
import humanize

from collections import Counter, defaultdict
from bs4 import BeautifulSoup

from ailla_collection import  AillaCollection
from ailla_bundle import  AillaBundle
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

    def json_run_showcase(self,file_limit=999999):
        with open("showcase_ailla_copy_b.json") as json_in:
            d = json.load(json_in)
        for collection_name, collection_d in d.items():
            collection_url = collection_d['url']
            c = AillaCollection(collection_name, collection_url)
            collection_bundles = []
            for bundle_name, bundle_d in collection_d['bundles'].items():
                bundle_url = bundle_d['url']
                bundle_id = bundle_url.split('/')[-1]
                b = AillaBundle(bundle_name, bundle_id)
                b.populate_files()
                collection_bundles.append(b)
            c.bundles = collection_bundles
            print(f" There are {len(c.bundles)} bundles")
            self.collections.append(c)
        self.write_json(add='_f')
        self.report()


    def report(self):
        collections = self.collections
        bundles = [b for c in collections for b in c.bundles]
        files = [f for c in collections for b in c.bundles for f in b.files]
        types = [f.type_ for f in files]
        print(f"There are {len(collections)} collections")
        print(f"There are {len(bundles)} bundles")
        print(f"There are {len(files)} files")
        types_d = defaultdict(int)
        for f in files:
            types_d[f.type_] += f.size
        counter = Counter(types)
        for k, v in counter.items():
            readable_size = humanize.naturalsize(types_d[k])
            print (f" {k} files: {v} ({readable_size} total)")


