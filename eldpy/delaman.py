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
    cursor.execute(files_table_string)

    phyla_table_string = """CREATE TABLE phyla(language TEXT,
                                        phylum TEXT,
                                        family TEXT,
                                        languagecode TEXT PRIMARY KEY);
    """
    cursor.execute(phyla_table_string)

    languages_files_string = """CREATE TABLE languagesfiles(id TEXT,
                                                        archive TEXT,
                                                        languagecode TEXT,
                                                        PRIMARY KEY(id, archive, languagecode));
                            """
    cursor.execute(languages_files_string)

    view_creation_template = """CREATE view iso_{0}{1} AS
                                    SELECT phyla.languagecode, {2}(files.{3}) as {0}_{1}
                                    FROM languages, phyla, files
                                    WHERE languagesfiles.languagecode=phyla.languagecode AND
                                        languagesfiles.id=files.id AND
                                        files.megatype="{0}"
                                    GROUP BY phyla.languagecode;
                                    """
    for type_ in "xml audio video".split():
        for dimension in "bytes seconds files".split():
            if dimension == "files":
                operator = "count"
                column = "id"
            else:
                operator = "sum"
                column = type_
            view_creation_string = view_creation_template.format(
                type_, dimension, operator, column
            )
            cursor.execute(view_creation_string)

    global_language_files_report_string = """CREATE VIEW iso_language_files_report AS
                                SELECT  iso_videofiles.isocode,
                                        iso_videofiles.count as video_count,
                                        iso_videobytes.video_bytes,
                                        iso_videoseconds.video_seconds,
                                        iso_audiofiles.count as audio_count,
                                        iso_audiobytes.audio_bytes,
                                        iso_audioseconds.audio_seconds,
                                        iso_xmlfiles.count as xml_count,
                                        iso_xmlbytes.xml_bytes,
                                        iso_xmlseconds.xml_seconds
                                FROM    iso_videofiles,
                                        iso_videobytes,
                                        iso_videoseconds,
                                        iso_audiofiles,
                                        iso_audiobytes,
                                        iso_audioseconds,
                                        iso_xmlfiles,
                                        iso_xmlbytes,
                                        iso_xmlseconds
                                WHERE   iso_videofiles.isocode=iso_videobytes.isocode AND
                                        iso_videofiles.isocode=iso_videoseconds.isocode AND
                                        iso_videofiles.isocode=iso_audiofiles.isocode AND
                                        iso_videofiles.isocode = iso_audiobytes.isocode AND
                                        iso_videofiles.isocode=iso_audioseconds.isocode AND
                                        iso_videofiles.isocode=iso_xmlfiles.isocode AND
                                        iso_videofiles.isocode=iso_xmlbytes.isocode AND
                                        iso_videofiles.isocode=iso_xmlseconds.isocode;
                            """
    cursor.execute(global_language_files_report_string)

    # FIXME needs outer join
    phylum_report_string = """CREATE view phylum_report AS
                                SELECT   phylum,
                                         family,
                                         SUM(video_count),
                                         SUM(video_bytes),
                                         SUM(video_seconds),
                                         SUM(audio_count),
                                         SUM(audio_bytes),
                                         SUM(audio_seconds),
                                         SUM(xml_count),
                                         SUM(xml_bytes),
                                         SUM(xml_seconds)
                                FROM     phyla,
                                         iso_language_files_report
                                WHERE    phyla.languagecode=iso_language_files_report.languagecode
                                GROUP BY phylum;"""
    cursor.execute(phylum_report_string)

    # FIXME needs outer join
    language_report_string = """CREATE view language_report AS
                                    SELECT phyla.isocode,
                                            name,
                                            phylum,
                                            family,
                                            video_count,
                                            video_bytes,
                                            video_seconds,
                                            audio_count,
                                            audio_bytes,
                                            audio_seconds,
                                            xml_count,
                                            xml_bytes,
                                            xml_seconds
                                    FROM phyla,
                                         iso_language_files_report
                                    WHERE phyla.languagecode=iso_language_files_report.isocode;"""
    cursor.execute(language_report_string)
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
    populate_phyla(db_name=given_db_name)
    # print("ingesting archives")
    # for archive_name, archive in archives.items():
    #     print("ingesting", archive_name)
    #     archive.insert_into_database(db_name=given_db_name)
