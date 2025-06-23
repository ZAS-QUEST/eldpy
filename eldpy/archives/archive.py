"""
An archive with primary material in and about endangered languages
"""

import json

# import pprint
import datetime
import sqlite3
from collections import Counter, defaultdict

import squarify
import matplotlib.pyplot as plt
from matplotlib import cm

# from rdflib import Namespace, Graph, Literal, RDF, RDFS  # , URIRef, BNode


DEBUG = False
# DEBUG = True

LIMIT = 10000
if DEBUG:
    LIMIT = 3
    print(f"debugging mode enabled, retrieval limit is {LIMIT}")


class Archive:
    """
    An archive with primary material in and about endangered languages
    """

    # FILETYPES = {
    #     "ELAN": "text/x-eaf+xml",
    #     "Toolbox": "text/x-toolbox-text",
    #     "transcriber": "text/x-trs",
    #     "praat": "text/praat-textgrid",
    #     "Flex": "FLEx",
    # }

    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.collections = []
        self.files = []
        self.statistics = {}
        self.fingerprints = {}

    def populate_collections(self, limit=LIMIT):
        """
        get all bundles for the collections
        """

    def populate_bundles(self, limit=LIMIT, offset=0):
        """
        get all bundles for the collections
        """

        print("populating bundles")
        number_of_collections = len(self.collections)
        for i, collection in enumerate(self.collections[:limit]):
            print(f"c{i+1}/{number_of_collections}", end=" ")
            if collection.bundles == []:
                collection.populate_bundles(limit=limit)
            self.bundles += collection.bundles

    def populate_files(self, limit=LIMIT):
        """
        get all bundles for the collections
        """

        print("populating files")
        number_of_collections = len(self.collections)
        for i, collection in enumerate(self.collections):
            print(f"c{i+1}/{number_of_collections}")
            number_of_bundles = len(collection.bundles)
            for j, bundle in enumerate(collection.bundles[:limit]):
                print(f" b{j+1}/{number_of_bundles}", end=" ")
                bundle.populate_files()

    def get_languages(self, s):
        """dummy method for subclasses to instantiate"""
        return s

    def get_id(self, f):
        """dummy method for subclasses to instantiate"""
        id_ = f["name"]
        if not id_:
            return None
        return id_

    def get_length(self, f):
        """dummy method for subclasses to instantiate"""
        duration = f.get("duration", "").strip()
        if duration in ("", "--"):
            duration = 0
        return duration

    def get_type(self, type_):
        """dummy method for subclasses to instantiate"""
        return type_

    def insert_into_database(self, input_file, db_name="test.db"):
        """
        read the json file and insert it into a sqlite3 database
        """

        insert_file_list = []
        insert_language_list = []
        found_ids = {}
        with open(input_file, encoding="utf8") as json_in:
            d = json.load(json_in)
        for collection_name, collection_d in d.items():
            collection_has_duplicates = False
            for bundle_name, bundle_d in collection_d["bundles"].items():
                for f in bundle_d["files"]:
                    id_ = self.get_id(f)
                    if not id_:
                        continue
                    if id_.strip() == "":
                        continue
                    type_ = self.get_megatype(f["type_"])
                    megatype = self.get_megatype(f["type_"])
                    size = f["size"]
                    length = self.get_length(f)
                    if found_ids.get(id_):
                        if found_ids[id_] > 1:
                            collection_has_duplicates = True
                        found_ids[id_] += 1
                        continue
                    found_ids[id_] = 1
                    insert_file_tuple = (
                        id_,
                        self.name,
                        collection_name,
                        bundle_name,
                        type_,
                        megatype,
                        size,
                        length,
                    )
                    insert_file_list.append(insert_file_tuple)
                    for language in self.get_languages(f["languages"]):
                        insert_language_tuple = (id_, self.name, language)
                        insert_language_list.append(insert_language_tuple)
            if collection_has_duplicates:
                print(f"{collection_name} has duplicates:", end="\n    ")
                print(
                    ",".join(
                        [id_ for id_, occurences in found_ids.items() if occurences > 1]
                    )
                )
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()
        cursor.executemany(
            "INSERT INTO files VALUES(?,?,?,?,?,?,?,?)", insert_file_list
        )
        cursor.executemany(
            "INSERT INTO languagesfiles VALUES(?,?,?)", set(insert_language_list)
        )
        connection.commit()
        connection.close()

    def get_fingerprints(self):
        """map filenames to fingerprints"""
        fingerprintd = {
            f"{self.name}/{eaf.path}": eaf.fingerprint()
            for c in self.collections
            for eaf in self.collections[c].elanfiles
        }

        # sort by number of occurences and print
        counted_fingerprints = Counter(fingerprintd.values())
        ranks = sorted(
            [(counted_fingerprints[key], key) for key in counted_fingerprints.keys()]
        )[::-1]
        values = [x[0] for x in ranks]
        squarify.plot(
            sizes=values,
            label=values[:38],
            color=[cm.pink(x * 0.1) for x in [2, 8, 4, 7, 1, 6, 3, 9, 5]],
        )  # jumble colormap
        plt.axis("off")
        plt.savefig(f"tiertypetreemap-{self.name}.png")
        with open(f"tierranks-{self.name}.txt", "w", encoding="utf8") as out:
            out.write("\n".join(["{x}:{x}" for x in ranks]))
        self.fingerprints = fingerprintd

    def get_metadata(self):
        """get aggregated information about tranlations, transcriptions and glosses
        for this archive"""

        d = defaultdict(int)

        metadatafields = [
            "transcriptionfiles",
            "transcriptiontiers",
            "transcriptionwords",
            "transcribedseconds",
            #
            "translationfiles",
            "translationtiers",
            "translationwords",
            #
            "glossfiles",
            "glosstiers",
            "glosssentences",
            "glosswords",
            "glossmorphemes",
        ]

        for c in self.collections:
            for field in metadatafields:
                d[field] += self.collections[c].__dict__[field]

        d["transcribedhours"] = str(
            datetime.timedelta(seconds=d["transcribedseconds"])
        ).split(".", maxsplit=1)[0]
        self.statistics.update(d)

    def populate(self, limit=LIMIT):
        """add all collections, bundles, and files"""

        self.populate_collections(limit=limit)
        self.populate_bundles(limit=limit)
        self.populate_files(limit=limit)

    def get_megatype(self, type_):
        """dummy method for subclasses to instantiate"""
        return type_

    # def getIdentifiers(self, filename, typ):
    # tree = etree.parse(filename)
    # etree.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    ## retrieve all tags <dc:format>
    # dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
    ##retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
    # identifiers = []
    # for dcformat in dcformats:
    # if dcformat.text == typ:
    # identifiers = dcformat.findall(
    # "../{http://purl.org/dc/elements/1.1/}identifier"
    # )
    # return identifiers

    # def retrieve(self, xmlfiles, mimetype):
    ## retrieve all identifiers found in the xml files which include relevant mimetype
    # globalidentifiers = [self.getIdentifiers(x, mimetype) for x in xmlfiles]
    ## remove empty return values
    # records = [x for x in globalidentifiers if x != None]
    ## flatten out tuples of multiple identifiers contained in one file
    # IDs = [x2.text for x in records for x2 in x]
    # print(
    # "found %i IDs (%i records) with references to %s files"
    # % (len(IDs), len(records), mimetype)
    # )
    # return IDs, records

    # def scan(self, d, xmlfiles, filetypes):
    # print("Scanning %s" % d)
    # for filetype in filetypes:
    # IDs, records = self.retrieve(xmlfiles, filetypes[filetype])

    # def olaceaf(self, xmlfile, typ):
    # tree = etree.parse(xmlfile)
    # etree.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
    # globalidentifiers = []
    # dico = defaultdict(list)
    ## retrieve all tags <dc:format>
    # dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
    # retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
    # print(len(dcformats))
    # for dcformat in dcformats:
    # if dcformat.text.strip() == typ:
    # identifiers = dcformat.getparent().findall(
    # ".//{http://purl.org/dc/elements/1.1/}identifier"
    # )
    # globalidentifiers.append(identifiers)
    # records = [x for x in globalidentifiers if x != None]
    ## flatten out tuples of multiple identifiers contained in one file
    # for IDs in records:
    # for item in IDs:  # etree.findall returns list
    # dico[0].append(item.text.strip().replace("<", "").replace(">", ""))
