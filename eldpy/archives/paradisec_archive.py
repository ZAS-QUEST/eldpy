"""
instances of Pacific and Regional Archive for Digital Sources in Endangered Cultures
"""
# import re
# import urllib
import pprint
import sqlite3
import sys
# from collections import Counter, defaultdict
import json
from bs4 import BeautifulSoup
import requests
# import humanize
from eldpy import delaman


from eldpy.archives.paradisec_collection import ParadisecCollection
from eldpy.helpers import type2megatype
# from paradisec_bundle import ParadisecBundle
# from paradisec_file import ParadisecFile
from eldpy.archives.archive import Archive, LIMIT

class ParadisecArchive(Archive):
    """
    an instance of Pacific and Regional Archive for Digital Sources in Endangered Cultures
    """

    def __init__(self):
        super().__init__("PARADISEC", "https://catalog.paradisec.org.au")

    def populate_collections(self, limit=LIMIT):
        """
        get all PARADISEC collections
        """
        request_url = f"https://catalog.paradisec.org.au/collections/search?page=1&per_page={limit}"
        print(request_url)
        r = requests.get(
            request_url,
            timeout=120
        )
        content = r.content
        soup = BeautifulSoup(content, "html.parser")
        table = soup.find_all("table")[-1]
        trs = table.find_all("tr")
        print(len(trs))
        for i, tr in enumerate(trs[:limit]):
            tds = tr.find_all("td")
            collection_name = tds[1].text
            print(i,collection_name)
            link_base = tds[8].find("a")["href"]
            print(link_base)
            collection_link = (
                "https://catalog.paradisec.org.au" + link_base
            )
            self.collections.append(
                ParadisecCollection(collection_name, collection_link)
            )

    def populate_bundles(self, limit=LIMIT, offset=0):
        """
        get all bundles for the collections
        """
        print("populating bundles")
        for i, collection in enumerate(self.collections):
            print(f"{i}/{len(self.collections)} {collection.name}")
            if collection.bundles == []:
                collection.populate_bundles()
            self.bundles += collection.bundles

    def populate_files(self, limit=LIMIT):
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
            # filename = collection.url.split("/collections/")[-1]
            # collection_dict = {
            #     "name": collection.name,
            #     "url": collection.url,
            #     "bundles": {},
            # }
            # writeout=False
            # if writeout:
            #     for bundle in collection.bundles:
            #         bundle_dict = {
            #             "name": bundle.name,
            #             "url": bundle.url,
            #             "files": [file_.__dict__ for file_ in bundle.files],
            #             "languages": bundle.languages,
            #         }
            #         collection_dict["bundles"][bundle.name] = bundle_dict
            #     with open(f"paradisecjson/{filename}.json", "w", encoding='utf8') as jsonout:
            #         jsonout.write(json.dumps(collection_dict, indent=4, sort_keys=True))

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

    # def write_json(self, add=""):
    #     """
    #     write out the archive metadata as json
    #     """
    #     archive_dict = {}
    #     for collection in self.collections:
    #         collection_dict = {
    #             "name": collection.name,
    #             "url": collection.url,
    #             "bundles": {},
    #         }
    #         for bundle in collection.bundles:
    #             bundle_dict = {
    #                 "name": bundle.name,
    #                 "url": bundle.url,
    #                 "files": [file_.__dict__ for file_ in bundle.files],
    #                 "languages": bundle.languages,
    #             }
    #             collection_dict["bundles"][bundle.name] = bundle_dict
    #         archive_dict[collection.name] = collection_dict
    #     with open(f"paradisec_copy{add}.json", "w", encoding='utf8') as jsonout:
    #         jsonout.write(json.dumps(archive_dict, indent=4, sort_keys=True))



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


    def open_session(self, password):
        login_url = 'https://catalog.paradisec.org.au/users/sign_in'
        print(f"Logging in to {login_url}")
        session = requests.Session()
        login_page = session.get(login_url)
        soup = BeautifulSoup(login_page.text, "html.parser")
        token = soup.find("input", {"name": "authenticity_token"})["value"]
        print("Retrieved authentication token")
        response = session.post('https://catalog.paradisec.org.au/users/sign_in',data= {'user[email]':'nordhoff@bbaw.de', 'user[password]': password, 'authenticity_token':token, 'user[remember_me]':'0', 'commit':'Log+in'} )
        return session



    def fetch_one_page(self, session, page=1, graphql_url='https://catalog.paradisec.org.au/graphql', limit=100):
        query_template = """
            query {
            items(limit: %s, page: %d) {
                total
                next_page
                results {
                full_identifier
                title
                collection {
                    identifier
                }
                content_languages {
                    code
                }
                doi
                essences {
                    id
                    filename
                    size
                    duration
                }
                }
            }
            }
            """

        query = query_template % (limit, page)
        response = session.post(
            graphql_url,
            json={"query": query}
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise RuntimeError(data["errors"])
        items = data["data"]["items"]
        results = items["results"]
        next_page = items["next_page"]
        return results, next_page

    def fetch_all_items(self, session, graphql_url = 'https://catalog.paradisec.org.au/graphql', limit=100):
        page = 1
        all_results = []
        while True:
            print(page)
            results, next_page = self.fetch_one_page(session, page=page)
            # collect results
            all_results.extend(results)
            if not next_page:
                break
            page = next_page
        return all_results

    def insert_into_database(self, input_file, db_name="test.db"):
        insert_file_list = []
        insert_language_list = []
        with open(input_file, encoding="utf8") as json_in:
            items = json.load(json_in)
        for item in items:
            collection_id = item['collection']['identifier']
            bundle_id = item['full_identifier']
            languages = [x['code'] for x in item['content_languages']]
            files = []
            for e in item['essences']:
                id_ = e['id']
                size = e['size']
                duration = e['duration']
                filename = e['filename']
                extension = filename.split('.')[-1]
                type_ = ''
                if extension in ('mpg','mp4','mkv', 'mxf', 'webm', 'm4v','mov', 'dv', 'MP4', 'mts', 'avi', 'MTS'):
                    type_ = 'video'
                elif extension in ('mp3','wav'):
                    type_ = 'audio'
                elif extension in ('eaf','xml','flextext', 'annis'):
                    type_ = 'xml'
                elif extension in ('jpg','png','tiff','tif','odt', 'trs','JPG', 'img'):
                    type_ = 'image'
                elif extension in ('doc','docx', 'txt','srt','pdf','rtf','TextGrid', 'cha', 'html', 'PDF', 'tex'):
                    type_ = 'text'
                elif extension in ('zip','opex','imdi', 'xlsx', 'version', 'csv', 'ods', 'cmdi', 'lbl', 'fwbackup', 'tab', 'kml', 'pfsx', 'ixt'):
                    type_ = 'other'
                else:
                    print(f'unknown extension: {extension}')
                megatype = self.get_megatype(type_)
                insert_file_tuple = (
                    id_,
                    'PARADISEC',
                    collection_id,
                    bundle_id,
                    megatype,
                    type_,
                    size,
                    duration,
                )
                insert_file_list.append(insert_file_tuple)
                for language in self.get_languages(languages):
                    insert_language_tuple = (id_, 'PARADISEC', language)
                    insert_language_list.append(insert_language_tuple)
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()
        print(f"{len(insert_file_list)} to be inserted")
        try:
            cursor.executemany(
                "INSERT INTO files VALUES(?,?,?,?,?,?,?,?)", set(insert_file_list)
            )
        except ValueError:
            pass
        try:
            cursor.executemany(
                "INSERT INTO languagesfiles VALUES(?,?,?)", set(insert_language_list)
            )
        except ValueError:
                pass
        connection.commit()
        connection.close()


if __name__ == "__main__":
    pa = ParadisecArchive()
    # pa.populate_collections()
    # pa.populate_bundles()
    # pa.populate_files()
    # pa.write_json(add="_f")
    # password = sys.argv[1]
    # session = pa.open_session(password)
    # results = pa.fetch_one_page(session)[0]
    # results = pa.fetch_all_items(session)
    # with open('paradisec.json', 'w') as jsonout:
    #     jsonout.write(json.dumps(results, indent=4, ensure_ascii=False))
    # delaman.setup_metadata_database(db_name='paradisec.db')
    pa.insert_into_database("paradisec.json", db_name="delaman2025a.db")

    # pa.insert_into_database("paradisec_copy.json", db_name="delaman2025a.db")


