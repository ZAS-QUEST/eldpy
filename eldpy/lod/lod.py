import json
import glob
from rdflib import Namespace, Graph, Literal, RDF, RDFS #, URIRef, BNode
from rdflib.namespace import NamespaceManager, DC #, FOAF
# from .resolver import get_URI_for_AILLA, get_URI_for_ANLA, get_URI_for_TLA, get_URI_for_Paradisec, get_URI_for_ELAR


#define general namespaces
QUEST = Namespace("http://zasquest.org/")
QUESTRESOLVER = Namespace("http://zasquest.org/resolver/")
DBPEDIA = Namespace("http://dbpedia.org/ontology/")
WIKIDATA = Namespace("http://www.wikidata.org/entity/")
LGR = Namespace("https://www.eva.mpg.de/lingua/resources/glossing-rules.php/")
LIGT = Namespace("http://purl.org/liodi/ligt/")
FLEX = Namespace("http://example.org/flex/")
NIF = Namespace("http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#")

#define archive namespaces
ELD_NAMESPACE_MANAGER = NamespaceManager(Graph())
ELD_NAMESPACE_MANAGER.bind('dbpedia', DBPEDIA)
ELD_NAMESPACE_MANAGER.bind('wikidata', WIKIDATA)
ELD_NAMESPACE_MANAGER.bind('quest', QUEST) #for ontology
ELD_NAMESPACE_MANAGER.bind('QUESTRESOLVER', QUESTRESOLVER) #for the bridge for rewritable URLs
ELD_NAMESPACE_MANAGER.bind("rdfs", RDFS)
ELD_NAMESPACE_MANAGER.bind("dc", DC)
ELD_NAMESPACE_MANAGER.bind("lgr", LGR)
ELD_NAMESPACE_MANAGER.bind("ligt", LIGT)
ELD_NAMESPACE_MANAGER.bind("flex", FLEX)
ELD_NAMESPACE_MANAGER.bind("nif", NIF)

ARCHIVE_NAMESPACES = {
    'paradisec': Namespace("https://catalog.paradisec.org.au/collections/"),
    #'elarcorpus': Namespace("https://lat1.lis.soas.ac.uk/corpora/ELAR/"),
    'elarcorpus': Namespace("https://elar.soas.ac.uk/Record/"),
    'elarfiles': Namespace("https://elar.soas.ac.uk/resources/"),
    'elar': Namespace("https://elar.soas.ac.uk/resources/"),
    'ailla': Namespace("http://ailla.utexas.org/islandora/object/"),
    'anla': Namespace("https://www.uaf.edu/anla/collections/search/resultDetail.xml?id="),
    'tla': Namespace("https://archive.mpi.nl/islandora/object/"),
    'langsci': Namespace("https://langsci-press.org/catalog/book/")
    }

#duplicate for test purposes
keylist = list(ARCHIVE_NAMESPACES.keys())
for key in keylist:
    ARCHIVE_NAMESPACES["%s2"%key] = ARCHIVE_NAMESPACES[key]

for archive in ARCHIVE_NAMESPACES:
    ELD_NAMESPACE_MANAGER.bind(archive, ARCHIVE_NAMESPACES[archive])

def create_graph():
    return Graph(namespace_manager=ELD_NAMESPACE_MANAGER)


def write_graph(graph, filename):
    with open(filename, "wb") as rdfout:
        rdfout.write(graph.serialize(format='n3'))



#AILLAMAPPER = dict(
    #[(line.strip().split()[::-1]) for line in open("aillaeaf.tsv").readlines()]
#)
#ANLAMAPPER = dict(
    #[(line.strip().split("/")[::-1][:2]) for line in open("anla-eaffiles").readlines()]
#)
#ELARMAPPER = dict(
    #[(line.strip().split()[::-1]) for line in open("elar2.tsv").readlines()]
#)

#TLAMAPPER = {}
#tlajson = json.loads(open("tla.json").read())
#for k in tlajson:
    #vs = tlajson[k]
    #for v in vs:
        #TLAMAPPER[v] = k.replace("/datastream/OBJ/download", "").split("/")[-1]


#PARADISECMAPPER = {}
#paradisecjson = json.loads(open("paradisec.json").read())
#for k in paradisecjson:
    #vs = paradisecjson[k]
    #for v in vs:
        #PARADISECMAPPER[v] = k.replace("/collections/", "")

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
