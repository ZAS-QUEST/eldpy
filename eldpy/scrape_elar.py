import os
import re
import csv
import logging
import time
import sqlite3
import pprint

from datetime import date
# from helpers import language_dictionary, type2megatype
from itertools import tee
# from datetime import datetime
from datetime import timedelta

from eldpy.archives.elar_file import ElarFile

from eldpy.archives.elar_archive import  ElarArchive
# from dateutil.parser import parse as parse_time
from pathlib import Path

# import pandas as pd
# import humanize
from dotenv import load_dotenv
from pyPreservica import *

from pypreservica_api_wrapper import PreservicaAPIWrapper

HHMMSS = re.compile("([0-9]*?)[H:]?([0-9]*)[M:]?([0-9][0-9])S?$")

logging.basicConfig(level=logging.INFO)




if __name__ == "__main__":
    ea = ElarArchive()
    fussy=False
    try:
        offset = int(sys.argv[1])
    except (TypeError, IndexError):
        offset = 0
    print(f"offset is {offset}")
    try:
        given_db_name = sys.argv[2]
    except (TypeError, IndexError):
        given_db_name = "test.db"
    print(f'db to use is {given_db_name}')
    ea.populate_database(given_db_name=given_db_name, offset=offset, limit=99999, fussy=fussy)
