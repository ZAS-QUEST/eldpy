"""
instances of The Endangered Language Archive
"""
import os
# import re
# import urllib
# import pprint
import json
# import csv
import logging
import time
# import pprint

# from collections import Counter, defaultdict
import sqlite3
# from pathlib import Path
from bs4 import BeautifulSoup

# import humanize
import requests
from dotenv import load_dotenv

from pyPreservica.common import ReferenceNotFoundException
from pypreservica_api_wrapper import PreservicaAPIWrapper

from eldpy.archives.archive import Archive, DEBUG, LIMIT

from eldpy.archives.elar_collection import  ElarCollection

from eldpy.archives.elar_file import ElarFile

from eldpy.helpers import get_seconds, type2megatype
from eldpy.language_metadata import language_dictionary

from itertools import tee
# from datetime import timedelta, date
# from elar_bundle import  ElarBundle
# from elar_file import  ElarFile

logging.basicConfig(level=logging.INFO)

class ElarArchive(Archive):

    """
    instances of The Endangered Language Archive
    """

    def __init__(self):
        super().__init__("ELAR", "https://www.elararchive.org/")
        self.ingested_collections = []
        self.collections_with_errors = []

    def populate_collections(self, limit=LIMIT, pagelimit=40):
        print("populating collections")
        self.collections = self.get_elar_collections(pagelimit=pagelimit, limit=limit)

    def populate_bundles(self, limit=LIMIT, offset=0, languages=True):
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



    def populate_database(self, given_db_name="test.db", offset=0, limit=99999, fussy=False):
        """crawl the ELAR archive via the Preservica API and add the metadata to the db"""

        connection = sqlite3.connect(given_db_name)
        # collections_with_errors = []
        # ingested_collections = []
        self.retrieve_collections(connection, offset=offset, limit=limit, fussy=fussy)
        print("The following collections could not be ingested:", self.collections_with_errors)
        connection.close()


    def retrieve_collections(self, connection, offset=0, limit=99999, fussy=True):
        """retrieve collection medata from ELAR and add it to the db"""
        cursor = connection.cursor()
        load_dotenv()
        load_dotenv(dotenv_path=os.environ["ENV_PATH"])

        client = PreservicaAPIWrapper()

        # the * is used to filter for existing values, "" retrieves all records
        collection_filter_values = {
            "imdi.country": "",
            "imdi.language": "",
            "imdi.corpusTitle": "",
            "xip.title": "",
            "xip.parent_ref": os.environ["PRESERVICA_ROOT_FOLDER_ID"],
        }

        #     # now go through all hits
        print("retrieving collections")
        raw_hits = client.content_client.search_index_filter_list(
            query="*", filter_values=collection_filter_values
        )
        print("fetching all hits into memory", end=" ")
        hits = [x for x in raw_hits]
        print(f"({len(hits)} hits)")
        limit = min(limit, len(hits))
        i = offset
        try:
            for current_hit in hits[offset:]:
                i += 1
                if i > limit:
                    break
                print(f"{i}/{limit}:", end=" ")
                current_collection_folder = client.entity_client.folder(
                    current_hit["xip.reference"]
                )
                collection_folder = self.process_collection(current_hit, current_collection_folder, client, cursor, fussy=fussy)
                if collection_folder:
                    self.ingested_collections.append(collection_folder)
                    connection.commit()
                    print("Added to database")
        except RuntimeError as e:
            self.collections_with_errors.append((i,current_collection_folder))
            print()
            print(e)
            print("Server connection dropped. Proceeding to next collection")
            self.retrieve_collections(connection,offset=i,fussy=fussy)
        except sqlite3.IntegrityError as e:
            connection.rollback()
            self.collections_with_errors.append((i,current_collection_folder))
            print()
            print(e)
            print("Database problem. Proceeding to next collection")
            self.retrieve_collections(connection,offset=i,fussy=fussy)
        except ReferenceNotFoundException as e:
            connection.rollback()
            self.collections_with_errors.append((i,current_collection_folder))
            print()
            print(e)
            print("Archive problem. Proceeding to next collection")
            self.retrieve_collections(connection,offset=i,fussy=fussy)



    def process_collection(self, hit, collection_folder, client, cursor, fussy=True):
        """process one ELAR collection and add the metadata to the database"""
        # print("processing")

        # collection_countries = set()
        collection_languages = set()

        collection_title = hit.get("imdi.corpusTitle", "_NO_TITLE")
        print(f"now in {collection_folder.title}")

        # collection_countries.add(hit.get("imdi.country"))
        collection_languages.update(hit.get("imdi.language", []))

        # find the folders with the collection folder as parent
        session_filter_values = {
            "imdi.country": "",
            "imdi.sessionTitle": "",
            "imdi.language": "",
            "xip.security_descriptor": "*",
            "xip.parent_ref": collection_folder.reference,
        }

        collection_ref = collection_folder.reference
        cursor.execute(
            f'select * from files where archive="ELAR" and collection="{collection_ref}"'
        )
        files_for_collection = cursor.fetchall()
        if len(files_for_collection) > 0:
            cursor.execute(
                f'select distinct(bundle) from files where archive="ELAR" and collection="{collection_ref}"'
            )
            bundles = cursor.fetchall()
            # print(f"collection {collection_ref} already in database ({len(files_for_collection)} files in {len(bundles)} sessions). Skipping.")
            return False
        # now go through all hits
        raw_session_hits = client.content_client.search_index_filter_list(
            query="*", filter_values=session_filter_values
        )
        print(" fetching session hits. ", end="", flush=True)
        try:
            session_hits = [x for x in raw_session_hits]
        except RuntimeError:
            time.sleep(3)
            session_hits = [x for x in raw_session_hits]
        print(
            f"Analyzing {len(session_hits)} sessions. Numbers indicate the number of files fetched per session",
            end="\n ",
        )
        collection_files_db = []
        languages_db = []
        for current_session_hit in session_hits:
            # pprint.pprint(current_session_hit)
            session_ref = current_session_hit["xip.reference"]
            # short_title = current_session_hit.get("imdi.sessionTitle", "")[:50]
            # print(f" processing {file_ref} {short_title}")
            if fussy:
                elar_files = self.process_session_hit(current_session_hit, client)
            else:
                try:
                    elar_files = self.process_session_hit(current_session_hit, client)
                except pyPreservica.common.ReferenceNotFoundException as e:
                    print(
                        f"Archive problem while fetching files for  {session_ref} in {collection_ref}. Skipping"
                    )
                    print(e)
                    continue
            if not elar_files:
                continue
            for elar_file in elar_files:
                elar_file.megatype = type2megatype(elar_file.type_)
                file_ref = elar_file.id_
                file_data = [
                    file_ref,
                    "ELAR",
                    collection_ref,
                    session_ref,
                    elar_file.megatype,
                    elar_file.type_,
                    elar_file.size,
                    elar_file.duration,
                ]
                # print(file_data)
                collection_files_db.append(file_data)
                for language in elar_file.languages:
                    try:
                        iso6393 = language_dictionary[language]["iso6393"]
                    except KeyError:
                        iso6393 = f"_{language}"
                    language_data = (file_ref, "ELAR", iso6393)
                    languages_db.append(language_data)
        for c in collection_files_db:
            # print(c)
            cursor.execute("INSERT INTO files VALUES (?,?,?,?,?,?,?,?)", c)
        for l in list(set(languages_db)):
            # print(l)
            cursor.execute(
                "INSERT INTO languagesfiles VALUES (?,?,?)",
                l,
            )
        print()
        return collection_folder


    def process_session_hit(self, session_hit, client):
        """ extract the metadata for one session"""

        # session_countries = set()
        session_languages = set()
        # we only want published Sessions
        # session_sec_desc_set = set(session_hit["xip.security_descriptor"])
        session_folder = client.entity_client.folder(session_hit["xip.reference"])
        try:
            session_languages.update(session_hit.get("imdi.language"))
        except TypeError:
            pass
        # print(session_languages)

        # find the assets with the session folder as parent
        asset_filter_values = {
            # size of preservation bitstream
            "xip.size_r_Preservation": "",
            # all the technical information in a list
            "xip.property_r_Preservation": "",
            # original file name with extension
            "xip.bitstream_names_r_Preservation": "",
            # audio, video, document
            "xip.content_type_r_Preservation": "",
            "xip.security_descriptor": "*",
            "xip.parent_ref": session_folder.reference,
        }
        # now go through all hits
        raw_asset_hits = client.content_client.search_index_filter_list(
            query="*", filter_values=asset_filter_values
        )
        # i = 0
        # make a backup of the generator in case the first one runs into a timeout
        raw_asset_hits1, raw_asset_hitsbackup = tee(raw_asset_hits)
        for raw_asset_hits in (raw_asset_hits1, raw_asset_hitsbackup):
            try:
                asset_hits = [x for x in raw_asset_hits]
                print(f"{len(asset_hits)}.", end="", flush=True)
                files = []
                for asset_hit in asset_hits:
                    try:
                        filename = asset_hit["xip.bitstream_names_r_Preservation"][0]
                    except KeyError:
                        filename = "_UNNAMED"
                    file_ref = asset_hit["xip.reference"]
                    filetype = filename.split(".")[-1]
                    elar_file = ElarFile(filename, file_ref, filetype, id_=file_ref)
                    elar_file.languages = session_languages
                    r_preservation = asset_hit.get("xip.content_type_r_Preservation", "")
                    if not r_preservation:
                        return None
                    elar_file.size = asset_hit["xip.size_r_Preservation"]
                    if "video" in r_preservation:
                        elar_file.duration = get_seconds(asset_hit)
                        elar_file.megatype = "video"
                    elif "audio" in r_preservation:
                        elar_file.duration = get_seconds(asset_hit)
                        elar_file.megatype = "audio"
                    files.append(elar_file)
            except TimeoutError:
                continue
            break  # if the run succeeded the first time, skip the backup
        return files



if __name__ == "__main__":
    ea = ElarArchive()
    # ea.populate()
    ea.populate_collections()
    ea.populate_bundles()
    ea.populate_files()
    ea.write_json()
    # ea.insert_into_database()
