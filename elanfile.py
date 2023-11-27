"""
A representation of an ELAN file
"""

import copy
import json
import logging
import pprint
import re
import requests
from collections import Counter, defaultdict
from lxml import etree
from langdetect import detect_langs, lang_detect_exception
import time
import csv
import io
import sys
import annotation
import constants


logger = logging.getLogger("eldpy")
logger.setLevel(logging.ERROR)


class ElanFile:
    def __init__(self, path, url, namespace=None):
        # self.name = name
        self.path = path
        self.ID = self.path.split("/")[-1]
        self.url = url
        self.namespace = namespace
        self.tiers = []
        self.vernaculartiers = []
        self.translationtiers = []
        self.glosstiers = []
        self.timecodes = {}
        self.reftypes = {}
        self.transcriptions = {}
        self.translations = {}
        self.fingerprint = None
        self.secondstranscribed = 0
        self.secondstranslated = 0
        tmpxml = self.xml()
        self.root = tmpxml
        if self.root is None:
            return None
        self.get_tier_hierarchy()
        self.create_parent_tier_dic()
        try:
            self.timeslots = self.get_timeslots()
        except KeyError:
            self.timeslots = {}
        self.alignable_annotations = {
            el.attrib["ANNOTATION_ID"]: (
                el.attrib["TIME_SLOT_REF1"],
                el.attrib["TIME_SLOT_REF2"],
            )
            for el in tmpxml.findall(".//ALIGNABLE_ANNOTATION")
        }
        self.ref_annotations = {
            el.attrib["ANNOTATION_ID"]: el.attrib["ANNOTATION_REF"]
            for el in tmpxml.findall(".//REF_ANNOTATION")
        }
        self.timeslottedancestors = self.get_timeslotted_parents()
        # print(len(self.timeslottedancestors))
        self.annotationdic = {
            el[0].attrib["ANNOTATION_ID"]: annotation.Annotation(el, self.timeslots, self.ref_annotations, self.alignable_annotations )
            for el in self.root.findall(".//ANNOTATION")
        }

    LANGDETECTTHRESHOLD = 0.95  # 85% seems to have no false positives in a first run

    def __eq__(
        self, other
    ):  # this is needed for some rdflib function which throws unclear errors
        return self.path == other.path

    def __ne__(self, other):
        return not (self == other)

    def __lt__(self, other):
        return self.path < other.path

    def __gt__(self, other):
        return self.path > other.path

    def __le__(self, other):
        return self.path <= other.path

    def __ge__(self, other):
        return self.path >= other.path

    def get_timeslotted_parents(self):
        def get_timeslotted_parent(ID, d):
            parent_id = self.ref_annotations[ID]
            if parent_id in self.alignable_annotations:
                # parent is an alignable_annotation with timecodes
                return parent_id
            elif parent_id in d:
                # we had already established who the ultimate ancestor of the parent is
                d[ID] = d[
                    parent_id
                ]  # the ultimate ancestor or ego is the same as the ua of ego's father
                return d[parent_id]
            else:
                # this parent element is unknown
                return get_timeslotted_parent(parent_id, d)

        d = copy.copy(self.alignable_annotations)
        a = {ra: get_timeslotted_parent(ra, d) for ra in self.ref_annotations}
        return a

    def xml(self):
        try:
            root = etree.parse(self.path)
        except etree.XMLSyntaxError:
            return None
        return root

    def write(self):
        """write the file to the file system"""
        pass

    # def analyze(self, fingerprint=False):
    # """
    # get information about:
    # - number of words
    # - number of glosses
    # - time transcribed
    # etc
    # """
    # if fingerprint:
    # return self.fingerprint()
    # return None

    def get_triples(self, bundle_url=None):
        """
        get RDF triples describing the Resource
        """
        # metadata triples
        # transcription triples
        # translation triples
        # gloss triples
        # NER triples
        pass

    def get_fingerprint(self):
        """
        check the tiers there are in a given file and
        return a fingerprint describing the structure
        Dots indicate the level
        The type of a tier is indicated by
        - s: subdivision
        - a: association
        - x: anything else
        """
        if self.fingerprint:
            return self.fingerprint
        else:
            tree = self.xml()
            # the fingerprint is computed recursively, hence we store it as an attribute
            self.fingerprint = "["
            # start with dummy tier
            self.analyze_tier(
                {"id": self.path, "constraint": "root", "ltype": ""},
                0,
                # lump=lump
            )
            self.fingerprint += "]"
            return self.fingerprint

    def analyze_tier(self, d, level, lump=False):
        """
        analyze a tier and its children

        Recursively analyze a tier and its children for their types.
        Tier types are indicated by the letters x, s(ubdivision), a(ssociation),
        t, i, R, and x.
        The Boolean keyword "lump" will subsume i(nclude in) and t(ime subdivision)
        under s(ubdivision).

        Children are an ordered list, whose start is indicated by [. After the last
        child, the list is closed by ]. Lists can be nested for grandchildren etc.

        The root of the document is indicated by R. Tiers of unkown types are indicated
        by x.

        """
        constraint = d["constraint"]
        code = "x"
        if constraint in ("Symbolic_Subdivision", "Symbolic Subdivision"):
            code = "s"
        elif constraint in ("Symbolic_Association", "Symbolic Association"):
            code = "a"
        elif constraint in ("Time_Subdivision", "Time Subdivision"):
            if lump:
                code = "s"
            else:
                code = "t"
        elif constraint == "Included_In":
            if lump:
                code = "s"
            else:
                code = "i"
        elif constraint == "root":
            code = "R"
        elif constraint == "":
            code = "x"
        elif constraint is None:
            code = "x"
        self.fingerprint += code
        children = self.tier_hierarchy[d["id"]]
        if children == []:
            return
        self.fingerprint += "["
        for child in children:
            self.analyze_tier(child, level + 1, lump=lump)
        self.fingerprint += "]"

    def is_ID_tier(self, wl):
        """
        check for ID tiers.

        ID tiers either have only digits, or they have an ID consisting of the filename
        and a running number. We have to find at least three digits since some tone languages
        use two digit tone indications like "ma24ma52"
        """

        if re.search("[0-9]{3}$", wl[0]) or re.match("[0-9]+", wl[0]):
            if len(wl) > 1:
                if re.search("[0-9]{3}$", wl[1]) or re.match(
                    "[0-9]+", wl[1]
                ):  # this is an ID tier
                    return True

    def get_annotation_list(self, t):
        aas = self.get_alignable_annotations(self.root)
        result = []
        for ref_annotation in t.findall(".//REF_ANNOTATION"):
            if ref_annotation.find(".//ANNOTATION_VALUE").text is not None:
                try:
                    anno = annotation.Annotation(
                        aas.get(ref_annotation.attrib["ANNOTATION_REF"]),
                        self.timeslots,
                        self.ref_annotations,
                        self.alignable_annotations
                    )
                    result.append(anno)
                except ValueError:
                    continue
        return result

    def is_major_language(self, list_, spanish=False, logtype="False"):
        try:  # detect candidate languages and retrieve most likely one
            toplanguage = detect_langs(" ".join(list_))[0]
        except lang_detect_exception.LangDetectException:
            # we are happy that this is an unknown language
            toplanguage = None
        accepted_languages = ["en"]
        if spanish:
            accepted_languages.append("es")
        if (
            toplanguage
            and toplanguage.lang in accepted_languages
            and toplanguage.prob > self.LANGDETECTTHRESHOLD
        ):
            if logtype == "True":
                logger.warning(
                    'ignored vernacular tier with "%s" language content at %.2f%% probability ("%s ...")'
                    % (
                        toplanguage.lang,
                        toplanguage.prob * 100,
                        " ".join(list_)[:100],
                    )
                )
            return True
        if toplanguage is None:
            if logtype == "False":
                logger.warning(
                    "could not detect language for %s in %s" % (list_, self.path)
                )
            return False
        if toplanguage.prob < self.LANGDETECTTHRESHOLD:
            # language is English or Spanish, but likelihood is too small
            if logtype == "False":
                logger.warning(
                    'ignored %.2f%% probability English for "%s ..."'
                    % (toplanguage.prob * 100, " ".join(list_)[:100])
                )
            return False

    def tier_to_wordlist(self, t):
        """
        create a list of all words in that tier by splitting
        and collating all annotation values of that tier
        """

        result = []
        for av in t.findall(".//ANNOTATION_VALUE"):
            try:
                result.append(av.text.strip())
            except AttributeError:
                result.append("")
        return result

    def tier_to_annotation_ID_list(self, t):
        """
        create a list of all IDs in that tier
        """

        return [  # FIXME use generic method
            (ra.attrib["ANNOTATION_ID"], ra.attrib["ANNOTATION_REF"])
            for ra in t.findall(".//REF_ANNOTATION")
        ]

    def get_seconds_from_tier(self, t):
        """
        get a list of duration from the time slots directly mentioned in annotations
        """

        timelist = [
            annotation.Annotation(aa, self.timeslots, self.ref_annotations, self.alignable_annotations).get_duration()
            for aa in t.findall("./ANNOTATION")
            if aa.text is not None
        ]
        timelistannno = [anno.get_duration() for anno in self.get_annotation_list(t)]
        return sum(timelist + timelistannno) / 1000

    def has_minimal_translation_length(self, t, tierID):
        """
        how many words should the average annotation have for this
        tier to be counted as translation?
        Very short stretches are typically not translations but something else
        """

        translation_minimum = 1.5
        avg_annotation_length = sum([len(x.strip().split()) for x in t]) / len(t)
        if avg_annotation_length < translation_minimum:
            logger.warning(
                "%s has too short annotations (%s) for the tier to be a translation (%s ,...)"
                % (tierID, avg_annotation_length, ", ".join(t[:3]))
            )
            return False
        return True

    def populate_transcriptions(self):
        """fill the attribute transcriptions with translations from the ELAN file"""

        transcriptioncandidates = constants.ACCEPTABLE_TRANSCRIPTION_TIER_TYPES
        transcriptions = defaultdict(dict)
        root = self.root
        if root is None:
            self.transcriptions = {}
            return
        # we check the XML file which of the frequent names for transcription tiers it uses
        # there might be several transcription tiers with different names, hence we store them
        # in a dictionary
        time_in_seconds = []
        for candidate in transcriptioncandidates:
            # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            vernaculartiers = root.findall(querystring)
            for tier in vernaculartiers:
                tierID = tier.attrib["TIER_ID"]
                wordlist = self.tier_to_wordlist(tier)
                if wordlist == []:
                    continue
                if self.is_ID_tier(wordlist):
                    # print("skipping ID tier")
                    continue
                if self.is_major_language(wordlist, spanish=True):
                    continue
                time_in_seconds.append(self.get_seconds_from_tier(tier))
                transcriptions[candidate][tierID] = wordlist
        self.secondstranscribed = sum(time_in_seconds) #FIXME make sure that only filled annotations are counted. Add negative test
        self.transcriptions = transcriptions

    def populate_translations(self):
        """fill the attribute translation with translations from the ELAN file"""

        translationcandidates = constants.ACCEPTABLE_TRANSLATION_TIER_TYPES
        root = self.root
        if root is None:
            self.transcriptions = {}
            self.translations_with_IDs = {}
            return
        # we check the XML file which of the frequent names for translation tiers it uses
        # there might be several translation tiers with different names, hence we store them
        # in a dictionary
        translations = defaultdict(dict)
        translations_with_IDs = defaultdict(dict)
        time_in_seconds = []
        for candidate in translationcandidates:
            # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            translationtiers = root.findall(querystring)
            if translationtiers != []:  # we found a tier of the linguistic type
                for tier in translationtiers:
                    tierID = tier.attrib["TIER_ID"]
                    wordlist = self.tier_to_wordlist(tier)
                    if wordlist == []:
                        continue
                    # Sometimes, annotators put non-English contents in translation tiers
                    # For our purposes, we want to discard such content
                    if not self.is_major_language(wordlist):
                        continue
                    if not self.has_minimal_translation_length(wordlist, tierID):
                        continue
                    time_in_seconds.append(self.get_seconds_from_tier(tier))
                    translations[candidate][tierID] = wordlist
                    tmp = self.tier_to_annotation_ID_list(tier)
                    translations_with_IDs[candidate][tierID] = {
                        x[1]: wordlist[i] for i, x in enumerate(tmp)
                    }
        self.secondstranslated = sum(time_in_seconds) #FIXME make sure that only filled annotations are counted. Add negative test
        self.translations = translations
        self.translations_with_IDs = translations_with_IDs

    def get_translations(self):
        """return a list of lists of translations per tier"""

        return [
            self.translations[tier_type][tierID]
            for tier_type in self.translations
            for tierID in self.translations[tier_type]
        ]

    def get_transcriptions(self):
        """return a list of lists of transcriptions per tier"""

        return [
            self.transcriptions[tier_type][tierID]
            for tier_type in self.transcriptions
            for tierID in self.transcriptions[tier_type]
        ]

    def get_cldfs(self):
        lines = []
        # FIXME check for several tiers
        tmp_dict = copy.deepcopy(self.translations_with_IDs)
        try:
            translation_ID_dict = tmp_dict.popitem()[1].popitem()[1]
        except KeyError:
            return ""
        except AttributeError:  # FIXME should not throw attribute error at 5489
            return ""
        try:
            glosses = copy.deepcopy(self.glossed_sentences.popitem()[1].popitem()[1])
        except KeyError:
            return ""
        for g in glosses:
            if g == {}:
                return ""
            vernacular_subcells = []
            gloss_subcells = []
            ID, word_gloss_list = g.popitem()
            for tupl in word_gloss_list:
                vernacular = tupl[0]
                if vernacular is None:  # FIXME this should raise an error
                    vernacular = ""
                gloss = tupl[1]
                if gloss is None:  # FIXME this should raise an error
                    gloss = ""
                vernacular_subcells.append(vernacular)
                gloss_subcells.append(gloss)
            try:
                translation = translation_ID_dict[ID]
            except KeyError: #FIXME gigantic hack to align glosses with translations
                integer_part = ID.replace("ann","").replace("a","")
                next_integer = int(integer_part)+1
                try:
                    translation = translation_ID_dict[f"ann{next_integer}"]
                except KeyError:
                    logger.warning("translation", ID, "could not be retrieved, nor could", next_integer, "be retrieved")
                    translation = "TRANSLATION NOT RETRIEVED"
            vernacular_cell = "\t".join(vernacular_subcells)
            gloss_cell = "\t".join(gloss_subcells)
            translation_cell = translation
            line = [ID,vernacular_cell, gloss_cell, translation_cell]
            lines.append(line)
        cldfstringbuffer = io.StringIO()
        csv_writer = csv.writer(
            cldfstringbuffer, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )
        csv_writer.writerow("ID Analyzed_Word Gloss Translated_Text".split())
        for line in lines:
            csv_writer.writerow(line)
        return cldfstringbuffer.getvalue()

    def populate_glosses(self):
        """retrieve all glosses from an eaf file and map to text from parent annotation"""

        def get_word_for_gloss(annotation_value, mapping):
            """retrieve the parent annotation's text"""

            # get the XML parent, called <REF_ANNOTATION>
            ref_annotation = annotation_value.getparent()
            # find the attributed called ANNOTATION_REF, which gives the ID of the referred annotation
            annotation_ref = ref_annotation.attrib["ANNOTATION_REF"]
            wordtext = mapping.get(annotation_ref, "")
            return wordtext

        def get_annotation_text_mapping(root):
            # querystring = (
            # ".//REF_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % annotation_ref
            # )

            if root is None:
                return {}
            textdic = {
                ref_annotation.attrib.get("ANNOTATION_ID"): ref_annotation.find(
                    "./ANNOTATION_VALUE"
                ).text
                for ref_annotation in root.findall(".//REF_ANNOTATION")
            }
            return textdic

        # def get_parent_element_ID_dic(root):
        #     # querystring = (
        #     # ".//REF_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % annotation_ref
        #     # )
        #     get_parent_element_ID_dic = {
        #         ref_annotation.attrib.get("ANNOTATION_ID"): ref_annotation.getparent()
        #         for ref_annotation in root.findall(".//REF_ANNOTATION")
        #     }
        #     return get_parent_element_ID_dic

        def get_glossed_sentences(annos):  # FIXME
            ws = [mapping.get(annotation.parentID, "") for annotation in annos]
            ids = [
                self.timeslottedancestors.get(annotation.ID, None)
                for annotation in annos
            ]
            current_sentence_ID = None
            d = {}
            glossed_sentences = []
            for i, annotation in enumerate(annos):
                # print(annotation.__dict__)
                gloss = annos[i].text
                sentenceID = ids[i]
                if annotation.previous_annotation_ID is None:
                    word = ws[i]
                else:
                    try:
                        d[sentenceID][-1][1] += gloss
                    except TypeError:
                        pass
                    except KeyError:
                        logger.warning("tried to update non-existing word for gloss in", sentenceID)
                    continue
                if sentenceID != current_sentence_ID:
                    if current_sentence_ID:
                        glossed_sentences.append(d)
                    current_sentence_ID = sentenceID
                    d = {sentenceID: [[word, gloss]]}
                else:
                    try:
                        d[sentenceID].append([word, gloss])
                    except KeyError:
                        logger.warning(
                            "gloss with no parent",
                            self.path,
                            tierID,
                            annos[i].ID,
                        )
            glossed_sentences.append(d)
            return glossed_sentences

        root = self.root
        if root is None:
            return {}
        glosscandidates = constants.ACCEPTABLE_GLOSS_TIER_TYPES
        mapping = get_annotation_text_mapping(root)
        retrieved_glosstiers = {}


        for candidate in glosscandidates:
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            glosstiers = root.findall(querystring)
            if glosstiers != []:  # we found a tier of the linguistic type
                retrieved_glosstiers[candidate] = {}
                for tier in glosstiers:
                    tierID = tier.attrib["TIER_ID"]
                    parentID = self.child_parent_dic[tierID]
                    # parent_type = parent.attrib["LINGUISTIC_TYPE_REF"]
                    # if not parent_type in ACCEPTABLE_WORD_TIER_TYPES:
                    # logger.warning(
                    # "%s: Type %s is not accepted for potential parent %s of gloss candidate %s" %
                    # (self.path, parent_type, parentID, tierID)
                    # )
                    # continue
                    annotations = [
                        annotation.Annotation(el, self.timeslots, self.ref_annotations, self.alignable_annotations)
                        for el in tier.findall(".//ANNOTATION")
                    ]
                    # try:
                    # glossed_sentences = get_glossed_sentences(annotations)
                    # except KeyError:
                    # print("problematic parent relations in ", self.path, tierID)
                    # continue
                    retrieved_glosstiers[candidate][tierID] = get_glossed_sentences(
                        annotations
                    )
        self.glossed_sentences = retrieved_glosstiers
        # print(len(self.glossed_sentences), "glossed sentences")

    def create_parent_tier_dic(self):
        """
        match all tier IDs with the referenced parent IDs

        The parents are not the XML parents but are different tiers,
        which are the logical parents of a tier
        """
        d = {}
        for tier_ID in self.tier_hierarchy:
            for child in self.tier_hierarchy[tier_ID]:
                d[child["id"]] = tier_ID
        self.child_parent_dic = d

    def get_tier_hierarchy(self):
        tree = self.root
        dico = defaultdict(list)
        linguistic_types = tree.findall(".//LINGUISTIC_TYPE")
        # map tier IDs to their constraints
        tierconstraints = {
            linguistic_type.attrib["LINGUISTIC_TYPE_ID"]: linguistic_type.attrib.get(
                "CONSTRAINTS"
            )
            for linguistic_type in linguistic_types
        }
        tiers = tree.findall(".//TIER")
        for tier in tiers:
            ID = tier.attrib["TIER_ID"]
            # map all tiers to their parent tiers, defaulting to the file itself
            PARENT_REF = tier.attrib.get("PARENT_REF", (self.path))
            linguistic_type = tier.attrib["LINGUISTIC_TYPE_REF"]
            try:
                constraint = tierconstraints[linguistic_type]
            except KeyError:
                print(
                    "reference to unknown LINGUISTIC_TYPE_ID  %s when establishing constraints in %s"
                    % (linguistic_type, self.path)
                )
                continue
            dico[PARENT_REF].append(
                {"id": ID, "constraint": constraint, "ltype": linguistic_type}
            )
        self.tier_hierarchy = dico

    def translations_from_tiers(self):
        self.translations = {}

    def transcriptions_from_tiers(self):
        self.transcriptions = {}

    def glosses_from_tiers(self):
        self.glosses = {}

    def annotation_time(self):
        self.annotation_time = 0

    def readable_duration(self, seconds):
        return time.strftime("%H:%M:%S", time.gmtime(seconds))

    def get_timeslots(self):
        """
        Create a dictionary with time slot ID as keys and offset in ms as values
        """

        time_order = self.xml().find(".//TIME_ORDER")
        try:
            timeslots = {
                slot.attrib["TIME_SLOT_ID"]: slot.attrib["TIME_VALUE"]
                for slot in time_order.findall("TIME_SLOT")
            }
        except AttributeError:
            timeslots = {}
        return timeslots

    def get_alignable_annotations(self, root):
        """
        Create a dictionary with alignable annotations ID as keys and the elements themselves as values
        """

        aas = root.findall(".//ALIGNABLE_ANNOTATION")
        return {aa.attrib["ANNOTATION_ID"]: aa for aa in aas}

    def print_overview(self, writer=sys.stdout):#FIXME print tier ID
        filename = self.path.split("/")[-1]
        # outputstring = f"{filename[:4]}...{filename[-8:-4]}"
        try:
            sorted_timecodes =  sorted([int(x) for x in self.timeslots.values()])
        except AttributeError:
            sorted_timecodes = [0,0]
        first_timecode = 0
        last_timecode = 0
        try:
            first_timecode = sorted_timecodes[0]
            last_timecode = sorted_timecodes[-1]
        except IndexError:
            pass
        duration_in_seconds = (last_timecode - first_timecode)/1000
        duration_timeslots = self.readable_duration(duration_in_seconds)
        translation_tier_names = list(self.translations.keys())
        primary_translation_tier_name = ''
        translated_sentence_count = 0
        translated_word_count = 0
        translated_char_count = 0
        if len(translation_tier_names) > 1:
            logger.warning(f"{self.path} more than one translation tier found")
        if len(translation_tier_names) > 0:
            primary_translation_tier_name = translation_tier_names[0]
            translation_tier_tokens = self.translations[primary_translation_tier_name]
            for at_name in translation_tier_tokens.values():
                for sentence in at_name:
                    translated_sentence_count += 1
                    words = sentence.split()
                    translated_word_count += len(words)
                    translated_char_count += sum([len(w) for w in words])

        transcription_tier_names = list(self.transcriptions.keys())
        primary_transcription_tier_name = ''
        transcribed_sentence_count = 0
        transcribed_word_count = 0
        transcribed_char_count = 0
        if len(transcription_tier_names) > 1:
            logger.warning(f"{self.path} more than one transcription tier found")
        if len(transcription_tier_names) > 0:
            primary_transcription_tier_name = transcription_tier_names[0]
            transcription_tier_tokens = self.transcriptions[primary_transcription_tier_name]
            for at_name in transcription_tier_tokens.values():
                for sentence in at_name:
                    transcribed_sentence_count += 1
                    words = sentence.split()
                    transcribed_word_count += len(words)
                    transcribed_char_count += sum([len(w) for w in words])
        try:
            gloss_tier_names = list(self.glossed_sentences.keys())
        except AttributeError:
            gloss_tier_names = []
        primary_gloss_tier_name = ''
        glossed_sentences_count = 0
        gloss_count = 0
        zipf1 = 0
        zipf2 = 0
        distinct_glosses = defaultdict(int)
        if len(gloss_tier_names) > 1:
            logger.warning(f"{self.path} more than one gloss tier found")
        if len(gloss_tier_names) > 0:
            primary_gloss_tier_name = gloss_tier_names[0]
            gloss_tier_tokens = self.glossed_sentences[primary_gloss_tier_name]
            for at_name in gloss_tier_tokens.values():
                for gloss_list in at_name:
                    glossed_sentences_count += 1
                    try:
                        tuples = list(gloss_list.values())[0]
                    except IndexError:
                        continue
                    gloss_count += len(tuples)
                    for t in tuples:
                        gloss = t[1]
                        if gloss is None:
                            continue
                        if gloss == "***":
                            continue
                        max_ascii = max([ord(c) for c in gloss])
                        if max_ascii < 65: #we have no letters in gloss
                            continue
                        gloss_count += 1
                        distinct_glosses[gloss] += 1
        max_glosses = sorted([distinct_glosses[k] for k in distinct_glosses], key=lambda x:x,reverse=True)

        try:
            max1 = float(max_glosses[0])
            max2 = float(max_glosses[1])
        except IndexError:
            max1 = False
            max2 = False
        try:
            max3 = float(max_glosses[2])
        except IndexError:
            max3 = False
        if max3:
            zipf2 = max2/max3
        if max2:
            zipf1 = max1/max2
        if translated_sentence_count == 0:
            translated_sentence_count = -1
        if translated_word_count == 0:
            translated_word_count = -1
        if transcribed_sentence_count == 0:
            transcribed_sentence_count = -1
        if transcribed_word_count == 0:
            transcribed_word_count = -1
        if distinct_glosses == {}:
            distinct_glosses = {None:True}
        outputstring = "\t".join([filename,
                        duration_timeslots,
# #
                        primary_translation_tier_name,
                        str(translated_sentence_count),
                        str(translated_word_count),
                        str(translated_char_count),
                        str(round(translated_word_count/translated_sentence_count,2)),
                        str(round(translated_char_count/translated_word_count,2)),
                        self.readable_duration(self.secondstranslated),
# #
                        primary_transcription_tier_name,
                        str(transcribed_sentence_count),
                        str(transcribed_word_count),
                        str(transcribed_char_count),
                        str(round(transcribed_word_count/transcribed_sentence_count,2)),
                        str(round(transcribed_char_count/transcribed_word_count,2)),
                        self.readable_duration(self.secondstranscribed),#  most probably wrong # FIXME
# #
                        primary_gloss_tier_name,
                        str(glossed_sentences_count),
                        str(gloss_count),
                        str(len(distinct_glosses)),
                        str(round(gloss_count/len(distinct_glosses),2)),
                        str(round(zipf1,2)),
                        str(round(zipf2,2)),
]
)
        writer.write(f"{outputstring}\n")
        return outputstring.split("\t")


class Tier:
    def __init__(self):
        self.ID = ""  # the ID as used in the Elan file
        self.reftypename = ""  # the reftype used in the elan file
        self.constrainttype = ""  # subdivision, association, etc
        self.parenttier = None
        self.annotations = []
        self.annotation_values = []

    def get_annotated_time(self):
        pass

    def get_annotation_text(self):
        return []

    def get_glossed_categories(self):
        self.rawglosses = [
            supergloss
            for string in self.annotations
            for supergloss in re.split("[-=:. ]", string)
            if re.search("^[^a-z]+$", supergloss) and re.search("[A-Z]", supergloss)
        ]

    def get_gloss_count(self):
        personnumberdic = {
            "1SG": ["1", "SG"],
            "2SG": ["2", "SG"],
            "3SG": ["3", "SG"],
            "1DU": ["1", "DU"],
            "2DU": ["2", "DU"],
            "3DU": ["3", "DU"],
            "1PL": ["1", "PL"],
            "2PL": ["2", "PL"],
            "3PL": ["3", "PL"],
        }
        cleanglosses = Counter(self.rawglosses)

        # split fused personnumber glosses
        for k in personnumberdic:
            if k in cleanglosses:
                cleanglosses[person] += occurrences
                cleanglosses[number] += occurrences
                del cleanglosses[k]
        return cleanglosses

    def get_LGR_glosses(self):
        result = self.get_gloss_count()
        for key in result:
            if key not in constants.LGRLIST:
                del result[key]
        return result

