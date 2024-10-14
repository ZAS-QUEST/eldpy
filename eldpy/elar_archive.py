import re
import urllib
import pprint
import json
import humanize

from collections import Counter, defaultdict
from bs4 import BeautifulSoup

from elar_collection import  ElarCollection
from elar_bundle import  ElarBundle
from elar_file import  ElarFile


class ElarArchive:
    # FILETYPES = {
    #     "ELAN": "text/x-eaf+xml",
    #     "Toolbox": "text/x-toolbox-text",
    #     "transcriber": "text/x-trs",
    #     "praat": "text/praat-textgrid",
    #     "Flex": "FLEx",
    # }

    def __init__(self):
        self.collections = []
        self.bundles = []
        self.files = []

    def populate_collections(self, pagelimit=50, hardlimit=10000):
        print("populating collections")
        self.collections = self.get_elar_collections(pagelimit=pagelimit, hardlimit=hardlimit)

    def populate_bundles(self, hardlimit=10000, languages=True):
        print("populating bundles")
        for collection in self.collections:
            print(collection.name)
            if collection.bundles == []:
                collection.populate_bundles(hardlimit=hardlimit, languages=True)
            self.bundles += collection.bundles

    def populate_files(self,hardlimit=10000):
        print(f"populating files from {len(self.collections)} collections")
        for i, collection in enumerate(self.collections):
            print(f"{i+1}/{len(self.collections)}")
            if collection.bundles == []:
                collection.populate_bundles()
            for bundle in collection.bundles:
                if bundle.files == []:
                    bundle.populate_files(hardlimit=hardlimit)
                self.files += bundle.files

    def get_elar_collections(self, pagelimit=40, hardlimit=10000):
        collections = []
        for i in range(pagelimit):
            catalogpage = f'https://www.elararchive.org/uncategorized/SO_5f038640-311d-4296-a3e9-502e8a18f5b7/?pg={i}'
            print(f"reading {catalogpage}")
            try:
                with urllib.request.urlopen(catalogpage) as catalog_reader:
                    content = catalog_reader.read()
                    new_collection_links = self.get_elar_collection_links_(content)
                    print(f" found {len(new_collection_links)} collections")
                    collections += new_collection_links
            except urllib.error.HTTPError:
                print(f"could not download {catalogpage}")
        if len(collections) >= hardlimit:
            collections = collections[:hardlimit]
        print(f"finished. There are {len(collections)} collections")
        return collections

    def get_elar_collection_links_(self, page):
        soup = BeautifulSoup(page, 'html.parser')
        collection_links = [ElarCollection(a.text, a['href']) for h5 in soup.find_all('h5') for a in h5.find_all('a')]
        return collection_links
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
        with open(f'elar_copy{add}.json', 'w') as jsonout:
            jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))




    def run(self):
        self.populate_collections(pagelimit=30)
        self.write_json(add='_c')
        self.populate_bundles()
        self.write_json(add='_b')
        self.populate_files()
        self.write_json(add='_f')



    def json_run_bundle(self):
        with open("elar_copy_b.json") as json_in:
            d = json.load(json_in)
        for collection_name, collection_d in d.items():
            collection_url = collection_d['url']
            c = ElarCollection(collection_name, collection_url)
            collection_bundles = []
            for bundle_name, bundle_d in collection_d['bundles'].items():
                bundle_url = bundle_d['url']
                b = ElarBundle(bundle_name, bundle_url)
                collection_bundles.append(b)
            c.bundles = collection_bundles
            self.collections.append(c)
        self.populate_files()
        self.write_json(add='_f')

    def json_run_showcase(self,file_limit=999999):
        with open("showcase_elar_copy_f.json") as json_in:
            d = json.load(json_in)
        i = 0
        for collection_name, collection_d in d.items():
            i+=1
            if i>5:
                break
            collection_url = collection_d['url']
            c = ElarCollection(collection_name, collection_url)
            collection_bundles = []
            for bundle_name, bundle_d in collection_d['bundles'].items():
                bundle_url = bundle_d['url']
                b = ElarBundle(bundle_name, bundle_url)
                bundle_files = []
                for file_d in bundle_d['files'][:file_limit]:
                    file_name = file_d['name']
                    file_url = file_d['url']
                    file_type = file_d['type_']
                    f = ElarFile(file_name, file_url, file_type)
                    f.get_size()
                    bundle_files.append(f)
                b.files = bundle_files
                collection_bundles.append(b)
            c.bundles = collection_bundles
        self.collections.append(c)
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


    def run_languages(self,file_limit=999999):
        self.populate_collections()
        self.populate_bundles(languages=True)
        self.write_json(add='_b')
        self.report()

    def insert_into_database(self, db_name='test.db'):
        insert_file_list = []
        insert_language_list = []
        found_ids = {}
        with open("tla_copy_f.json") as json_in:
            d = json.load(json_in)
        for collection_name, collection_d in d.items():
            collection_has_duplicates = False
            for bundle_name, bundle_d in collection_d['bundles'].items():
                for f in bundle_d['files']:
                    id_ = f['url'].split('/')[-1].strip().replace('%3A',':')
                    if not id_:
                        continue
                    type_ = f['type_']
                    megatype = type2megatype(type_)
                    size = tla_sizes.get(id_, 0)
                    length = 0
                    if found_ids.get(id_):
                        if found_ids[id_] > 1:
                            collection_has_duplicates = True
                        found_ids[id_] += 1
                        continue
                    found_ids[id_] = 1
                    insert_file_tuple = (id_, "TLA", collection_name, bundle_name, type_, megatype,size,length)
                    insert_file_list.append(insert_file_tuple)
                    try:
                        languages = f['languages'][0].split('\n')
                    except IndexError:
                        languages  = []
                    for language in languages:
                        try:
                            iso6393 = language_dictionary[language]['iso6393']
                        except KeyError:
                            # print(f"{language} not found in language dictionary")
                            iso6393 = ''
                        insert_language_tuple = (id_,"TLA",iso6393)
                        insert_language_list.append(insert_language_tuple)
            if collection_has_duplicates:
                print(f"{collection_name} has duplicates:", end="\n    ")
                print(','.join([id_ for id_ in found_ids if found_ids[id_]>1]))
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
                print(f"skipping {l} as this combination is already present in the database")
        connection.commit()
        connection.close()



if __name__ == "__main__":
    ea = ElarArchive()
    ea.insert_into_database()
