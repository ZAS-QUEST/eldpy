import sys
import json
from archive import Archive

LIMIT = 999999
OFFSET = 0
try:
    OFFSET = int(sys.argv[1])
except IndexError:
    OFFSET = 0

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

def writejson(type_):
    print(" ", type_)
    d = {c: archive.collections[c].__dict__[type_] for c in archive.collections}
    with open("cache/%s/%s.json" % (type_, archive.name), "w") as out:
        out.write(json.dumps(d, indent=4, sort_keys=True))

for archivename in archives[]:
#for archivename in ['AILLA']:
#for archivename in ['ANLA']:
#for archivename in ['ELAR']:
#for archivename in ['PARADISEC']:
#for archivename in ['TLA']:
    print("processing", archivename)
    archive = archives[archivename]
    archive.populate_collections()
    print("loading caches")
    transcriptioncache = json.loads(open("cache/transcriptions/%s.json" % archive.name).read())
    translationcache = json.loads(open("cache/translations/%s.json" % archive.name).read())
    glosscache = json.loads(open("cache/glosses/%s.json" % archive.name).read())
    entitiescache = json.loads(open("cache/entities/%s.json" % archive.name).read())
    print("processing data")
    for c in archive.collections:
        archive.collections[c].acquire_elans(cache=True)
        #archive.collections[c].populate_transcriptions(jsoncache=transcriptioncache)
        #archive.collections[c].populate_translations(jsoncache=translationcache)
        #archive.collections[c].populate_glosses(jsoncache=glosscache)
        #archive.collections[c].populate_entities(jsoncache=entitiescache)
    #archive.print_metadata()
    #print("caching json")
    #writejson('translations')
    #writejson('transcriptions')
    #writejson('glosses')
    #writejson('entities')

    #with open("cache/statistics/%s.json" % archive.name, "w") as statisticsout:
        #statisticsout.write(json.dumps(archive.statistics, indent=4, sort_keys=True))

    #print("calculating fingerprints")
    archive.get_fingerprints()
    fingerprintd = {c: archive.collections[c].fingerprints for c in archive.collections}
    with open("cache/fingerprints/%s.json" % archive.name, "w") as out:
        out.write(json.dumps(fingerprintd, indent=4, sort_keys=True))

    #print("writing rdf")
    #meta rdf
    #print("  transcriptions")
    #archive.write_transcriptions_rdf()
    #print("  glosses")
    #archive.write_glosses_rdf()
    #print("  translations")
    #archive.write_translations_rdf()
    #print("  entities")
    #archive.write_entities_rdf()
    #print("  done")
