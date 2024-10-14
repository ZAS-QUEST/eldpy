"""
instances of Pacific and Regional Archive for Digital Sources in Endangered Cultures
"""
# import re
# import urllib
# import pprint
import sqlite3
# from collections import Counter, defaultdict
import json
from bs4 import BeautifulSoup
import requests
# import humanize

from paradisec_collection import ParadisecCollection
from helpers import type2megatype
# from paradisec_bundle import ParadisecBundle
# from paradisec_file import ParadisecFile
from archive import Archive

class ParadisecArchive(Archive):
    """
    an instance of Pacific and Regional Archive for Digital Sources in Endangered Cultures
    """

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []
        self.name = "PARADISEC"

    def populate_collections(self, hardlimit=1000):
        """
        get all PARADISEC collections
        """
        r = requests.get(
            f"https://catalog.paradisec.org.au/collections/search?page=1&per_page={hardlimit}",
            timeout=120
        )
        content = r.content
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find_all("table")[-1]
        trs = table.find_all("tr")
        for i, tr in enumerate(trs):
            print(f"{i}/{len(trs)}")
            tds = tr.find_all("td")
            collection_name = tds[1].text
            collection_link = (
                "https://catalog.paradisec.org.au" + tds[7].find("a")["href"]
            )
            self.collections.append(
                ParadisecCollection(collection_name, collection_link)
            )

    def populate_bundles(self):
        """
        get all bundles for the collections
        """
        print("populating bundles")
        for i, collection in enumerate(self.collections):
            print(f"{i}/{len(self.collections)} {collection.name}")
            if collection.bundles == []:
                collection.populate_bundles()
            self.bundles += collection.bundles

    def populate_files(self, writeout=False):
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
            filename = collection.url.split("/collections/")[-1]
            collection_dict = {
                "name": collection.name,
                "url": collection.url,
                "bundles": {},
            }
            if writeout:
                for bundle in collection.bundles:
                    bundle_dict = {
                        "name": bundle.name,
                        "url": bundle.url,
                        "files": [file_.__dict__ for file_ in bundle.files],
                        "languages": bundle.languages,
                    }
                    collection_dict["bundles"][bundle.name] = bundle_dict
                with open(f"paradisecjson/{filename}.json", "w", encoding='utf8') as jsonout:
                    jsonout.write(json.dumps(collection_dict, indent=4, sort_keys=True))

    # def run(self):
    #     self.populate_collections()
    #     # self.write_json(add='_c')
    #     with open("paradisec_copy_b.json") as jin:
    #         s = jin.read()
    #     j = json.loads(s)
    #     for c_in in j:
    #         c_temp = ParadisecCollection(j[c_in]["name"], j[c_in]["url"])
    #         id_ = j[c_in]["url"].split("/")[-1]
    #         #     print(id_)
    #         #     with open(f"paradisecjson/{id_}.json") as bundle_in:
    #         #         s2 = bundle_in.read()
    #         #     j2 = json.loads(s2)
    #         #     for bundle in j2['bundles']:
    #         #         name = j2['bundles'][bundle]['name']
    #         #         url = j2['bundles'][bundle]['url']
    #         #         languages = j2['bundles'][bundle]['languages']
    #         #         b = ParadisecBundle(name, url, languages)
    #         #         files = []
    #         #         for f in j2['bundles'][name]['files']:
    #         #             name = f['name']
    #         #             url = f['url']
    #         #             type_ = f['type_']
    #         #             duration = f['duration']
    #         #             size = f"{f['size']}B"
    #         #             if "\n" in name:
    #         #                 continue
    #         #             files.append(ParadisecFile(name, url, type_, size, duration))
    #         #         b.files = files
    #         #         c_temp.bundles.append(b)
    #         self.collections.append(c_temp)
    #     # self.collections = self.collections[:4]
    #     print(f"found {len(self.collections)} collections")
    #     self.populate_bundles()
    #     self.write_json(add="_b")
    #     self.populate_files(writeout=True)
    #     self.write_json(add="_f")

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
        with open(f"paradisec_copy{add}.json", "w", encoding='utf8') as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))

    def get_id(self, f):
        id_ = f["name"]
        if " files" in id_:
            return None
        if not id_:
            return None
        return id_

    def get_megatype(self, type_):
        try:
            tmptype = type_.split("/")[1]
            megatype = type2megatype(tmptype)
        except IndexError:
            megatype = ''
        return megatype

    def get_type(self, type_):
        return type_.split("/")[1]

    def get_length(self, f):
        duration = f.get("duration", "").strip()
        if duration in ("", "--"):
            length = 0
        else:
            h, m, s = duration.split(":")
            length = float(s) + 60 * int(m) + 60 * 60 * int(h)
        return length





if __name__ == "__main__":
    pa = ParadisecArchive()
    pa.insert_into_database("paradisec_copy_f.json")
