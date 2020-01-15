"""
map eaf files to their landing pages

for historical reasons, a variety of different formats are used. This will eventually be consolidated
"""


import json

AILLAMAPPER = dict(
    [(line.strip().split()[::-1]) for line in open("aillaeaf.tsv").readlines()]
)
ANLAMAPPER = dict(
    [(line.strip().split("/")[::-1][:2]) for line in open("anla-eaffiles").readlines()]
)
ELARMAPPER = dict(
    [(line.strip().split()[::-1]) for line in open("elar2.tsv").readlines()]
)

TLAMAPPER = {}
tlajson = json.loads(open("tla.json").read())
for k in tlajson:
    vs = tlajson[k]
    for v in vs:
        TLAMAPPER[v] = k.replace("/datastream/OBJ/download", "").split("/")[-1]
        
        
ELARMAPPER = {} 
for t in open("elar2.tsv").readlines():
    ID, eaf = t.strip().split()
    eafname = eaf.split('/')[-1]  
    ELARMAPPER[eafname] = ID


PARADISECMAPPER = {}
paradisecjson = json.loads(open("paradisec.json").read())
for k in paradisecjson:
    vs = paradisecjson[k]
    for v in vs:
        PARADISECMAPPER[v] = k.replace("/collections/", "")

# def get_URI(eaf, archive):
# if archive == "AILLA":
# return get_URI_for_AILLA(eaf)


def get_URI_for_AILLA(eaf):
    return AILLAMAPPER[eaf].split("/")[-1]


def get_URI_for_ANLA(eaf):
    return ANLAMAPPER[eaf]


def get_URI_for_TLA(eaf):
    return TLAMAPPER[eaf]


def get_URI_for_Paradisec(eaf):
    return PARADISECMAPPER[eaf]


def get_URI_for_ELAR(eaf):
    try:
        return ELARMAPPER[eaf]
    except KeyError:
        return  "www.test.de"
