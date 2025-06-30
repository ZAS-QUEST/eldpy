import os
import re
import csv
import logging
import time
import sqlite3
from datetime import date

# from datetime import datetime
from datetime import timedelta

# from dateutil.parser import parse as parse_time
from pathlib import Path

# import pandas as pd
# import humanize
from dotenv import load_dotenv
from pyPreservica import *

from pypreservica_api_wrapper import PreservicaAPIWrapper

HHMMSS = re.compile("([0-9]*?)[H:]?([0-9]*)[M:]?([0-9][0-9])S?")

logging.basicConfig(level=logging.INFO)


class Session:
    def __init__(self, languages):
        self.languages = languages
        # self.countries = countries
        self.vsize = 0
        self.vduration = 0
        self.asize = 0
        self.aduration = 0


def get_minutes_from_str(input_string):
    return get_seconds_from_str(input_string) / 60


def get_seconds_from_str(input_string):
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
        return 3600 * int(h) + 60 * int(m) + int(s)
    return 0


def get_size_duration(hit):
    file_size = hit["xip.size_r_Preservation"]
    duration = 0
    for prop in hit.get("xip.property_r_Preservation", []):
        if "Duration" in prop:
            duration = get_minutes_from_str(prop)
    return file_size, duration


def list_to_string(l):
    if l:
        # do not include falsy elements
        return ", ".join([x for x in l if x])
    return ""


def process_session_hit(session_hit):
    # session_countries = set()
    session_languages = set()
    # we only want published Sessions
    session_sec_desc_set = set(session_hit["xip.security_descriptor"])
    session = Session(session_languages)
    # if not published_tags.intersection(session_sec_desc_set):
    #     return session
    # again we need the folder object to get all the details
    session_folder = client.entity_client.folder(session_hit["xip.reference"])
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
    asset_hits = client.content_client.search_index_filter_list(
        query="*", filter_values=asset_filter_values
    )
    while True:
        try:
            asset_hit = next(asset_hits)
        except RuntimeError:
            # give the server time to relax
            time.sleep(3)
            asset_hit = next(asset_hits)
        except StopIteration:
            break
        # we only want published Assets
        # asset_security_desc_set = set(asset_hit["xip.security_descriptor"])
        # if not published_tags.intersection(asset_security_desc_set):
        #     return None
        # create asset to get information
        # asset = client.entity_client.asset(asset_hit["xip.reference"])
        r_preservation = asset_hit.get("xip.content_type_r_Preservation", "")
        if not r_preservation:
            return None
        if "video" in r_preservation:
            size, duration = get_size_duration(asset_hit)
            session.vsize = size
            session.vduration = duration
        elif "audio" in r_preservation:
            size, duration = get_size_duration(asset_hit)
            session.asize = size
            session.aduration = duration
        return session


def process_hit(hit, collection_folder):
    print("processing")

    collection_countries = set()
    collection_languages = set()

    video_file_size = 0
    audio_file_size = 0
    video_duration = 0
    audio_duration = 0

    collection_title = hit.get("imdi.corpusTitle", "_NO_TITLE")
    print(f"now in {collection_folder.title}")

    collection_countries.add(hit.get("imdi.country"))
    # print(collection_countries, end=" ")
    collection_languages.update(hit.get("imdi.language", []))
    # print(collection_languages)

    # find the folders with the collection folder as parent
    session_filter_values = {
        "imdi.country": "",
        "imdi.sessionTitle": "",
        "imdi.language": "",
        "xip.security_descriptor": "*",
        "xip.parent_ref": collection_folder.reference,
    }

    # now go through all hits
    raw_session_hits = client.content_client.search_index_filter_list(
        query="*", filter_values=session_filter_values
    )
    print(" fetching session hits")
    try:
        session_hits = [x for x in raw_session_hits]
    except RuntimeError:
        time.sleep(3)
        session_hits = [x for x in raw_session_hits]
    print(f" fetched {len(session_hits)} hits")
    print(" analyzing sessions\n ")
    for current_session_hit in session_hits:
        session_ref = current_session_hit["xip.reference"]
        short_title = current_session_hit.get("imdi.sessionTitle", "")[:50]
        print(".", end="", flush=True)
        print(f" processing {session_ref} {short_title}")
        session = process_session_hit(current_session_hit)
        if not session:
            continue
        sessiondata = [
            collection_folder.reference,
            session_ref,
            session.vsize,
            session.vduration,
            session.asize,
            session.aduration,
            0,
            0,
        ]
        print(f"sessiondata:  {sessiondata}")
        cursor.execute("INSERT INTO sessions VALUES (?,?,?,?,?,?,?,?)", sessiondata)
        print(f"  {session.languages}")
        for language in session.languages:
            cursor.execute(
                "INSERT INTO languagesfiles VALUES (?,?,?)",
                [collection_folder.reference, session_ref, language],
            )
        connection.commit()


if __name__ == "__main__":
    limit = 1000
    try:
        given_db_name = sys.argv[1]
    except (TypeError, IndexError):
        given_db_name = "test.db"
    try:
        offset = int(sys.argv[2])
    except (TypeError, IndexError):
        offset = 0
    print(f"offset is {offset}")
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

    connection = sqlite3.connect(given_db_name)
    cursor = connection.cursor()
    #     # now go through all hits
    raw_hits = client.content_client.search_index_filter_list(
        query="*", filter_values=collection_filter_values
    )
    print("fetching all hits into memory", end=" ")
    hits = [x for x in raw_hits]
    print(f"({len(hits)} hits)")
    limit = min(limit, len(hits))
    i = offset
    for current_hit in hits[offset:]:
        i += 1
        if i > limit:
            break
        print(f"{i}/{limit}")
        print("scanning " + current_hit["xip.title"].split("-")[2], end=" ")
        current_collection_folder = client.entity_client.folder(
            current_hit["xip.reference"]
        )
        # if not current_hit["xip.title"].split("-")[2].startswith(key):
        #     print(". Skipping.")
        #     continue
        print("")
        process_hit(current_hit, current_collection_folder)
    connection.close()
