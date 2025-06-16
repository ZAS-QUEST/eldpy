"""
instances of Pacific and Regional Archive for Digital Sources in Endangered Cultures
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
from archive import Archive
# from ailla_bundle import AillaBundle

# from ailla_file import  AillaFile


class AillaArchive(Archive):
    """
    An instance of the Archive of the Indigenous Languages of Latin America
    """

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []
        self.name = "AILLA"

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
        print(f"found {len(collection_list)} collections")

    # def populate_bundles(self, hardlimit=10000):
    #     """
    #     get all bundles for the collections
    #     """
    #
    #     print("populating bundles")
    #     for collection in self.collections:
    #         print(collection.name)
    #         if collection.bundles == []:
    #             collection.populate_bundles(hardlimit=hardlimit)
    #         self.bundles += collection.bundles

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

    def get_megatype(self, type_):
        return type_

    def get_length(self, f):
        return 0

    def get_id(self, f):
        return f["url"].split("/")[-4].strip()


if __name__ == "__main__":
    aa = AillaArchive()
    aa.populate()
    # aa.populate_collections()
    # aa.populate_bundles()
    # aa.populate_files()
    aa.write_json()
    # aa.insert_into_database("ailla_copy_f.json")
