import sys
import json
from archive import Archive

archives = {
    "ANLA": Archive(
        "ANLA",
        "https://www.uaf.edu/anla/collections/",
        collectionprefix="https://uafanlc.alaska.edu/Online",
    ),
    "PARADISEC": Archive(
        "PARADISEC",
        "https://catalog.paradisec.org.au/",
        collectionprefix="http://catalog.paradisec.org.au/repository",
        collection_url_template="http://catalog.paradisec.org.au/repository/%s/%s/%s",
    ),
    "ELAR": Archive(
        "ELAR",
        "elar.soas.ac.uk",
        collectionprefix="https://elar.soas.ac.uk/Collection/",
        collection_url_template="https://elar.soas.ac.uk/Collection/%s",
    ),
    "TLA": Archive(
        "TLA",
        "https://archive.mpi.nl",
        collectionprefix="https://archive.mpi.nl/islandora/object/",
        collection_url_template="https://archive.mpi.nl/islandora/object/%s",
    ),
    "AILLA": Archive(
        "AILLA",
        "https://ailla.utexas.org",
        collectionprefix="https://ailla.utexas.org/islandora/object/",
        collection_url_template="https://ailla.utexas.org/islandora/object/%s",
    ),
}


def write_jsons(type_, jsonarchives=archives):
    for archive in jsonarchives:
        print(" ", type_)
        with open("cache/%s/%s.json" % (type_, archive.name), "w") as out:
            out.write(archive.json(type_))



def bulk_populate(archives_to_populate=archives, cache=True):
    for archivename in archives_to_populate:
        print("processing", archivename)
        archive = Archive(archives_to_populate[archivename])
        archive.populate_collections()
        print("processing data")
        for c in archive.collections:
            archive.collections[c].acquire_elans(cache=cache)
            archive.collections[c].populate_transcriptions(cache=cache)
            archive.collections[c].populate_translations(cache=cache)
            archive.collections[c].populate_glosses(cache=cache)
            archive.collections[c].populate_entities(cache=cache)
        archive.print_metadata()


def bulk_cache(cachearchives=archives, exclude=[]):
    print("caching json")
    types = ["translation", "transcription", "glosses", "entities"]
    for type_ in types:
        if type_ in exclude:
            continue
        write_jsons(type_, jsonarchives=cachearchives)


def bulk_rdf(rdfarchives=archives):
    for archive in rdfarchives:
        archive.write_rdf()


def bulk_statistics(statisticsarchives=archives):
    for archive in statisticsarchives:
        with open("cache/statistics/%s.json" % archive.name, "w") as statisticsout:
            statisticsout.write(
                json.dumps(archive.statistics, indent=4, sort_keys=True)
            )


def bulk_fingerprints(fingerprintarchives=archives):
    for archive in fingerprintarchives:
        print("calculating fingerprints")
        archive.get_fingerprints()
        fingerprintd = {
            c: archive.collections[c].fingerprints for c in archive.collections
        }
        with open("cache/fingerprints/%s.json" % archive.name, "w") as out:
            out.write(json.dumps(fingerprintd, indent=4, sort_keys=True))
