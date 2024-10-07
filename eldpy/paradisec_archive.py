import re
import urllib
import pprint
import json
import sqlite3
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
        for i,tr in enumerate(trs):
            print(f"{i}/{len(trs)}")
            tds = tr.find_all('td')
            collection_name = tds[1].text
            collection_link = "https://catalog.paradisec.org.au" + tds[7].find('a')['href']
            self.collections.append(ParadisecCollection(collection_name, collection_link))

    def populate_bundles(self, hardlimit=10000):
        print("populating bundles")
        for i, collection in enumerate(self.collections):
            print(f"{i}/{len(self.collections)} {collection.name}")
            if collection.bundles == []:
                collection.populate_bundles()
            self.bundles += collection.bundles

    def populate_files(self,hardlimit=10000,writeout=False):
        print(f"populating files from {len(self.collections)} collections")
        for i, collection in enumerate(self.collections):
            print(f"{i+1}/{len(self.collections)}")
            if collection.bundles == []:
                collection.populate_bundles()
            for bundle in collection.bundles:
                if bundle.files == []:
                    bundle.populate_files()
                self.files += bundle.files
            filename = collection.url.split('/collections/')[-1]
            collection_dict = {'name':collection.name, 'url':collection.url,'bundles':{}}
            if writeout:
                for bundle in collection.bundles:
                    bundle_dict = {
                        'name'  : bundle.name,
                        'url' : bundle.url,
                        'files' : [file_.__dict__ for file_ in bundle.files],
                        'languages' : bundle.languages,
                    }
                    collection_dict['bundles'][bundle.name] = bundle_dict
                with open(f"paradisecjson/{filename}.json", "w") as jsonout:
                    jsonout.write(json.dumps(collection_dict, indent=4, sort_keys=True))




    def run(self):
        self.populate_collections()
        # self.write_json(add='_c')
        with  open("paradisec_copy_b.json") as jin:
            s = jin.read()
        j =json.loads(s)
        for c_in in j:
            c_temp = ParadisecCollection(j[c_in]['name'], j[c_in]['url'])
            id_ = j[c_in]['url'].split('/')[-1]
        #     print(id_)
        #     with open(f"paradisecjson/{id_}.json") as bundle_in:
        #         s2 = bundle_in.read()
        #     j2 = json.loads(s2)
        #     for bundle in j2['bundles']:
        #         name = j2['bundles'][bundle]['name']
        #         url = j2['bundles'][bundle]['url']
        #         languages = j2['bundles'][bundle]['languages']
        #         b = ParadisecBundle(name, url, languages)
        #         files = []
        #         for f in j2['bundles'][name]['files']:
        #             name = f['name']
        #             url = f['url']
        #             type_ = f['type_']
        #             duration = f['duration']
        #             size = f"{f['size']}B"
        #             if "\n" in name:
        #                 continue
        #             files.append(ParadisecFile(name, url, type_, size, duration))
        #         b.files = files
        #         c_temp.bundles.append(b)
            self.collections.append(c_temp)
        # self.collections = self.collections[:4]
        print(f"found {len(self.collections)} collections")
        self.populate_bundles()
        self.write_json(add='_b')
        self.populate_files(writeout=True)
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



    def insert_into_database(self, db_name='test.db'):
        insert_file_list = []
        insert_language_list = []
        found_ids = {}
        with open("paradisec_copy_f.json") as json_in:
            d = json.load(json_in)
        for collection_name, collection_d in d.items():
            collection_has_duplicates = False
            for bundle_name, bundle_d in collection_d['bundles'].items():
                for f in bundle_d['files']:
                    id_ = f['name']
                    if " files" in id_:
                        continue
                    if not id_:
                        continue
                    type_ = f['type_']
                    try:
                        megatype, tmptype = type_.split('/')
                        if tmptype == 'pfsx+xml':
                            continue
                        if tmptype == 'flextext+xml':
                            megatype = 'xml'
                        if tmptype == 'eaf+xml':
                            megatype = 'xml'
                        if tmptype == 'pdf':
                            megatype = 'text'
                        if tmptype == 'x-iso9660-image':
                            megatype = 'image'
                        if tmptype == 'pdf':
                            megatype = 'text'
                        if tmptype == 'vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                            continue
                        if tmptype == 'vnd.oasis.opendocument.spreadsheet':
                            continue
                        if tmptype == 'vnd.openxmlformats-officedocument.wordprocessingml.document':
                            megatype = 'text'
                        if tmptype == 'vnd.oasis.opendocument.text':
                            megatype = 'text'
                        if tmptype == 'mxf':
                            megatype = 'video'
                    except IndexError:
                        megatype = None
                    size = f['size']
                    duration = f.get('duration','').strip()
                    if duration in ('', '--'):
                        length = 0
                    else:
                        h, m, s = duration.split(':')
                        length = float(s) + 60*int(m) +60*60*int(h)
                    if found_ids.get(id_):
                        if found_ids[id_] > 1:
                            collection_has_duplicates = True
                        found_ids[id_] += 1
                        continue
                    found_ids[id_] = 1
                    insert_file_tuple = (id_, "Paradisec", collection_name, bundle_name, megatype, type_, size, length)
                    insert_file_list.append(insert_file_tuple)
                    for language in f['languages']:
                        insert_language_tuple = (id_,"Paradisec",language)
                        insert_language_list.append(insert_language_tuple)
            if collection_has_duplicates:
                print(f"{collection_name} has duplicates:", end="\n    ")
                print(','.join([id_.strip() for id_ in found_ids if found_ids[id_]>1]))
                found_ids = {}
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()
        cursor.executemany("INSERT INTO files VALUES(?,?,?,?,?,?,?,?)", insert_file_list)
        cursor.executemany("INSERT INTO languagesfiles VALUES(?,?,?)", set(insert_language_list))
        connection.commit()
        connection.close()


if __name__ == "__main__":
    pa = ParadisecArchive()
    pa.insert_into_database()



