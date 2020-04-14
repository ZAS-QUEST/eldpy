"""
A collection with primary material in and about endangered languages.
"""

import re
import pprint
import os.path
import logging
import json
from lxml.etree import XMLSyntaxError
from lxml.html.soupparser import fromstring
import requests
from elanfile import ElanFile
import lod

logger = logging.getLogger("eldpy")
logger.setLevel(logging.ERROR)


class Collection:
    def __init__(self,
                 name,
                 url,
                 namespace=None,
                 archive="",
                 urlprefix="",
                 url_template=""
                ):
        self.name = name
        self.archive = archive
        self.url = url
        self.urlprefix = urlprefix
        self.url_template = url_template
        self.ID = ""
        self.cacheprefix = "cache/eafs/%s" % self.archive.lower()
        self.elanpaths = []
        self.elanfiles = []
        self.translations = {}
        self.transcriptions = {}
        self.glosses = {}
        self.namespace = namespace

        self.transcriptionfiles = 0
        self.transcriptiontiers = 0
        self.transcriptionwords = 0
        self.transcribedseconds = 0

        self.translationfiles = 0
        self.translationtiers = 0
        self.translationwords = 0

        self.glossfiles = 0
        self.glosstiers = 0
        self.glosssentences = (
            0  # check for sentences with more than one gloss tiere TODO
        )
        self.glosswords = 0
        self.glossmorphemes = 0
        self.fingerprints = []

    def acquire_elans(self, cache=True):
        # print(self.elanpaths)
        for path in self.elanpaths:
            localpath = "/".join((self.cacheprefix, path))
            eaf_url = "/".join((self.urlprefix, self.name, path))
            print(".", end="", flush=True)
            if os.path.isfile(localpath):
                try:
                    self.elanfiles.append(ElanFile(localpath, eaf_url))
                except XMLSyntaxError:
                    logger.warning("malformed XML in %s" % localpath)
            else:
                logger.warning("file not found %s (remote %s)" % (localpath, eaf_url))

    def populate_translations(self, jsoncache=None):
        if jsoncache:
            self.translations = jsoncache[self.name]
        else:
            for eaf in self.elanfiles:
                eaf.populate_translations()
                translations = eaf.get_translations()
                counts = [len(t) for t in translations]
                if translations:
                    # print(counts)
                    self.translationfiles += 1
                    self.translationtiers += len(counts)
                    self.translationwords += sum(counts)
                self.translations[eaf.path] = translations

    def populate_transcriptions(self, jsoncache=None):
        if jsoncache:
            self.transcriptions = jsoncache[self.name]
        else:
            for eaf in self.elanfiles:
                logging.info("transcriptions for", eaf.path)
                eaf.populate_transcriptions()
                transcriptions = eaf.get_transcriptions()
                counts = [len(t) for t in transcriptions]
                logging.info(
                    "  number of words in transcriptions tiers: %s" % str(counts)
                )
                if transcriptions:
                    self.transcriptionfiles += 1
                    self.transcriptiontiers += len(counts)
                    self.transcriptionwords += sum(counts)
                    self.transcribedseconds += eaf.secondstranscribed
                self.transcriptions[eaf.path] = transcriptions

    def populate_glosses(self, jsoncache=None):
        if jsoncache:
            self.glosses = jsoncache[self.name]
        else:
            logging.info("getting glosses for %i elans" % len(self.elanfiles))
            filecount = 0
            tiercount = 0
            sentencecount = 0
            wordcount = 0
            morphemecount = 0
            for eaf in self.elanfiles:
                eaf.populate_glosses()
                glossed_sentences = eaf.glossed_sentences
                if glossed_sentences == []:
                    continue
                filecount += 1
                for tiertype in glossed_sentences:
                    for tierID in glossed_sentences[tiertype]:
                        tiercount += 1
                        for dictionary in glossed_sentences[tiertype][tierID]:
                            for sentence_ID in dictionary:
                                sentencecount += 1
                                # TODO check for double counting for different tiers
                                try:
                                    words = dictionary[sentence_ID]
                                except IndexError:
                                    continue
                                for pairing in words:
                                    wordcount += 1
                                    morphemecount += 1
                                    # every extra morpheme is marked by a separator
                                    # like - or = in the gloss
                                try:
                                    morphemecount += len(
                                        re.findall("[-=.:]", pairing[1])
                                    )
                                except TypeError:  # gloss None
                                    pass
                self.glosses[eaf.path] = glossed_sentences

            self.glossfiles += filecount
            self.glosstiers += tiercount
            self.glosssentences += sentencecount
                # check for sentences with more than one gloss tiere TODO
            self.glosswords += wordcount
            self.glossmorphemes += morphemecount

    def populate_entities(self, jsoncache=None):
        def get_entities(text):
            """sent text to online resolver and retrieve wikidataId's"""

            url = "http://cloud.science-miner.com/nerd/service/disambiguate"
            if len(text.split()) < 5:  # cannot do NER on less than 5 words
                return []
            # send text
            rtext = requests.post(url, json={"text": text}).text
            # parse json
            if rtext == None:
                return {}
            retrieved_entities = json.loads(rtext).get("entities", [])
            # extract names and wikidataId's
            return {x["wikidataId"]: x["rawName"]
                    for x in retrieved_entities
                    if x.get("wikidataId") and x["wikidataId"] not in lod.NER_BLACKLIST
                   }

        if jsoncache:
            self.entities = jsoncache[self.name]
        else:
            entities = {}
            translations = self.translations
            if translations == {}:
                translations = self.populate_translations()
            if translations is None:
                translations = {}
            for eaf in translations:
                entities[eaf] = []
                for tier in translations[eaf]: #some files have more than one translation tier
                    text = " ".join(tier)
                    entities[eaf].append(get_entities(text))
            self.entities = entities


    def get_fingerprints(self):
        logging.info("getting fingerprints for %i elans" % len(self.elanfiles))
        self.fingerprints = [eaf.fingerprint() for eaf in self.elanfiles]

    def paradisec_eaf_download(self, filename):
        # compute urls to use
        # PARADISEC has a naming scheme for URLs which can be inferred
        # from eaf file names.
        archive_url = "http://catalog.paradisec.org.au/repository/%s/%s/%s"
        first, second, thirdthrowaway = filename.split("-")
        url = archive_url % (first, second, filename)
        with requests.Session() as s:
            eafcontent = s.post(url, cookies=cookie).text
        # abort if fetched data is HTML because this is an error message
        if eafcontent.startswith("<!DOCTYPE html>"):
            # print("no access")
            return None
        return eafcontent

