"""
instances of The Endangered Language Archive
"""

# import re
# import urllib
# import pprint
import json

# from collections import Counter, defaultdict
# import sqlite3
from bs4 import BeautifulSoup

# import humanize
import requests

from archive import Archive, DEBUG, LIMIT

from elar_collection import  ElarCollection
# from elar_bundle import  ElarBundle
# from elar_file import  ElarFile


class ElarArchive(Archive):

    """
    instances of The Endangered Language Archive
    """

    def __init__(self):
        super().__init__("ELAR", "https://www.elararchive.org/")

    def populate_collections(self, limit=LIMIT, pagelimit=40):
        print("populating collections")
        self.collections = self.get_elar_collections(pagelimit=pagelimit, limit=limit)

    def populate_bundles(self, limit=LIMIT, hardlimit=LIMIT, languages=True):
        """add all bundles"""
        print("populating bundles")
        for i, collection in enumerate(self.collections[:LIMIT]):
            print(i, collection.name)
            if collection.bundles == []:
                collection.populate_bundles(limit=limit, languages=languages)
            self.bundles += collection.bundles

    def populate_files(self,limit=LIMIT):
        """add all files"""

        print(f"populating files from {len(self.collections)} collections")
        for i, collection in enumerate(self.collections):
            print(f"{i+1}/{len(self.collections)}")
            if collection.bundles == []:
                collection.populate_bundles()
            for bundle in collection.bundles:
                if bundle.files == []:
                    bundle.populate_files(limit=limit)
                self.files += bundle.files

    def get_elar_collections(self, pagelimit=40, limit=10000):
        """add all collections"""
        if DEBUG:
            pagelimit = LIMIT
            print(f"limit set to {LIMIT}")
        collections = []
        for i in range(pagelimit):
            catalogpage = f'https://www.elararchive.org/uncategorized/SO_5f038640-311d-4296-a3e9-502e8a18f5b7/?pg={i}'
            print(f"reading {catalogpage}")
            # try:
            r = requests.get(catalogpage, timeout=120)
            content = r.text
            new_collection_links = self.get_elar_collection_links_(content)
            print(f" found {len(new_collection_links)} collections")
            collections += new_collection_links
            # except Exception:
            #     print(f"could not download {catalogpage}")
        if len(collections) >= limit:
            collections = collections[:limit]
        print(f"finished. There are {len(collections)} collections")
        return collections

    def get_elar_collection_links_(self, page):
        """retrieve all links pointing to ELAR collections"""

        soup = BeautifulSoup(page, 'html.parser')
        collection_links = [ElarCollection(a.text, a['href']) for h5 in soup.find_all('h5') for a in h5.find_all('a')]
        return collection_links[:LIMIT]
    #
    # def get_elar_bundles(collections):
    #     elar_bundles = []
    #     for collection in collections:
    #         elar_bundles += get_collection_bundles(collection)
    #
    # def get_bundles_on_page(soup):
    #     return [(a['href'], a.text) for h5 in soup.find_all('h5') for a in h5.find_all('a')]
    #
    # def get_files_on_page(soup):
    #     return [(a['href'], a.text, a.findNext('div').text.strip()) for h5 in soup.find_all('h5') for a in h5.find_all('a')]
    #
    # def get_collection_bundles(collection):
    #     url = collection[0]
    #     print(url)
    #     with urllib.request.urlopen(url) as collection_reader:
    #         content = collection_reader.read()
    #         soup = BeautifulSoup(content, 'html.parser')
    #         try:
    #             limit = int(soup.find('div',class_='pagination').find_all('a')[-2].text)
    #         except IndexError:
    #             limit = 1
    #         bundles = get_bundles_on_page(soup)
    #         current = 2
    #     while current <= limit:
    #         current_url =  url + f"?pg={current}"
    #         print(current_url)
    #         with urllib.request.urlopen(current_url) as current_collection_reader:
    #             current_content = current_collection_reader.read()
    #             current_soup = BeautifulSoup(current_content, 'html.parser')
    #             bundles += get_bundles_on_page(current_soup)
    #         current += 1
    #     return bundles

    # def get_files(bundle):
    #     url = bundle[0]
    #     print(url)
    #
    #     with urllib.request.urlopen(url) as bundle_reader:
    #         try:
    #             content = bundle_reader.read()
    #         except urllib.error.HTTPError:
    #             print (f"{url} could not be opened")
    #             return []
    #         soup = BeautifulSoup(content, 'html.parser')
    #         try:
    #             limit = int(soup.find('div',class_='pagination').find_all('a')[-2].text)
    #         except IndexError:
    #             limit = 1
    #         files = get_files_on_page(soup)
    #         current = 2
    #     while current <= limit:
    #         current_url =  url + f"?pg={current}"
    #         print(current_url)
    #         with urllib.request.urlopen(current_url) as current_file_reader:
    #             current_content = current_file_reader.read()
    #             current_soup = BeautifulSoup(current_content, 'html.parser')
    #             files += get_bundles_on_page(current_soup)
    #         current += 1
    #     return files

    def write_json(self, add=''):
        """
        write out the archive metadata as json
        """
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
        with open(f'out/elar_copy{add}.json', 'w', encoding="utf8") as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))





    # def json_run_bundle(self):
    #     with open("elar_copy_b.json", encoding="utf8") as json_in:
    #         d = json.load(json_in)
    #     for collection_name, collection_d in d.items():
    #         collection_url = collection_d['url']
    #         c = ElarCollection(collection_name, collection_url)
    #         collection_bundles = []
    #         for bundle_name, bundle_d in collection_d['bundles'].items():
    #             bundle_url = bundle_d['url']
    #             b = ElarBundle(bundle_name, bundle_url)
    #             collection_bundles.append(b)
    #         c.bundles = collection_bundles
    #         self.collections.append(c)
    #     self.populate_files()
    #     self.write_json(add='_f')

    # def json_run_showcase(self,file_limit=999999):
    #     with open("showcase_elar_copy_f.json", encoding="utf8") as json_in:
    #         d = json.load(json_in)
    #     i = 0
    #     for collection_name, collection_d in d.items():
    #         i+=1
    #         if i>5:
    #             break
    #         c = ElarCollection(collection_name, collection_d['url'])
    #         collection_bundles = []
    #         for bundle_name, bundle_d in collection_d['bundles'].items():
    #             b = ElarBundle(bundle_name, bundle_d['url'])
    #             bundle_files = []
    #             for file_d in bundle_d['files'][:file_limit]:
    #                 f = ElarFile(file_d['name'], file_d['url'], file_d['type_'])
    #                 f.get_size()
    #                 bundle_files.append(f)
    #             b.files = bundle_files
    #             collection_bundles.append(b)
    #         c.bundles = collection_bundles
    #     self.collections.append(c)
    #     self.report()
    #
    # def report(self):
    #     collections = self.collections
    #     bundles = [b for c in collections for b in c.bundles]
    #     files = [f for c in collections for b in c.bundles for f in b.files]
    #     types = [f.type_ for f in files]
    #     print(f"There are {len(collections)} collections")
    #     print(f"There are {len(bundles)} bundles")
    #     print(f"There are {len(files)} files")
    #     types_d = defaultdict(int)
    #     for f in files:
    #         types_d[f.type_] += f.size
    #     counter = Counter(types)
    #     for k, v in counter.items():
    #         readable_size = humanize.naturalsize(types_d[k])
    #         print (f" {k} files: {v} ({readable_size} total)")
    #
    # def insert_into_database(self, input_file, db_name='test.db'):
    #     pass



if __name__ == "__main__":
    ea = ElarArchive()
    # ea.populate()
    ea.populate_collections()
    ea.populate_bundles()
    ea.populate_files()
    ea.write_json()
    # ea.insert_into_database()
