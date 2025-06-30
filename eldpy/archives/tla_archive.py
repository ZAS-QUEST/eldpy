"""
instances of The Language Archive
"""

# import re
# import urllib
# import pprint
import json

# import humanize
# import sqlite3
import requests

# from collections import Counter, defaultdict
from bs4 import BeautifulSoup

from eldpy.archives.tla_collection import TLACollection

# from tla_bundle import  TLABundle
# from tla_file import  TLAFile
from eldpy.helpers import type2megatype
from eldpy.language_metadata import language_dictionary
from eldpy.archives.tla_sizes import tla_sizes
from eldpy.archives.archive import Archive, LIMIT

class TLAArchive(Archive):
    """
    an instance of The Language Archive
    """

    def __init__(self):
        super().__init__("TLA", "https://archive.mpi.nl/tla")

    def populate_collections(self, limit=LIMIT, pagelimit=4):
        print("populating collections")
        self.collections = self.get_tla_collections(pagelimit=pagelimit, limit=limit)

    def get_tla_collections(self,  limit=LIMIT, pagelimit=4):
        """
        get all TLA collections
        """
        collections = []
        for i in range(pagelimit):
            catalogpage = f"https://archive.mpi.nl/tla/islandora/object/tla%253A1839_00_0000_0000_0001_305B_C?page={i+1}"
            print(f"reading {catalogpage}")
            r = requests.get(catalogpage, timeout=120)
            content = r.content
            soup = BeautifulSoup(content, "html.parser")
            links = soup.find_all("a")
            collections += [
                TLACollection(l["title"], f"https://archive.mpi.nl{l['href']}")
                for l in links
                if l.get("title")
                and "305B_C" not in l["href"]
                and l.get("href", "").startswith("/tla/isl")
            ]
        if len(collections) >= limit:
            collections = collections[:limit]
        print(f"finished. There are {len(collections)} collections")
        return collections

    def populate_bundles(self, limit=LIMIT, offset=0):
        """
        get all bundles for the collections
        """
        print(f"populating bundles. Offset is {offset}")
        for i, collection in enumerate(self.collections[offset:]):
            print(i+offset, collection.name)
            if collection.bundles == []:
                collection.populate_bundles()
            self.bundles += collection.bundles

    def populate_files(self, limit=10000):
        """
        get all files for the bundles
        """
        print(f"populating files from {len(self.collections)} collections")
        for i, collection in enumerate(self.collections):
            print(f"{i+1}/{len(self.collections)}")
            if collection.bundles == []:
                collection.populate_bundles()
            for bundle in collection.bundles:
                if bundle.files == []:
                    bundle.populate_files()
                self.files += bundle.files

    #
    # def run(self):
    #     self.populate_collections(pagelimit=4)
    #     self.write_json(add='_c')
    #     self.populate_bundles()
    #     self.write_json(add='_b')
    #     self.populate_files()
    #     self.write_json(add='_f')

    def write_json(self, add=""):
        """
        write out the archive metadata as json
        """
        archive_dict = {}
        for collection in self.collections:
            collection_dict = {
                "name": collection.name,
                "url": collection.url,
                "bundles": {},
            }
            for bundle in collection.bundles:
                bundle_dict = {
                    "name": bundle.name,
                    "url": bundle.url,
                    "files": [file_.__dict__ for file_ in bundle.files],
                    "languages": bundle.languages,
                }
                collection_dict["bundles"][bundle.name] = bundle_dict
            archive_dict[collection.name] = collection_dict
        with open(f"out/tla_copy{add}.json", "w", encoding="utf8") as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))




    def get_id(self, f):
        id_ = f["url"].split("/")[-1].strip().replace("%3A", ":")
        return id_

    def get_megatype(self, type_):
        return type2megatype(type_)

    def get_length(self, f):
        return 0

    def get_size(self, f):
        """return the size of a file in bytes"""

        return tla_sizes.get(f["url"].split("/")[-1].strip().replace("%3A", ":"), 0)

    def get_languages(self, s):
        """return a list of ISO-639-3 codes"""

        result = []
        try:
            languages = s[0].split("\n")
        except IndexError:
            languages = []
        for language in languages:
            try:
                iso6393 = language_dictionary[language]["iso6393"]
            except KeyError:
                continue
            result.append(iso6393)
        return result


    def populate(self, limit=LIMIT, bundle_offset=0):
        self.populate_collections()
        self.populate_bundles(offset=bundle_offset)
        self.populate_files()



if __name__ == "__main__":
    ta = TLAArchive()
    ta.populate(bundle_offset=46)
    ta.write_json()
    # ta.insert_into_database("tla_copy_f.json")
