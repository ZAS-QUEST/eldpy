"""
instances of The Language Archive
"""

# import re
# import urllib
# import pprint
import json

# import humanize
import sqlite3
import requests

# from collections import Counter, defaultdict
from bs4 import BeautifulSoup

from tla_collection import TLACollection

# from tla_bundle import  TLABundle
# from tla_file import  TLAFile
from helpers import type2megatype, language_dictionary
from tla_sizes import tla_sizes


class TLAArchive:
    """
    an instance of The Language Archive
    """

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []

    # def populate_collections(self, pagelimit=4, hardlimit=10000):
    #     print("populating collections")
    #     self.collections = self.get_tla_collections(pagelimit=pagelimit, hardlimit=hardlimit)

    def get_tla_collections(self, pagelimit=4, hardlimit=10000):
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
        if len(collections) >= hardlimit:
            collections = collections[:hardlimit]
        print(f"finished. There are {len(collections)} collections")
        return collections

    def populate_bundles(self):
        """
        get all bundles for the collections
        """
        print("populating bundles")
        for collection in self.collections:
            print(collection.name)
            if collection.bundles == []:
                collection.populate_bundles()
            self.bundles += collection.bundles

    def populate_files(self, hardlimit=10000):
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
        with open(f"tla_copy{add}.json", "w", encoding="utf8") as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))

    def insert_into_database(self, db_name="test.db"):
        insert_file_list = []
        insert_language_list = []
        found_ids = {}
        with open("tla_copy_f.json", encoding="utf8") as json_in:
            d = json.load(json_in)
        for collection_name, collection_d in d.items():
            collection_has_duplicates = False
            for bundle_name, bundle_d in collection_d["bundles"].items():
                for f in bundle_d["files"]:
                    id_ = f["url"].split("/")[-1].strip().replace("%3A", ":")
                    if not id_:
                        continue
                    type_ = f["type_"]
                    megatype = type2megatype(type_)
                    size = tla_sizes.get(id_, 0)
                    length = 0
                    if found_ids.get(id_):
                        if found_ids[id_] > 1:
                            collection_has_duplicates = True
                        found_ids[id_] += 1
                        continue
                    found_ids[id_] = 1
                    insert_file_tuple = (
                        id_,
                        "TLA",
                        collection_name,
                        bundle_name,
                        type_,
                        megatype,
                        size,
                        length,
                    )
                    insert_file_list.append(insert_file_tuple)
                    try:
                        languages = f["languages"][0].split("\n")
                    except IndexError:
                        languages = []
                    for language in languages:
                        try:
                            iso6393 = language_dictionary[language]["iso6393"]
                        except KeyError:
                            iso6393 = ""
                        insert_language_tuple = (id_, "TLA", iso6393)
                        insert_language_list.append(insert_language_tuple)
            if collection_has_duplicates:
                print(f"{collection_name} has duplicates:", end="\n    ")
                print(
                    ",".join(
                        [id_ for id_, occurences in found_ids.items() if occurences > 1]
                    )
                )
                found_ids = {}
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()
        for f in insert_file_list:
            try:
                cursor.execute("INSERT INTO files VALUES(?,?,?,?,?,?,?,?)", f)
            except sqlite3.IntegrityError:
                print(f"skipping {f} as the ID is already present in the database")
        for l in insert_language_list:
            try:
                cursor.execute("INSERT INTO languagesfiles VALUES(?,?,?)", l)
            except sqlite3.IntegrityError:
                print(
                    f"skipping {l} as this combination is already present in the database"
                )
        connection.commit()
        connection.close()


if __name__ == "__main__":
    ta = TLAArchive()
    ta.insert_into_database()
