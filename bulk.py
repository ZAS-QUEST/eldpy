import json
from .archive import Archive
from .delaman import archives

def bulk_populate(archives_to_populate=archives, cache=True,exclude=None):
    def load_cache(type_):
        return json.loads(open("cache/%s/%s.json" % (type_, archivename)).read())

    for archivename in archives_to_populate:
        #print(archivename)
        print("processing", archivename)
        archive = archives_to_populate[archivename]
        #print(archive)
        archive.populate_collections(cache=cache)
        print("processing data")
        transcriptioncache, translationschache, glosseschache, entitieschache = None, None, None, None
        if cache:
            transcriptioncache = load_cache('transcriptions')
            translationschache = load_cache('translations')
            glosseschache = load_cache('glosses')
            entitieschache = load_cache('entities')
        for c in archive.collections:
            print(c)
            archive.collections[c].acquire_elans(cache=cache)
            if 'transcriptions'  in exclude:
                print('transcriptions excluded')
            else:
                archive.collections[c].populate_transcriptions(jsoncache=transcriptioncache)
            if 'translations'  in exclude:
                print('translations excluded')
            else:
                archive.collections[c].populate_translations(jsoncache=translationschache)
            if 'glosses' in exclude:
                print('glosses excluded')
            else:
                archive.collections[c].populate_glosses(jsoncache=glosseschache)
            if 'entities'  in exclude:
                print('entities excluded')
            else:
                archive.collections[c].populate_entities(jsoncache=entitieschache)
            if 'metadata'  in exclude:
                print('metadata excluded')
            else:
                archive.get_metadata()


def bulk_cache(cachearchives=archives, exclude=[]):
    def write_jsons(type_):
        for archive in cachearchives:
            print(" ", archive)
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
            print(type_, "excluded")
            continue
        print(type_)
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
