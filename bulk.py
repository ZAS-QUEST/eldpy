import sys
import json
from archive import Archive

archives = {
    #"ANLA": Archive(
        #"ANLA",
        #"https://www.uaf.edu/anla/collections/",
        #collectionprefix="https://uafanlc.alaska.edu/Online",
        #landingpage_template = "https://www.uaf.edu/anla/collections/search/resultDetail.xml?resource=%s"
    #),
    "PARADISEC": Archive(
        "PARADISEC",
        "https://catalog.paradisec.org.au/",
        collectionprefix="http://catalog.paradisec.org.au/repository",
        collection_url_template="http://catalog.paradisec.org.au/repository/%s/%s/%s",
        landingpage_template = "https://catalog.paradisec.org.au/collections/%s"
    ),
    #"ELAR": Archive(
        #"ELAR",
        #"elar.soas.ac.uk",
        #collectionprefix="https://elar.soas.ac.uk/Collection/",
        #collection_url_template="https://elar.soas.ac.uk/Collection/%s",
        #landingpage_template = "https://elar.soas.ac.uk/Collection/%s"
    #),
    #"TLA": Archive(
        #"TLA",
        #"https://archive.mpi.nl",
        #collectionprefix="https://archive.mpi.nl/islandora/object/",
        #collection_url_template="https://archive.mpi.nl/islandora/object/%s",
        #landingpage_template = "https://archive.mpi.nl/islandora/object/%s"
    #),
    #"AILLA": Archive(
        #"AILLA",
        #"https://ailla.utexas.org",
        #collectionprefix="https://ailla.utexas.org/islandora/object/",
        #collection_url_template="https://ailla.utexas.org/islandora/object/%s",
        #landingpage_template = "https://ailla.utexas.org/islandora/object/%s"
    #),
}





def bulk_populate(archives_to_populate=archives, cache=True):
    for archivename in archives_to_populate:
        print("processing", archivename)
        archive = archives_to_populate[archivename]
        archive.populate_collections(cache=cache)
        #print("processing data")
        #transcriptioncache = json.loads(open("cache/transcriptions/%s.json" % archivename).read())
        #translationschache = json.loads(open("cache/translations/%s.json" % archivename).read())
        #glosseschache = json.loads(open("cache/glosses/%s.json" % archivename).read())
        #entitieschache = json.loads(open("cache/entities/%s.json" % archivename).read())
        #for c in archive.collections:
            #archive.collections[c].acquire_elans(cache=True)
            #archive.collections[c].populate_transcriptions(jsoncache=None)
            #archive.collections[c].populate_translations(jsoncache=None)
            #archive.collections[c].populate_glosses(jsoncache=None)
            ##archive.collections[c].populate_entities(jsoncache=entitieschache)
            #archive.get_metadata()


def bulk_cache(cachearchives=archives, exclude=[]):
    def write_jsons(type_):
        for archive in cachearchives:
            print(" ", type_)
            d_for_json = {cachearchives[archive].collections[c].ID: cachearchives[archive].collections[c].__dict__[type_]
                 for c
                 in cachearchives[archive].collections
                }
            with open("cache/%s/%s.json" % (type_, archive), "w") as out:
                out.write(json.dumps(d_for_json, indent=4, sort_keys=True))

    print("caching json")
    types = ["translations", "transcriptions", "glosses", "entities"]
    for type_ in types:
        if type_ in exclude:
            continue
        write_jsons(type_)


def bulk_rdf(rdfarchives=archives):
    for archive in rdfarchives:
        rdfarchives[archive].write_rdf()


def bulk_statistics(statisticsarchives=archives):
    for archive in statisticsarchives:
        with open("cache/statistics/%s.json" % archive, "w") as statisticsout:
            statisticsout.write(
                json.dumps(statisticsarchives[archive].statistics, indent=4, sort_keys=True)
            )


def bulk_fingerprints(fingerprintarchives=archives):
    for archive in fingerprintarchives:
        print("calculating fingerprints")
        for c in fingerprintarchives[archive].collections:
            fingerprintarchives[archive].collections[c].get_fingerprints()
        fingerprintd = {
            c: fingerprintarchives[archive].collections[c].fingerprints
            for c
            in fingerprintarchives[archive].collections
        }
        with open("cache/fingerprints/%s.json" % archive, "w") as out:
            out.write(json.dumps(fingerprintd, indent=4, sort_keys=True))
