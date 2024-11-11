import os
import re
import csv
import logging
import time
import sqlite3
import pprint

from datetime import date
from helpers import language_dictionary, type2megatype
from itertools import tee
# from datetime import datetime
from datetime import timedelta

from elar_file import ElarFile
# from dateutil.parser import parse as parse_time
from pathlib import Path

# import pandas as pd
# import humanize
from dotenv import load_dotenv
from pyPreservica import *

from pypreservica_api_wrapper import PreservicaAPIWrapper

HHMMSS = re.compile("([0-9]*?)[H:]?([0-9]*)[M:]?([0-9][0-9])S?$")

logging.basicConfig(level=logging.INFO)


# def get_minutes_from_str(input_string):
#     return get_seconds_from_str(input_string) / 60


def get_seconds_from_str(input_string):
    result = 0
    if "prp/10002" in input_string or "TSS-prp/30" in input_string:
        duration_string = input_string.split()[2].split(".")[0]
        try:
            h, m, s = HHMMSS.match(duration_string).groups()
        except AttributeError:
            return 0
        if not h:
            h = 0
        if not m:
            m = 0
        if not s:
            s = 0
        result = 3600 * int(h) + 60 * int(m) + int(s)
    # print(input_string, result)
    return result


def get_seconds(hit):
    duration = 0
    for prop in hit.get("xip.property_r_Preservation", []):
        if "Duration" in prop:
            duration = get_seconds_from_str(prop)
    return duration


def list_to_string(l):
    if l:
        # do not include falsy elements
        return ", ".join([x for x in l if x])
    return ""


def process_session_hit(session_hit, client):
    # session_countries = set()
    session_languages = set()
    # we only want published Sessions
    # session_sec_desc_set = set(session_hit["xip.security_descriptor"])
    session_folder = client.entity_client.folder(session_hit["xip.reference"])
    # elar_file = ElarFile(session_languages)
    # if not published_tags.intersection(session_sec_desc_set):
    #     return session
    # again we need the folder object to get all the details
    # try:
    #     session_countries.add(session_hit.get("imdi.country"))
    # except TypeError:
    #     pass
    # print(session_countries)
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
    i=0
    # make a backup of the generator in case the first one runs into a timeout
    raw_asset_hits1, raw_asset_hitsbackup = tee(raw_asset_hits)
    for raw_asset_hits in (raw_asset_hits1, raw_asset_hitsbackup):
        try:
            asset_hits = [x for x in raw_asset_hits]
            print(f"{len(asset_hits)}.", end='', flush=True)
            files = []
            for asset_hit in asset_hits:
                # pprint.pprint(asset_hit)
                # we only want published Assets
                # asset_security_desc_set = set(asset_hit["xip.security_descriptor"])
                # if not published_tags.intersection(asset_security_desc_set):
                #     return None
                # create asset to get information
                # asset = client.entity_client.asset(asset_hit["xip.reference"])
                try:
                    filename = asset_hit['xip.bitstream_names_r_Preservation'][0]
                except KeyError:
                    filename = "_UNNAMED"
                file_ref = asset_hit['xip.reference']
                filetype = filename.split('.')[-1]
                elar_file = ElarFile(filename,file_ref,filetype,id_=file_ref)
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
        break #if the run succeeded the first time, skip the backup
    return files


def process_collection(hit, collection_folder, client, cursor, fussy=True):
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
    cursor.execute(f'select * from files where archive="ELAR" and collection="{collection_ref}"')
    files_for_collection = cursor.fetchall()
    if len(files_for_collection) > 0:
        cursor.execute(f'select distinct(bundle) from files where archive="ELAR" and collection="{collection_ref}"')
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
    print(f"Analyzing {len(session_hits)} sessions. Numbers indicate the number of files fetched per session", end="\n ")
    collection_files_db = []
    languages_db = []
    for current_session_hit in session_hits:
        # pprint.pprint(current_session_hit)
        session_ref = current_session_hit["xip.reference"]
        short_title = current_session_hit.get("imdi.sessionTitle", "")[:50]
        # print(f" processing {file_ref} {short_title}")
        if fussy:
            elar_files = process_session_hit(current_session_hit, client)
        else:
            try:
                elar_files = process_session_hit(current_session_hit, client)
            except pyPreservica.common.ReferenceNotFoundException as e:
                print(f"Archive problem while fetching files for  {session_ref} in {collection_ref}. Skipping")
                continue
        if not elar_files:
            continue
        for elar_file in elar_files:
            elar_file.megatype = type2megatype(elar_file.type_)
            file_ref = elar_file.id_
            file_data = [
                file_ref,
                'ELAR',
                collection_ref,
                session_ref,
                elar_file.megatype,
                elar_file.type_,
                elar_file.size,
                elar_file.duration
            ]
            # print(file_data)
            collection_files_db.append(file_data)
            for language in elar_file.languages:
                try:
                    iso6393 = language_dictionary[language]['iso6393']
                except KeyError:
                    iso6393 = f"_{language}"
                language_data = (file_ref, 'ELAR', iso6393)
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
    ingested_collections.append(collection_folder)
    print()
    return True



def retrieve_collections(connection, offset=0, limit=99999, fussy=True):
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
            success = process_collection(current_hit, current_collection_folder, client, cursor, fussy=fussy)
            if success:
                connection.commit()
                print("Added to database")
    except RuntimeError as e:
        collections_with_errors.append((i,current_collection_folder))
        print()
        print(e)
        print("Server connection dropped. Proceeding to next collection")
        retrieve_collections(connection,offset=i,fussy=fussy)
    except sqlite3.IntegrityError as e:
        connection.rollback()
        collections_with_errors.append((i,current_collection_folder))
        print()
        print(e)
        print("Database problem. Proceeding to next collection")
        retrieve_collections(connection,offset=i,fussy=fussy)
    except pyPreservica.common.ReferenceNotFoundException as e:
        connection.rollback()
        collections_with_errors.append((i,current_collection_folder))
        print()
        print(e)
        print("Archive problem. Proceeding to next collection")
        retrieve_collections(connection,offset=i,fussy=fussy)

if __name__ == "__main__":
    fussy=False
    connection = sqlite3.connect("test.db")
    collections_with_errors = []
    ingested_collections = []
    limit = 99999
    # limit = 5
    try:
        offset = int(sys.argv[1])
    except (TypeError, IndexError):
        offset = 0
    print(f"offset is {offset}")
    retrieve_collections(connection, offset=offset, limit=99999, fussy=fussy)
    print("The following collections could not be ingested:", collections_with_errors)
    connection.close()
