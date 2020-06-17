import json
import glob
from rdflib import Namespace, Graph, Literal, RDF, RDFS #, URIRef, BNode
from rdflib.namespace import NamespaceManager, DC #, FOAF
from .resolver import get_URI_for_AILLA, get_URI_for_ANLA, get_URI_for_TLA, get_URI_for_Paradisec, get_URI_for_ELAR


#define general namespaces
QUEST = Namespace("http://zasquest.org/")
QUESTRESOLVER = Namespace("http://zasquest.org/resolver/")
DBPEDIA = Namespace("http://dbpedia.org/ontology/")
WIKIDATA = Namespace("http://www.wikidata.org/entity/")
LGR = Namespace("https://www.eva.mpg.de/lingua/resources/glossing-rules.php/")
LIGT = Namespace("http://purl.org/liodi/ligt")

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

ARCHIVE_NAMESPACES = {
    'paradisec': Namespace("https://catalog.paradisec.org.au/collections/"),
    #'elarcorpus': Namespace("https://lat1.lis.soas.ac.uk/corpora/ELAR/"),
    'elarcorpus': Namespace("https://elar.soas.ac.uk/Record/"),
    'elarfiles': Namespace("https://elar.soas.ac.uk/resources/"),
    'elar': Namespace("https://elar.soas.ac.uk/resources/"),
    'ailla': Namespace("http://ailla.utexas.org/islandora/object/"),
    'anla': Namespace("https://www.uaf.edu/anla/collections/search/resultDetail.xml?id="),
    'tla': Namespace("https://archive.mpi.nl/islandora/object/")
    }

for archive in ARCHIVE_NAMESPACES:
    ELD_NAMESPACE_MANAGER.bind(archive, ARCHIVE_NAMESPACES[archive])

def create_graph():
    return Graph(namespace_manager=ELD_NAMESPACE_MANAGER)


def write_graph(graph, filename):
    with open(filename, "wb") as rdfout:
        rdfout.write(graph.serialize(format='n3'))

LGRLIST = set(
    [
        "1",
        "2",
        "3",
        "A",
        "ABL",
        "ABS",
        "ACC",
        "ADJ",
        "ADV",
        "AGR",
        "ALL",
        "ANTIP",
        "APPL",
        "ART",
        "AUX",
        "BEN",
        "CAUS",
        "CLF",
        "COM",
        "COMP",
        "COMPL",
        "COND",
        "COP",
        "CVB",
        "DAT",
        "DECL",
        "DEF",
        "DEM",
        "DET",
        "DIST",
        "DISTR",
        "DU",
        "DUR",
        "ERG",
        "EXCL",
        "F",
        "FOC",
        "FUT",
        "GEN",
        "IMP",
        "INCL",
        "IND",
        "INDF",
        "INF",
        "INS",
        "INTR",
        "IPFV",
        "IRR",
        "LOC",
        "M",
        "N",
        "NEG",
        "NMLZ",
        "NOM",
        "OBJ",
        "OBL",
        "P",
        "PASS",
        "PFV",
        "PL",
        "POSS",
        "PRED",
        "PRF",
        "PRS",
        "PROG",
        "PROH",
        "PROX",
        "PST",
        "PTCP",
        "PURP",
        "Q",
        "QUOT",
        "RECP",
        "REFL",
        "REL",
        "RES",
        "S",
        "SBJ",
        "SBJV",
        "SG",
        "TOP",
        "TR",
        "VOC",
    ]
)

# terms which are occasionally recognized, but which are always false positives in the context of ELD
NER_BLACKLIST = [
    "Q7946755", #'wasn', radio station
    "Q3089073", #'happy, happy', norwegian comedy film
    "Q19893364",#'Inside The Tree', music album
    "Q49084,"# ss/ short story
    "Q17646620",# "don't" Ed Sheeran song
    "Q2261572",# "he/she" Gender Bender
    "Q35852",# : "ha" hectare
    "Q119018",#: "Mhm" Mill Hill Missionaries
    "Q932347",# "gave",# generic name referring to torrential rivers, in the west side of the Pyrenees
    "Q16836659", #"held" feudal land tenure in England
    "Q914307",# "ll" Digraph
    "Q3505473",# "stayed" Stay of proceedings
    "Q303",# "him/her" Elvis Presley
    "Q2827398",#: "Aha!" 2007 film by Enamul Karim Nirjhar
    "Q1477068",# "night and day" Cole Porter song
    "Q1124888",# "CEDA" Spanish Confederation of the Autonomous Righ
    ]

acceptable_translation_tier_types = [
    "eng",
    "english translation",
    "English translation",
    "fe",
    "fg",
    "fn",
    "fr",
    "free translation",
    "Free Translation",
    "Free-translation",
    "Free Translation (English)",
    "ft",
    "fte",
    "tf (free translation)",
    "Translation",
    "tl",
    "tn",
    "tn (translation in lingua franca)",
    "tf_eng (free english translation)",
    "trad1",
    "Traducción Español",
    "Tradución",
    "Traduccion",
    "Translate",
    "trad",
    "traduccion",
    "traducción",
    "traducción ",
    "Traducción",
    "Traducción español",
    "Traduction",
    "translation",
    "translations",
    "Translation",
    "xe",
    "翻译",
]


acceptable_transcription_tier_types = [
    "arta",
    "Arta",
    "conversación",
    "default-lt",  # needs qualification
    "default-lt",
    "Dusun",
    "Fonética",
    "Frases",
    "Hablado",
    "Hakhun orthography",
    "Hija",
    "hija",
    "ilokano",
    "interlinear-text-item",
    "Ikaan sentences",
    "Khanty Speech",
    "main-tier",
    "Madre",
    "madre",
    "Matanvat text",
    "Matanvat Text",
    "Nese Utterances",
    "o",
    "or",
    "orth",
    "orthT",
    "orthografia",
    "orthografía",
    "orthography",
    "othography",  # sic
    "po",
    "po (practical orthography)",
    "phrase",
    "phrase-item",
    "Phrases",
    "Practical Orthography",
    "sentence",
    "sentences",
    "speech",
    "Standardised-phonology",
    "Sumi",
    "t",  # check this
    "Tamang",
    "texo ",
    "text",
    "Text",
    "Text ",
    "texto",
    "Texto",
    "texto ",
    "Texto principal",
    "Texto Principal",
    "tl",  # check this
    "time aligned",  # check this
    "timed chunk",
    "tl",  # check this
    "Transcribe",
    "Transcrição",
    "TRANSCRIÇÃO",
    "Transcript",
    "Transcripción chol",
    "transcripción chol",
    "Transcripción",
    "Transcripcion",
    "transcripción",
    "Transcripcion chol",
    "transcript",
    "Transcription",
    "transcription",
    "transcription_orthography",
    "trs",
    "trs@",
    "trs1",
    "tx",  # check usages of this
    "tx2",  # check usages of this
    "txt",
    "type_utterance",
    "unit",  # some Dutch texts from TLA
    "ut",
    "utt",
    "Utterance",
    "utterance",
    "uterrances",  # sic
    "utterances",
    "utterrances",  # sic
    "Utterances",
    "utterance transcription",
    "UtteranceType",
    "vernacular",
    "Vernacular",
    "vilela",
    "Vilela",
    "word-txt",
    #'Word', #probably more often used for glossing
    #'word', #probably more often used for glossing
    "word_orthography",
    #'words', #probably more often used for glossing
    #'Words', #more often used for glossing
    "xv",
    "default transcript",
    "句子",
    "句子 ",
    "句子 ",
]

acceptable_word_tier_types = [
    "Word",
    "word",
    "Words",
    "words",
    "word-item",
    "morpheme",
    "morphemes",
    "mb",
    "mb (morpheme boundaries)",
    "Morpheme Break",
    "m",
    "morph",
    "mph",
    "wordT",
    "word-txt",
]

acceptable_gloss_tier_types = [
    "ge",
    "morph-item",
    "gl",
    "Gloss",
    "gloss",
    "glosses",
    "word-gls",
    "gl (interlinear gloss)",
]

acceptable_pos_tier_types = ["ps", "parts of speech"]


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
