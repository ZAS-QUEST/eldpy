"""
instances of the Archive of the Indigenous Languages of Latin America
"""

import json
import sqlite3

# import re
# import urllib
import pprint

# import humanize
import requests

# from collections import Counter, defaultdict
# from bs4 import BeautifulSoup

from ailla_collection import AillaCollection

# from ailla_bundle import AillaBundle

# from ailla_file import  AillaFile


class AillaArchive:
    """
    An instance of the Archive of the Indigenous Languages of Latin America
    """

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []

    def populate_collections(self, hardlimit=10000):
        """
        get all AILLA collections
        """

        print("populating AILLA collections")
        r = requests.get(
            "https://ailla-backend-prod.gsc1-pub.lib.utexas.edu/collections/all",
            timeout=120,
        )
        collection_list = json.loads(r.content)[:hardlimit]
        for collection in collection_list:
            id_ = collection["id"]
            url = f"https://ailla.utexas.org/collections/{id_}"
            name = collection["title"]["en"]
            self.collections.append(AillaCollection(name, url))

    def populate_bundles(self, hardlimit=10000):
        """
        get all bundles for the collections
        """

        print("populating bundles")
        for collection in self.collections:
            print(collection.name)
            if collection.bundles == []:
                collection.populate_bundles(hardlimit=hardlimit)
            self.bundles += collection.bundles

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
                }
                collection_dict["bundles"][bundle.name] = bundle_dict
            archive_dict[collection.name] = collection_dict
        with open(f"ailla_copy{add}.json", "w", encoding="utf8") as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))

    # def json_run_showcase(self, file_limit=999999):
    #     with open("showcase_ailla_copy_b.json") as json_in:
    #         d = json.load(json_in)
    #     for collection_name, collection_d in d.items():
    #         collection_url = collection_d["url"]
    #         c = AillaCollection(collection_name, collection_url)
    #         collection_bundles = []
    #         for bundle_name, bundle_d in collection_d["bundles"].items():
    #             bundle_url = bundle_d["url"]
    #             bundle_id = bundle_url.split("/")[-1]
    #             b = AillaBundle(bundle_name, bundle_id)
    #             b.populate_files()
    #             collection_bundles.append(b)
    #         c.bundles = collection_bundles
    #         print(f" There are {len(c.bundles)} bundles")
    #         self.collections.append(c)
    #     self.write_json(add="_f")
    #     self.report()

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
    #         print(f" {k} files: {v} ({readable_size} total)")

    def insert_into_database(self, db_name="test.db"):
        """
        read the json file and insert it into a sqlite3 database
        """

        insert_file_list = []
        insert_language_list = []
        found_ids = {}
        with open("ailla_copy_f.json", encoding="utf8") as json_in:
            d = json.load(json_in)
        for collection_name, collection_d in d.items():
            collection_has_duplicates = False
            for bundle_name, bundle_d in collection_d["bundles"].items():
                for f in bundle_d["files"]:
                    id_ = f["url"].split("/")[-4].strip()
                    if not id_:
                        continue
                    type_ = f["type_"]
                    size = f["size"]
                    length = 0
                    if found_ids.get(id_):
                        if found_ids[id_] > 1:
                            collection_has_duplicates = True
                        found_ids[id_] += 1
                        continue
                    found_ids[id_] = 1
                    insert_file_tuple = (
                        id_,
                        "AILLA",
                        collection_name,
                        bundle_name,
                        type_,
                        type_,
                        size,
                        length,
                    )
                    insert_file_list.append(insert_file_tuple)
                    for language in f["languages"]:
                        insert_language_tuple = (id_, "AILLA", language)
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
        cursor.executemany(
            "INSERT INTO files VALUES(?,?,?,?,?,?,?,?)", insert_file_list
        )
        cursor.executemany(
            "INSERT INTO languagesfiles VALUES(?,?,?)", set(insert_language_list)
        )
        connection.commit()
        connection.close()


if __name__ == "__main__":
    aa = AillaArchive()
    aa.insert_into_database()
