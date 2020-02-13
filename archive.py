"""
An archive with primary material in and about endangered languages
"""

import glob
import json
import pprint
import datetime
import re
import urllib
from collections import Counter, defaultdict
from lxml.html.soupparser import fromstring

from rdflib import Namespace, Graph, Literal, RDF, RDFS #, URIRef, BNode

# from random import shuffle
import matplotlib.pyplot as plt
from matplotlib import cm
import squarify

from collection import Collection
import lod

# from collections import defaultdict


class Archive:
    FILETYPES = {
        "ELAN": "text/x-eaf+xml",
        "Toolbox": "text/x-toolbox-text",
        "transcriber": "text/x-trs",
        "praat": "text/praat-textgrid",
        "Flex": "FLEx",
    }

    def __init__(self, name, url, collectionprefix="", collection_url_template=""):
        self.name = name
        self.url = url
        self.collectionprefix = collectionprefix
        self.collections = {}
        self.collection_url_template = collection_url_template
        self.statistics = {}
        self.fingerprints = {}

    def populate_collections(self):
        """read all the files for this collection"""

        if self.name in ("PARADISEC", "ELAR", "TLA", "AILLA"):
            print("loading cached information")
            try:
                with open("cache/links/%s.json"%self.name.lower()) as json_in:
                    cached_links = json.loads(json_in.read())
            except IOError:
                cached_links = {}
                print(
                    r"""please download files from the PARADISEC archive
via
> wget -O paradisec.html "https://catalog.paradisec.org.au/items/search?page=1&per_page=18347"
> grep '<a href="/collections' paradisec.html |grep -o '".*"'|grep -o '[^"]*'| sed "s/\//https:\/\/catalog.paradisec.org.au\//"> itemlist
> wget -w 5 -i itemlist
""",
"""please download files from the ELAR archive"""
"""please download files from the TLA archive"""
                )
            landingpage_template = "https://catalog.paradisec.org.au/collections/%s"
            #landingpage_template = "https://archive.mpi.nl/islandora/object/%s"
            #landingpage_template = "https://elar.soas.ac.uk/Collection/%s"
            #landingpage_template = "https://ailla.utexas.org/islandora/object/%s"
            print('done')
            for collection in cached_links:
                self.collections[collection] = Collection(
                    collection,
                    landingpage_template % collection,
                    archive=self.name.lower(),
                    urlprefix=self.collectionprefix,
                    url_template=self.collection_url_template,
                )
                self.collections[collection].elanpaths = [
                    path
                    for bundle in cached_links[collection]
                    for path in cached_links[collection][bundle]
                ]

        if self.name == "ANLA":
            #print("loading cached information")
            try:
                with open("cache/links/anla.json") as json_in:
                    cached_links = json.loads(json_in.read())
            except IOError:
                cached_links = {}
            html_files = glob.glob("anla/*html")
            landingpage_template = "https://www.uaf.edu/anla/collections/search/resultDetail.xml?resource=%s"
            print("reading files")
            for f in html_files:
                if f in cached_links:
                    # we already haveinformation about this file
                    if cached_links[f] == {}:
                        continue
                    # transfer information
                    for collection in cached_links[f]:
                        self.collections[collection] = Collection(
                            collection, "url", archive="anla"
                        )
                        self.collections[collection].elanpaths = cached_links[f][
                            collection
                        ]

                # print(f,anla_ID)
                # landingpage = landingpage_template % anla_ID
                else:
                    #anla_ID = f[5:-5]  # get rid of "anla/" and ".html"
                    with open(f, encoding="iso8859-1") as c:
                        content = c.read()
                        # print(len(content))
                        try:
                            root = fromstring(content)
                        except ValueError:
                            print(f, "is not valid XML")
                            continue
                        cached_links[f] = {}
                        for link in root.findall(".//td/a"):
                            href = link.attrib.get("href", "")
                            if href.endswith("eaf"):
                                #flag = True
                                collection, eaf_file = href.split("/")[-2:]
                                try:
                                    self.collections[collection].elanpaths.append(
                                        eaf_file
                                    )
                                except KeyError:
                                    self.collections[collection] = Collection(
                                        collection, "url", archive="anla"
                                    )  # TODO check for mutliple eaf files
                                    self.collections[collection].elanpaths = [eaf_file]
                                try:
                                    cached_links[f][collection].append(eaf_file)
                                except:
                                    cached_links[f][collection] = [eaf_file]

            print("updating cache")
            with open("cache/links/anla.json", "w") as json_out:
                json_out.write(json.dumps(cached_links, sort_keys=True, indent=4))

    def get_fingerprints(self):
        """map filenames to fingerprints"""
        fingerprintd = {
            "%s/%s" % (self.name, eaf.path): eaf.fingerprint()
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
        plt.savefig("tiertypetreemap-%s.png" % self.name)
        with open("tierranks-%s.txt" % self.name, "w") as out:
            out.write("\n".join(["%s:%s" % x for x in ranks]))
        self.fingerprints = fingerprintd

    def print_metadata(self):
        """print aggregated information about tranlations, transcriptions and glosses
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
        ).split(".")[0]
        self.statistics.update(d)

    #def getIdentifiers(self, filename, typ):
        #tree = etree.parse(filename)
        #etree.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
        ## retrieve all tags <dc:format>
        #dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
        ##retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
        #identifiers = []
        #for dcformat in dcformats:
            #if dcformat.text == typ:
                #identifiers = dcformat.findall(
                    #"../{http://purl.org/dc/elements/1.1/}identifier"
                #)
                #return identifiers

    #def retrieve(self, xmlfiles, mimetype):
        ## retrieve all identifiers found in the xml files which include relevant mimetype
        #globalidentifiers = [self.getIdentifiers(x, mimetype) for x in xmlfiles]
        ## remove empty return values
        #records = [x for x in globalidentifiers if x != None]
        ## flatten out tuples of multiple identifiers contained in one file
        #IDs = [x2.text for x in records for x2 in x]
        #print(
            #"found %i IDs (%i records) with references to %s files"
            #% (len(IDs), len(records), mimetype)
        #)
        #return IDs, records

    #def scan(self, d, xmlfiles, filetypes):
        #print("Scanning %s" % d)
        #for filetype in filetypes:
            #IDs, records = self.retrieve(xmlfiles, filetypes[filetype])

    #def olaceaf(self, xmlfile, typ):
        #tree = etree.parse(xmlfile)
        #etree.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
        #globalidentifiers = []
        #dico = defaultdict(list)
        ## retrieve all tags <dc:format>
        #dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
        #retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
        #print(len(dcformats))
        #for dcformat in dcformats:
            #if dcformat.text.strip() == typ:
                #identifiers = dcformat.getparent().findall(
                    #".//{http://purl.org/dc/elements/1.1/}identifier"
                #)
                #globalidentifiers.append(identifiers)
        #records = [x for x in globalidentifiers if x != None]
        ## flatten out tuples of multiple identifiers contained in one file
        #for IDs in records:
            #for item in IDs:  # etree.findall returns list
                #dico[0].append(item.text.strip().replace("<", "").replace(">", ""))

    def write_transcriptions_rdf(self):
        ID_template = "%s-%s-%s-%s"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for c in self.collections:
            for eaf in self.collections[c].transcriptions:
                hashed_eaf = hash(eaf)
                eaf_id = eaf_template%(c, hashed_eaf)
                for i,tier in enumerate(self.collections[c].transcriptions[eaf]):
                    for j,annotation in enumerate(tier):
                        tier_id = ID_template % (c, hashed_eaf, i, j)
                        g.add((lod.QUESTRESOLVER[tier_id], #TODO better use archive specific resolvers
                                RDF.type,
                                lod.QUEST.Transcripton_tier
                              ))
                        g.add((lod.QUESTRESOLVER[tier_id],
                               RDFS.label,
                               Literal('%s'%annotation.strip())
                               ))
                        g.add((lod.QUESTRESOLVER[tier_id],
                                lod.DBPEDIA.isPartOf, #check for tier-file, file-collection and tier-collection meronymic relations
                                lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id]
                              ))
        lod.write_graph(g, 'rdf/%s-transcriptions.n3'%self.name)

    def write_translations_rdf(self):
        ID_template = "%s-%s-%s-%s"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for c in self.collections:
            for eaf in self.collections[c].translations:
                hashed_eaf = hash(eaf)
                eaf_id = eaf_template%(c, hashed_eaf)
                for i,tier in enumerate(self.collections[c].translations[eaf]):
                    for j,annotation in enumerate(tier):
                        tier_id = ID_template % (c, hashed_eaf, i, j)
                        g.add((lod.QUESTRESOLVER[tier_id], #TODO better use archive specific resolvers
                                RDF.type,
                                lod.QUEST.Transcripton_tier
                              ))
                        g.add((lod.QUESTRESOLVER[tier_id],
                               RDFS.label,
                               Literal('%s'%annotation.strip())
                               ))
                        g.add((lod.QUESTRESOLVER[tier_id],
                                lod.DBPEDIA.isPartOf, #check for tier-file, file-collection and tier-collection meronymic relations
                                lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id]
                              ))
        lod.write_graph(g, 'rdf/%s-translations.n3'%self.name)

    def write_glosses_rdf(self):
        ID_template = "%s-%s-%s"
        gloss_template = "%s-%s-%s-%s"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for c in self.collections:
            for eaf in self.collections[c].glosses:
                hashed_eaf = hash(eaf)
                eaf_id = eaf_template%(c, hashed_eaf)
                for tiertype in self.collections[c].glosses[eaf]:
                    for tierID in self.collections[c].glosses[eaf][tiertype]:
                        for dictionary  in self.collections[c].glosses[eaf][tiertype][tierID]:
                            for sentenceID in dictionary:
                                sentence_lod_ID = ID_template % (c, hashed_eaf, sentenceID)
                                g.add((lod.QUESTRESOLVER[sentence_lod_ID], #TODO better use archive specific resolvers
                                    RDF.type,
                                    lod.QUEST.Transcripton_tier
                                    ))
                                #wordstring = " ".join([t[0] for t in dictionary[sentenceID]])
                                #glossstring = " ".join([t[1] for t in dictionary[sentenceID]])
                                g.add((lod.QUESTRESOLVER[sentence_lod_ID],
                                    lod.DBPEDIA.isPartOf,
                                    lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id]
                                ))
                                glosses = [t[1] for t in dictionary[sentenceID] if t[1]]
                                for i, gloss in enumerate(glosses):
                                    try:
                                        gloss = gloss.strip()
                                    except TypeError:
                                        gloss = ''
                                    gloss_id = urllib.parse.quote(gloss_template % (c, hashed_eaf, sentenceID, i))
                                    g.add((lod.QUESTRESOLVER[gloss_id],
                                            RDF.type,
                                            lod.QUEST.gloss
                                        ))
                                    g.add((lod.QUESTRESOLVER[gloss_id],
                                            RDFS.label,
                                            Literal(gloss)
                                        ))
                                    g.add((lod.QUESTRESOLVER[gloss_id],
                                           lod.DBPEDIA.isPartOf,
                                           lod.QUESTRESOLVER[sentence_lod_ID]
                                        ))
                                    for subgloss in re.split("[-=.:]", gloss):
                                        subgloss = subgloss.replace("1",'').replace("2",'').replace("3",'')
                                        if subgloss in lod.LGRLIST:
                                            g.add((lod.QUESTRESOLVER[gloss_id],
                                                lod.QUEST.has_lgr_value,
                                                lod.LGR[subgloss]
                                            ))
        lod.write_graph(g, 'rdf/%s-glosses.n3'%self.name)


    def write_entities_rdf(self):
        ID_template = "%s-%s-%s"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for c in self.collections:
            for eaf in self.collections[c].entities:
                hashed_eaf = hash(eaf)
                eaf_id = eaf_template%(c, hashed_eaf)
                for i,tier in enumerate(self.collections[c].entities[eaf]):
                    tier_id = ID_template % (c, hashed_eaf, i)
                    for q_value in tier:
                        g.add((lod.QUESTRESOLVER[tier_id], #TODO better use archive specific resolvers
                                lod.DC.topic,
                                lod.WIKIDATA[q_value]
                              ))
        lod.write_graph(g, 'rdf/%s-entities.n3'%self.name)
