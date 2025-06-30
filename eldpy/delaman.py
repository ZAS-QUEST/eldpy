"""
model the Digital Endangered Languages and Musics Archives Network and its member archives
"""

import sqlite3
import sys

# from archive import Archive
from phyla import phyla
# from tla_sizes import tla_sizes
from ailla_archive import AillaArchive
from elar_archive import ElarArchive
from paradisec_archive import ParadisecArchive
from tla_archive import TLAArchive

archives = {
    "PARADISEC": ParadisecArchive(),
    "AILLA": AillaArchive(),
    # "ELAR": ElarArchive(),
    "TLA": TLAArchive(),
}


def setup_metadata_database(db_name="delaman_holdings.db"):
    """
    setup the bare database with basic tables and views but no content
    """

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    files_table_string = """CREATE TABLE files(id TEXT,
                                        archive TEXT NOT NULL,
                                        collection TEXT NOT NULL,
                                        bundle TEXT,
                                        megatype TEXT,
                                        filetype TEXT NOT NULL,
                                        bytes int,
                                        seconds int,
                                        PRIMARY KEY (ID, archive));
    """
    # cursor.execute(files_table_string)

    phyla_table_string = """CREATE TABLE phyla(language TEXT,
                                        phylum TEXT,
                                        family TEXT,
                                        languagecode TEXT PRIMARY KEY);
    """
    # cursor.execute(phyla_table_string)

    languages_files_string = """CREATE TABLE languagesfiles(id TEXT,
                                                        archive TEXT,
                                                        languagecode TEXT,
                                                        PRIMARY KEY(id, archive, languagecode));
                            """
    # cursor.execute(languages_files_string)

    views = [
    """CREATE VIEW languagevideos AS
        SELECT languagesfiles.languagecode,
                count(files.id) AS videocount,
                SUM(files.bytes) AS videobytes,
                SUM(files.seconds) AS videoseconds
        FROM languagesfiles, files
        WHERE languagesfiles.id=files.id AND files.megatype='video'
        GROUP BY languagecode """,
    """CREATE VIEW languageaudios  AS
        SELECT languagesfiles.languagecode,
            count(files.id) AS audiocount,
            SUM(files.bytes) AS audiobytes,
            SUM(files.seconds) AS audioseconds
        FROM languagesfiles, files
        WHERE languagesfiles.id=files.id AND files.megatype='audio'
        GROUP BY languagecode """,
    """CREATE VIEW languagexmls AS
        SELECT languagesfiles.languagecode,
            count(files.id) AS xmlcount,
            SUM(files.bytes) AS xmlbytes,
            SUM(files.seconds) AS xmlseconds
        FROM languagesfiles, files
        WHERE languagesfiles.id=files.id AND files.megatype='xml'
        GROUP BY languagecode """,
    """CREATE VIEW fulljoinvideos AS
        SELECT * FROM  phyla
            LEFT JOIN languagevideos
            ON languagevideos.languagecode=phyla.languagecode """,
    """CREATE VIEW fulljoinaudios AS
        SELECT * FROM  phyla
            LEFT JOIN languageaudios
            ON languageaudios.languagecode=phyla.languagecode """,
    """CREATE VIEW fulljoinxmls AS
        SELECT * FROM  phyla LEFT JOIN languagexmls
        ON languagexmls.languagecode=phyla.languagecode """,
    """CREATE VIEW cleanlanguagecsv AS
        SELECT * FROM languagestats
            WHERE videocount IS NOT NULL
            OR audiocount IS NOT NULL
            OR xmlcount is not null """,
    """CREATE VIEW cleanphylumcsv AS
        SELECT * FROM phylumstats
            WHERE videocount IS NOT NULL
            OR audiocount IS NOT NULL
            OR xmlcount is not null """,
    """CREATE VIEW languagecodearchive AS
        SELECT distinct languagecode, archive
            FROM languagesfiles
            ORDER BY languagecode, archive """,
    """CREATE VIEW languagecodearchiveconcat AS
        SELECT languagecode,
                GROUP_CONCAT(archive) AS archives
            FROM languagecodearchive
            GROUP BY languagecode"""
    ]
    for view in views:
        cursor.execute(view)
    connection.commit()
    connection.close()


def populate_phyla(db_name="delaman_holdings.db"):
    """
    insert information about languages, phyla, families and isocodes
    """

    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    insert_matrix = [(t[2], t[1], t[0], t[3]) for t in phyla]
    cursor.executemany("INSERT INTO phyla VALUES(?,?,?,?)", insert_matrix)
    connection.commit()
    connection.close()


if __name__ == "__main__":
    given_db_name = "test.db"
    try:
        given_db_name = sys.argv[1]
    except IndexError:
        pass
    print("setting up tables")
    setup_metadata_database(db_name=given_db_name)
    # populate_phyla(db_name=given_db_name)
    # print("ingesting archives")
    # for archive_name, archive in archives.items():
    #     print(" ingesting", archive_name)
    #     archive.insert_into_database(f"{archive_name.lower()}_copy_f.json", db_name=given_db_name)
