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


# from random import shuffle
import matplotlib.pyplot as plt
from matplotlib import cm
import squarify
from rdflib import Namespace, Graph, Literal, RDF, RDFS  # , URIRef, BNode

from .collection import Collection
from . import lod

# from collections import defaultdict


class Archive:
    FILETYPES = {
        "ELAN": "text/x-eaf+xml",
        "Toolbox": "text/x-toolbox-text",
        "transcriber": "text/x-trs",
        "praat": "text/praat-textgrid",
        "Flex": "FLEx",
    }

    def __init__(self,
                 name,
                 url,
                 collectionprefix="",
                 collection_url_template="",
                 landingpage_template="%s",
                ):
        self.name = name
        self.url = url
        self.collectionprefix = collectionprefix
        self.collections = {}
        self.collection_url_template = collection_url_template
        self.statistics = {}
        self.fingerprints = {}
        self.landingpage_template = landingpage_template

    def populate_collections(self, cache=True):
        """read all the files for this collection"""
        if cache:
            if self.name in ("PARADISEC", "ELAR", "TLA", "AILLA"):
                print("loading cached information")
                try:
                    with open("cache/links/%s.json" % self.name.lower()) as json_in:
                        cached_links = json.loads(json_in.read())
                except IOError:
                    cached_links = {}
                    print(
                        "No cached information available. Please download files from %s archive via bulk_download"
                        % self.name
                    )
                    return
                print("done")
                for collection in cached_links:
                    self.collections[collection] = Collection(
                        collection,
                        self.landingpage_template % collection,
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
                # print("loading cached information")
                try:
                    with open("cache/links/anla.json") as json_in:
                        cached_links = json.loads(json_in.read())
                except IOError:
                    cached_links = {}
                html_files = glob.glob("anla/*html")
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
                        # anla_ID = f[5:-5]  # get rid of "anla/" and ".html"
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
                                    # flag = True
                                    collection, eaf_file = href.split("/")[-2:]
                                    try:
                                        self.collections[collection].elanpaths.append(
                                            eaf_file
                                        )
                                    except KeyError:
                                        self.collections[collection] = Collection(
                                            collection, "url", archive="anla"
                                        )  # TODO check for mutliple eaf files
                                        self.collections[collection].elanpaths = [
                                            eaf_file
                                        ]
                                    try:
                                        cached_links[f][collection].append(eaf_file)
                                    except:
                                        cached_links[f][collection] = [eaf_file]

                print("updating cache")
                with open("cache/links/anla.json", "w") as json_out:
                    json_out.write(json.dumps(cached_links, sort_keys=True, indent=4))
        else:  # if not cache
            if self.name in ["PARADISEC","PARADISEC2"]:  # to be extended
                collections = glob.glob("./%s/*" % self.name.lower())
                for collection in collections:
                    collectionbasename = collection.split("/")[-1]
                    #print(collectionbasename)
                    self.collections[collectionbasename] = Collection(
                        collectionbasename,
                        self.landingpage_template % collectionbasename,
                        archive=self.name.lower(),
                        urlprefix=self.collectionprefix,
                        url_template=self.collection_url_template,
                    )
                    filenames = glob.glob("%s/*eaf" % collection)
                    paradisecpaths = defaultdict(list)
                    for filename in filenames:
                        basename = filename.split("/")[-1]
                        collectionthrowaway, bundle, recordingthrowaway = basename.split("-")
                        #print(collectionbasename, bundle, basename)
                        paradisecpaths[bundle].append(basename)
                self.collections[collectionbasename].elanpaths = paradisecpaths
            if self.name in ["TLA","TLA2"]:  # to be extended
                collections = glob.glob("./%s/*" % self.name.lower())
                #print(collections)
                for collection in collections:
                    collectionbasename =  collection.split("/")[-1]
                    #print(collectionbasename)
                    self.collections[collectionbasename] = Collection(
                        collectionbasename,
                        self.landingpage_template % collectionbasename,
                        archive=self.name.lower(),
                        urlprefix=self.collectionprefix,
                        url_template=self.collection_url_template,
                    )
                    filenames = glob.glob("%s/*eaf" % collection)
                    tlapaths = defaultdict(list)
                    for filename in filenames:
                        basename = filename.split("/")[-1]
                        bundle = collectionbasename #we treat TLA as having collections with exactly 1 member for the time being.
                        #print(collectionbasename, bundle, basename)
                        #print(basename, basename)
                        tlapaths[bundle].append(basename)
                    #pprint.pprint(tlapaths)
                    #pprint.pprint(self.collections[collectionbasename].__dict__)
                #print(6)
                self.collections[collectionbasename].elanpaths = tlapaths
                #pprint.pprint(self.collections[collectionbasename].elanpaths)
            if self.name in ["ELAR","ELAR2"]:  # to be extended
                collections = glob.glob("./%s/*" % self.name.lower())
                #print(collections)
                for collection in collections:
                    collectionbasename =  collection.split("/")[-1]
                    #print(collectionbasename)
                    self.collections[collectionbasename] = Collection(
                        collectionbasename,
                        self.landingpage_template % collectionbasename,
                        archive=self.name.lower(),
                        urlprefix=self.collectionprefix,
                        url_template=self.collection_url_template,
                    )
                    filenames = glob.glob("%s/*eaf" % collection)
                    tlapaths = defaultdict(list)
                    for filename in filenames:
                        basename = filename.split("/")[-1]
                        bundle = collectionbasename #we treat ELAR as having collections with exactly 1 member for the time being.
                        #print(collectionbasename, bundle, basename)
                        #print(basename, basename)
                        tlapaths[bundle].append(basename)
                    #pprint.pprint(tlapaths)
                    #pprint.pprint(self.collections[collectionbasename].__dict__)
                #print(6)
                self.collections[collectionbasename].elanpaths = tlapaths
                #pprint.pprint(self.collections[collectionbasename].elanpaths)
            if self.name in ["AILLA","AILLA2"]:  # to be extended
                collections = glob.glob("./%s/*" % self.name.lower())
                for collection in collections:
                    collectionbasename = collection.split("/")[-1]
                    #print(collectionbasename)
                    self.collections[collectionbasename] = Collection(
                        collectionbasename,
                        self.landingpage_template % collectionbasename,
                        archive=self.name.lower(),
                        urlprefix=self.collectionprefix,
                        url_template=self.collection_url_template,
                    )
                    filenames = glob.glob("%s/*eaf" % collection)
                    aillapaths = defaultdict(list)
                    for filename in filenames:
                        basename = filename.split("/")[-1]
                        bundle = collectionbasename
                        #print(collectionbasename, bundle, basename)
                        aillapaths[bundle].append(basename)
                self.collections[collectionbasename].elanpaths = aillapaths

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
        ).split(".")[0]
        self.statistics.update(d)

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
    #% (len(IDs), len(records), mimetype)
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

    def write_metadata_rdf(self):
        archive = self.name
        eaf_template = "%s-%s"
        g = lod.create_graph()
        g.add((lod.QUESTRESOLVER[archive], RDF.type, lod.QUEST.Archive))
        for collection in self.collections:
            g.add((lod.QUESTRESOLVER[collection], RDF.type, lod.QUEST.Collection))
            g.add(
                (
                    lod.QUESTRESOLVER[collection],
                    lod.DBPEDIA.isPartOf,
                    lod.QUESTRESOLVER[archive],
                )
            )
            # print(collection, len(self.collections[collection].elanfiles))
            for eafname in self.collections[collection].elanfiles:
                hashed_eaf = self.get_eaf_hash(eafname.url)
                eaf_id = eaf_template % (collection, hashed_eaf)
                g.add(
                    (
                        lod.QUESTRESOLVER[
                            eaf_id
                        ],  # TODO better use archive specific resolvers
                        RDF.type,
                        # lod.QUEST.Elan_file
                        lod.LIGT.InterlinearText,
                    )
                )
                g.add((lod.QUESTRESOLVER[eaf_id], RDFS.label, Literal(eafname)))
                g.add(
                    (
                        lod.QUESTRESOLVER[eaf_id],
                        lod.DBPEDIA.isPartOf,
                        lod.QUESTRESOLVER[collection],
                    )
                )
        lod.write_graph(g, "rdf/%s-metadata.n3" % self.name)

    def get_eaf_hash(self, eafname):
        eafbasename = eafname.split("/")[-1]
        hashed_eaf = str(hash(eafbasename))[-7:]

        return hashed_eaf

    def write_transcriptions_rdf(self):
        ID_template = "%s-%s-transcription-%s-%s"
        # FIXME transcriptions and translations should probably point to the same tier
        # but we must make sure that he offsets match. Better use the annotation_ID of the time-aligned ancestor, which should be shared
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for collection in self.collections:
            collection_id = self.collections[collection].ID
            for eafname in self.collections[collection].transcriptions:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection_id, hashed_eaf)
                for i, tier in enumerate(self.collections[collection].transcriptions[eafname]):
                    for j, annotation in enumerate(tier):
                        tier_id = ID_template % (collection_id, hashed_eaf, i, j)
                        g.add(
                            (
                                lod.QUESTRESOLVER[
                                    tier_id
                                ],  # TODO better use archive specific resolvers
                                RDF.type,
                                # lod.QUEST.Transcripton_tier
                                lod.LIGT.Utterance,
                            )
                        )
                        g.add(
                            (
                                lod.QUESTRESOLVER[tier_id],
                                RDFS.label,
                                Literal(
                                    "%s" % annotation.strip(), lang="und"
                                ),  # we use und_efined until we can retrieve metatdata
                            )
                        )
                        g.add(
                            (
                                lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id],
                                lod.LIGT.hasTier,  # check for tier-file, file-collection and tier-collection meronymic relations
                                lod.QUESTRESOLVER[tier_id],
                            )
                        )
        lod.write_graph(g, "rdf/%s-transcriptions.n3" % self.name)

    def write_translations_rdf(self):
        ID_template = "%s-%s-translation-%s-%s"
        eaf_template = "%s-%s"
        # FIXME transcriptions and translations should probably point to the same tier
        # but we must make sure that he offsets match. Better use the annotation_ID of the time-aligned ancestor, which should be shared
        g = lod.create_graph()
        for collection in self.collections:
            for eafname in self.collections[collection].translations:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection, hashed_eaf)
                for i, tier in enumerate(self.collections[collection].translations[eafname]):
                    for j, annotation in enumerate(tier):
                        tier_id = ID_template % (collection, hashed_eaf, i, j)
                        g.add(
                            (
                                lod.QUESTRESOLVER[
                                    tier_id
                                ],  # TODO better use archive specific resolvers
                                RDF.type,
                                # lod.QUEST.Translation_tier
                                lod.LIGT.Utterance,
                            )
                        )
                        g.add(
                            (
                                lod.QUESTRESOLVER[tier_id],
                                RDFS.label,
                                Literal("%s" % annotation.strip(), lang="eng"),
                            )
                        )
                        g.add(
                            (
                                lod.QUESTRESOLVER[tier_id],
                                lod.LIGT.subSegment,  # check for tier-file, file-collection and tier-collection meronymic relations
                                lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id],
                            )
                        )
        lod.write_graph(g, "rdf/%s-translations.n3" % self.name)

    def write_glosses_rdf(self):
        #https://github.com/acoli-repo/ligt/blob/master/samples/nordhoff-1.ttl
        example_ID_template = "%s-%s-%s_u"
        word_tier_ID_template = "%s-%s-%s_wt"
        morph_tier_ID_template = "%s-%s-%s_mt"
        word_template = "%s-%s-%s-%s_w"
        morph_ID_template = "%s-%s-%s-%s_m"
        gloss_template = "%s-%s-%s-%s_g"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        g.add((lod.QUEST.morph2,#TODO needs better label
                lod.RDFS.subPropertyOf,
                lod.LIGT.annotation
                ))
        g.add((lod.QUEST.gloss2, #TODO needs better label
                lod.RDFS.subPropertyOf,
                lod.LIGT.annotation
                ))
        for collection in self.collections:
            for eafname in self.collections[collection].glosses:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection, hashed_eaf)
                for tiertype in self.collections[collection].glosses[eafname]:
                    for tierID in self.collections[collection].glosses[eafname][tiertype]:
                        for dictionary in self.collections[collection].glosses[eafname][tiertype][tierID]:
                            for sentenceID in dictionary:
                                example_block_ID = example_ID_template % (collection, hashed_eaf, sentenceID)
                                sentence_word_tier_lod_ID = word_tier_ID_template % (collection, hashed_eaf, sentenceID)
                                sentence_morph_tier_lod_ID = word_tier_ID_template % (collection, hashed_eaf, sentenceID)
                                wordstring = " ".join(['' if t[0] is None else t[0] for t in dictionary[sentenceID]])
                                glossstring = " ".join(['' if t[1] is None else t[1] for t in dictionary[sentenceID]])
                                example_block_nif_label =  wordstring
                                words_nif_label =  wordstring
                                vernacular_language_id = "und"
                                gloss_language_id = "en-x-lgr"
                                g.add((lod.ARCHIVE_NAMESPACES[self.name.lower()][eaf_id],
                                        lod.LIGT.hasTier,
                                        lod.QUESTRESOLVER[example_block_ID],
                                    ))
                                #example block (=utterance in LIGT lingo)
                                g.add((lod.QUESTRESOLVER[example_block_ID],
                                       # TODO better use archive specific resolvers
                                       RDF.type,
                                       lod.LIGT.InterlinearText
                                     ))
                                g.add((lod.QUESTRESOLVER[example_block_ID],
                                       RDF.type,
                                       lod.LIGT.Utterance
                                     ))
                                g.add((lod.QUESTRESOLVER[example_block_ID],
                                       lod.NIF.anchorOf,
                                       Literal(example_block_nif_label, lang=vernacular_language_id),
                                     ))
                                g.add((lod.QUESTRESOLVER[example_block_ID],
                                       lod.LIGT.hasTier,
                                       lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                                     ))
                                g.add((lod.QUESTRESOLVER[example_block_ID],
                                       lod.LIGT.hasTier,
                                       lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                                     ))
                                #words
                                g.add((lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                                       RDF.type,
                                       lod.LIGT.WordTier,
                                     ))
                                g.add((lod.QUESTRESOLVER[sentence_word_tier_lod_ID],
                                       lod.NIF.anchorOf,
                                       Literal(example_block_ID, lang=vernacular_language_id),
                                     ))
                                #morphs
                                g.add((lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                                       RDF.type,
                                       lod.LIGT.MorphTier,
                                     ))
                                g.add((lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                                       lod.NIF.anchorOf,
                                       Literal(example_block_ID, lang=vernacular_language_id),
                                     ))
                                #subelements of word, morph and gloss tier
                                #TODO unclear whether we need word tier
                                morphs = [t[0] if t[0] else "" for t in dictionary[sentenceID]]
                                glosses = [t[1] if t[1] else "" for t in dictionary[sentenceID]]
                                for i in range(len(morphs)):
                                    morph = morphs[i]
                                    morph_id = morph_ID_template % (
                                                collection,
                                                hashed_eaf,
                                                sentenceID,
                                                i,
                                            )
                                    gloss = glosses[i]
                                    try:
                                        gloss = gloss.strip()
                                    except TypeError:
                                        gloss = ""
                                    #add items to tier
                                    g.add((lod.QUESTRESOLVER[sentence_morph_tier_lod_ID],
                                        lod.LIGT.item,
                                        lod.QUESTRESOLVER[morph_id]
                                        ))
                                    #anchor in superstring about items
                                    g.add((lod.QUESTRESOLVER[morph_id],
                                        lod.NIF.anchorOf,
                                        lod.QUESTRESOLVER[sentence_word_tier_lod_ID] #TODO this should probably sentence_word_id, but we have no notion of "word" right now, hence resorting to a larger substring
                                        ))
                                    #forward link to create linked list
                                    try:
                                        nextmorph = morphs[i + 1]
                                        nextmorph_id = urllib.parse.quote(
                                            morph_ID_template
                                            % (
                                                collection,
                                                hashed_eaf,
                                                sentenceID,
                                                i + 1,
                                            )
                                        )
                                        g.add((lod.QUESTRESOLVER[morph_id],
                                               lod.LIGT.nextWord,
                                               lod.QUESTRESOLVER[nextmorph_id]
                                             ))
                                    except IndexError:  # we have reached the end of the list
                                        g.add((lod.QUESTRESOLVER[nextmorph_id],
                                               lod.LIGT.nextWord,
                                               lod.RDF.nil,
                                            ))
                                    #give labels for morphs
                                    g.add((lod.QUESTRESOLVER[morph_id],
                                               lod.QUEST.morph2, #TODO probably use not   "morph2" here
                                               Literal(morph, lang=vernacular_language_id),
                                            ))
                                    g.add((lod.QUESTRESOLVER[morph_id],
                                               lod.QUEST.gloss2, #TODO probably use not   "gloss2" here
                                               Literal(gloss, lang=gloss_language_id)
                                            ))
                                    for subgloss in re.split("[-=.:]", gloss):
                                        subgloss = (
                                            subgloss.replace("1", "")
                                            .replace("2", "")
                                            .replace("3", "")
                                        )
                                        if subgloss in lod.LGRLIST:
                                            g.add((lod.QUESTRESOLVER[morph_id],
                                                   lod.QUEST.has_lgr_value,
                                                   lod.LGR[subgloss]
                                                  ))


                                #TODO not sure in how far the specific ligt modeling from 2019 is needed anymore
                                #for i, gloss in enumerate(glosses):
                                    #vernacular = vernaculars[i]
                                    #try:
                                        #gloss = gloss.strip()
                                    #except TypeError:
                                        #gloss = ""
                                    #gloss_id = urllib.parse.quote(
                                        #gloss_template % (collection, hashed_eaf, sentenceID, i)
                                    #)
                                    #g.add((lod.QUESTRESOLVER[gloss_id],
                                           #RDF.type,
                                           ## lod.QUEST.gloss
                                           #lod.LIGT.Word,
                                         #))
                                    #g.add((lod.QUESTRESOLVER[gloss_id],
                                           #lod.FLEX.gls,
                                           #Literal(gloss, lang="eng"),
                                           ## we use qqq since glossed text is not natural language
                                         #))
                                    #g.add((lod.QUESTRESOLVER[gloss_id],
                                           #lod.FLEX.txt,
                                           #Literal(vernacular, lang="und"),
                                           ## we use "und" until we can retrieve the proper metadata
                                         #))
                                    #g.add((lod.QUESTRESOLVER[sentence_lod_ID],
                                           #lod.LIGT.hasWord,
                                           #lod.QUESTRESOLVER[gloss_id],
                                         #))
        lod.write_graph(g, "rdf/%s-glosses.n3" % self.name)

    def write_entities_rdf(self):
        ID_template = "%s-%s-%s"
        eaf_template = "%s-%s"
        g = lod.create_graph()
        for collection in self.collections:
            for eafname in self.collections[collection].entities:
                hashed_eaf = self.get_eaf_hash(eafname)
                eaf_id = eaf_template % (collection, hashed_eaf)
                for i, tier in enumerate(self.collections[collection].entities[eafname]):
                    tier_id = ID_template % (collection, hashed_eaf, i)
                    g.add((
                        lod.QUESTRESOLVER[tier_id],
                        lod.LIGT.subSegment,
                        lod.QUESTRESOLVER[eaf_id],
                        ))
                    for q_value in tier:
                        g.add((
                            lod.QUESTRESOLVER[tier_id],   # TODO better use archive specific resolvers
                            lod.DC.subject,
                            lod.WIKIDATA[q_value],
                            ))
        lod.write_graph(g, "rdf/%s-entities.n3" % self.name)

    def write_rdf(self):
        print("writing rdf for", self.name)
        print("  meta")
        self.write_metadata_rdf()
        print("  transcriptions")
        self.write_transcriptions_rdf()
        print("  glosses")
        self.write_glosses_rdf()
        print("  translations")
        self.write_translations_rdf()
        print("  entities")
        self.write_entities_rdf()
        print("  done")
