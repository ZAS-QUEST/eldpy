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

from eldpy import annotation
from eldpy import constants


logging.basicConfig(filename='eldpy.log', level=logging.WARNING)
logger = logging.getLogger("eldpy")


class ElanFile:
    def __init__(self, path, url, namespace=None):
        logger.info("starting init")
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
        self.transcriptions_with_IDs = {}
        self.translations = {}
        self.translations_with_IDs = {}
        self.comments = {}
        self.comments_with_IDs = {}
        self.fingerprint = None
        self.secondstranscribed = 0
        self.secondstranslated = 0
        self.root = self.xml()
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
            for el in self.root.findall(".//ALIGNABLE_ANNOTATION")
        }
        self.ref_annotations = {
            el.attrib["ANNOTATION_ID"]: el.attrib["ANNOTATION_REF"]
            for el in self.root.findall(".//REF_ANNOTATION")
        }
        self.timeslottedancestors = self.get_timeslotted_parents()
        self.timeslotted_reversedic = defaultdict(list)
        for k in self.timeslottedancestors:
            v = self.timeslottedancestors[k]
            self.timeslotted_reversedic[v].append(k)
        self.annotationdic = {
            el[0].attrib["ANNOTATION_ID"]: annotation.Annotation(
                el, self.timeslots, self.ref_annotations, self.alignable_annotations
            )
            for el in self.root.findall(".//ANNOTATION")
        }
        self.glossed_sentences = {}

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
            raise EldpyError(f"the file {self.path} is not valid XML")
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
                        self.alignable_annotations,
                    )
                    result.append(anno)
                except ValueError:
                    #there is no text
                    continue
        return result

    def is_major_language(
        self,
        list_,
        spanish=False,
        french=False,
        indonesian=False,
        portuguese=False,
        russian=False,
        logtype="False",
    ):
        try:  # detect candidate languages and retrieve most likely one
            toplanguages = detect_langs(" ".join(list_))
            toplanguage = toplanguages[0]
        except lang_detect_exception.LangDetectException:
            # we are happy that this is an unknown language
            toplanguage = None

        accepted_languages = ["en"]
        if spanish:
            accepted_languages.append("es")
        if french:
            accepted_languages.append("fr")
        # if indonesian: #indonesian causes some random errors for muyu
        #     accepted_languages.append("id")
        # if portuguese:#portuguese throws falls positives
        #     accepted_languages.append("pt")
        if russian:
            accepted_languages.append("ru")
        # print(toplanguage.lang,toplanguage.prob,accepted_languages)
        if (
            toplanguage
            and toplanguage.lang in accepted_languages
            and toplanguage.prob > self.LANGDETECTTHRESHOLD
        ):
            if logtype == "True":
                logger.info(
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
                logger.info(
                    'ignored %.2f%% probability %s for "%s ..."'
                    % (toplanguage.prob * 100, toplanguage.lang, " ".join(list_)[:100])
                )
            return False

    def tier_to_ID_wordlist(self, t):
        """
        create a list of all words in that tier by splitting
        and collating all annotation values of that tier
        """

        result = []
        for ref_ann in t.findall(".//REF_ANNOTATION") + t.findall(
            ".//ALIGNABLE_ANNOTATION"
        ):
            ID = ref_ann.attrib["ANNOTATION_ID"]
            try:
                annotation_text = ref_ann.find(".//ANNOTATION_VALUE").text.strip()
            except AttributeError:
                # there is no text
                annotation_text = ""
            result.append((ID, annotation_text))
        return result

    def tier_to_wordlist(self, t):
        tier_with_IDs = self.tier_to_ID_wordlist(t)
        result = [el[1] for el in tier_with_IDs]
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
            annotation.Annotation(
                aa, self.timeslots, self.ref_annotations, self.alignable_annotations
            ).get_duration(include_void_annotations=False)
            for aa in t.findall("./ANNOTATION")
            if aa.text is not None
        ]
        if len(timelist)>1 and sum(timelist) != 0:
            return sum(timelist) / 1000
        else:
            annotation_list = self.get_annotation_list(t)
            found_start_times = []
            cleaned_duration_list = []
            for anno in annotation_list:
                if anno.starttime not in found_start_times:
                    cleaned_duration_list.append(anno.get_duration())
                    found_start_times.append(anno.starttime)
            return sum(cleaned_duration_list) / 1000

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

    def populate(
        self,
        transcriptioncandidates=constants.ACCEPTABLE_TRANSCRIPTION_TIER_TYPES,
        translationcandidates=constants.ACCEPTABLE_TRANSLATION_TIER_TYPES,
        glosscandidates=constants.ACCEPTABLE_GLOSS_TIER_TYPES,
        commentcandidates=constants.ACCEPTABLE_COMMENT_TIER_TYPES,
        spanish=False,
        french=False,
        indonesian=False,
        portuguese=False,
        russian=False,
    ):
        self.populate_transcriptions(candidates=transcriptioncandidates)
        self.populate_translations(
            candidates=translationcandidates,
            spanish=spanish,
            french=french,
            portuguese=portuguese,
            indonesian=indonesian,
            russian=russian,
        )
        self.populate_glosses(candidates=glosscandidates)
        self.populate_comments(candidates=commentcandidates)

    def get_segment_counts(self):
        root = self.root
        querystring = ".//TIER"
        try:
            alltiers = root.findall(querystring)
        except AttributeError:
            logger.info(f"no tiers in {self.path}")
            return 0, 0
        segment_count = 0
        empty_segment_count = 0
        for tier in alltiers:
            wordlist = self.tier_to_ID_wordlist(tier)
            empty_segments = [x for x in wordlist if x[1] == ""]
            segment_count += len(wordlist)
            empty_segment_count += len(empty_segments)
        return empty_segment_count, segment_count

    def populate_transcriptions(
        self, candidates=constants.ACCEPTABLE_TRANSCRIPTION_TIER_TYPES
    ):
        """fill the attribute transcriptions with translations from the ELAN file"""

        transcriptioncandidates = candidates
        transcriptions = defaultdict(dict)
        transcriptions_with_IDs = defaultdict(dict)
        root = self.root
        if root is None:
            self.transcriptions = {}
            self.transcriptions_with_IDs = {}
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
                wordlist = self.tier_to_wordlist(tier)  # FIXME avoid duplication
                wordlist_with_IDs = self.tier_to_ID_wordlist(tier)
                if wordlist == []:
                    continue
                if self.is_ID_tier(wordlist):
                    # print("skipping ID tier")
                    continue
                if self.is_major_language(
                    wordlist,
                    spanish=True,
                    french=True,
                    indonesian=True,
                    portuguese=True,
                    russian=True,
                ):
                    continue
                newseconds = self.get_seconds_from_tier(tier)
                time_in_seconds.append(newseconds)
                transcriptions[candidate][tierID] = wordlist
                transcriptions_with_IDs[candidate][tierID] = wordlist_with_IDs
        self.secondstranscribed += sum(time_in_seconds)
        if len(transcriptions) > 0:
            self.transcriptions = transcriptions
            self.transcriptions_with_IDs = transcriptions_with_IDs

    def populate_translations(
        self,
        candidates=constants.ACCEPTABLE_TRANSLATION_TIER_TYPES,
        spanish=False,
        french=True,
        indonesian=False,
        portuguese=False,
        russian=False,
    ):
        """fill the attribute translation with translations from the ELAN file"""

        translationcandidates = candidates
        root = self.root
        if root is None:
            self.translations = {}
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
                    if not self.is_major_language(
                        wordlist,
                        spanish=spanish,
                        french=french,
                        portuguese=portuguese,
                        indonesian=indonesian,
                        russian=russian,
                    ):
                        continue
                    if not self.has_minimal_translation_length(wordlist, tierID):
                        continue
                    newseconds = self.get_seconds_from_tier(tier)
                    time_in_seconds.append(newseconds)
                    translations[candidate][tierID] = wordlist
                    tmp = self.tier_to_annotation_ID_list(tier)
                    translations_with_IDs[candidate][tierID] = {
                        x[1]: wordlist[i] for i, x in enumerate(tmp)
                    }
        self.secondstranslated += sum(time_in_seconds)
        # FIXME make sure that only filled annotations are counted. Add negative test
        if len(translations) > 0:
            self.translations = translations
            self.translations_with_IDs = translations_with_IDs

    def populate_comments(self, candidates=constants.ACCEPTABLE_COMMENT_TIER_TYPES):
        """fill the attribute comment with comments from the ELAN file"""

        commentcandidates = constants.ACCEPTABLE_COMMENT_TIER_TYPES
        root = self.root
        if root is None:
            self.comments = {}
            self.comments_with_IDs = {}
            return
        # we check the XML file which of the frequent names for comment tiers it uses
        # there might be several comment tiers with different names, hence we store them
        # in a dictionary
        comments = defaultdict(dict)
        comments_with_IDs = defaultdict(dict)
        for candidate in commentcandidates:
            # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            commenttiers = root.findall(querystring)
            if commenttiers != []:  # we found a tier of the linguistic type
                for tier in commenttiers:
                    tierID = tier.attrib["TIER_ID"]
                    wordlist = self.tier_to_wordlist(tier)
                    if wordlist == []:
                        continue
                    comments[candidate][tierID] = wordlist
                    tmp = self.tier_to_annotation_ID_list(tier)
                    comments_with_IDs[candidate][tierID] = {
                        x[1]: wordlist[i] for i, x in enumerate(tmp)
                    }
        if len(comments) > 0:
            self.comments = comments
            self.comments_with_IDs = comments_with_IDs

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

    def get_cldfs(self, provided_gloss_tier_name=False, matrix=False):
        lines = []
        tmp_transcription_dic = copy.deepcopy(self.transcriptions_with_IDs)
        d = {}
        for candidate in tmp_transcription_dic:
            for tier in tmp_transcription_dic[candidate]:
                for tupl in tmp_transcription_dic[candidate][tier]:
                    d[tupl[0]] = tupl[1]
        transcription_ID_dict = d

        tmp_translations_dict = copy.deepcopy(self.translations_with_IDs)
        try:
            translation_tier_to_retain = {}
            translation_tiername_to_retain = ""
            # print(f"found {len(tmp_translations_dict)} possible gloss types: {list(tmp_translations_dict.keys())}")
            max_charcount = 0
            for type_candidate in tmp_translations_dict:
                # print(f" found {len(tmp_translations_dict[type_candidate])} possible tiers in {type_candidate}: {list(tmp_translations_dict[type_candidate])}")
                for tier in tmp_translations_dict[type_candidate]:
                    # print(tier)
                    # pprint.pprint(tmp_translations_dict[type_candidate][tier].keys())
                    charcount = 0
                    for top_element in tmp_translations_dict[type_candidate][tier]:
                        charcount += len(
                            tmp_translations_dict[type_candidate][tier][top_element]
                        )
                    # print(f"  tier {tier} has {charcount} characters. Current maximum is {max_charcount}")
                    if charcount >= max_charcount:
                        max_charcount = charcount
                        translation_tiername_to_retain = tier
                        translation_tier_to_retain = tmp_translations_dict[type_candidate][tier]
            # print(f"  retaining {translation_tiername_to_retain} as the tier with most characters ({max_charcount})")
            translation_ID_dict = translation_tier_to_retain
        except (ValueError, AttributeError, KeyError):
            raise EldpyError(f"No translations found in {self.filename}")
        tmp_comments_dict = copy.deepcopy(self.comments_with_IDs)
        try:
            comments_ID_dict = tmp_comments_dict.popitem()[1].popitem()[1]
        except KeyError:
            logger.info(f"no comments in {self.path}")
            comments_ID_dict = {}
        try:
            glosses_d = copy.deepcopy(self.glossed_sentences)
        except AttributeError:
            raise EldpyError(
                f"No glosses found in {self.filename}. Try providing the tier type of the gloss tier explicitly"
            )
        best_tier_ratio = 0
        glosstiername_to_retain = ''
        glosstier_to_retain = {}
        # print(f"found {len(glosses_d)} possible gloss types")
        for type_candidate in glosses_d:
            # print(f" found {len(glosses_d[type_candidate])} possible tiers in {type_candidate}")
            for tier in glosses_d[type_candidate]:
                tier_glosses = []
                for annotation in glosses_d[type_candidate][tier]:
                    for element in annotation:
                        glosses = [x[1] for x in annotation[element]]
                        tier_glosses += glosses
                distinct_glosses = list(set(tier_glosses))
                try:
                    ratio = len(distinct_glosses) / len(tier_glosses)
                except ZeroDivisionError:
                    ratio = 0
                # print(f"  tier {tier} has {ratio:.4f} gloss diversity")
                if provided_gloss_tier_name and tier == provided_gloss_tier_name:
                    best_tier_ratio = 100
                    glosstiername_to_retain = tier
                    glosstier_to_retain = glosses_d[type_candidate][tier]
                    break
                if ratio > best_tier_ratio:
                    best_tier_ratio = ratio
                    glosstiername_to_retain = tier
                    glosstier_to_retain = glosses_d[type_candidate][tier]
        # print(f"  retaining {glosstiername_to_retain} as the tier with most gloss diversity ({best_tier_ratio})")
        glosses = glosstier_to_retain
        if glosses is None:
            raise EldpyError(f"Glosses could not be retrieved from {self.filename} > {glosstiername_to_retain}")
        for g in glosses:
            if g == {}:
                return ""
            vernacular_subcells = []
            gloss_subcells = []
            ID, word_gloss_list = g.popitem()
            for tupl in word_gloss_list:
                vernacular = tupl[0]
                gloss = tupl[1]
                if vernacular is None and gloss is None:
                    #no need to act
                    continue
                if vernacular is None:
                    # raise EldpyError(f"empty transcription with gloss {tupl[0]}:{tupl[1]} in ")
                    logger.warning(f"empty transcription with gloss {repr(tupl[0])}:{repr(tupl[1])} in {self.path}. Setting vernacular to ''")
                    vernacular = ""
                if gloss is None:
                    logger.warning(f"empty transcription with gloss {repr(tupl[0])}:{repr(tupl[1])} in {self.path}. Setting gloss to ''")
                    gloss = ""
                vernacular_subcells.append(vernacular)
                gloss_subcells.append(gloss)
            try:
                primary_text = transcription_ID_dict[ID]
            except KeyError:
                # FIXME gigantic hack to align glosses with transcriptions
                integer_part = ID.replace("ann", "").replace("a", "")
                try:
                    next_integer = int(integer_part) + 1
                except ValueError:
                    logger.warning(f"translation {ID} could not be retrieved in {self.path}, word-gloss pair {vernacular}:{gloss}")
                    primary_text = "PRIMARY TEXT NOT RETRIEVED"
                else:
                    try:
                        primary_text = transcription_ID_dict[f"ann{next_integer}"]
                    except KeyError:
                        # we try to retrieve a tier dependent on the ref tier which does have a primary text
                        for v in self.timeslotted_reversedic[ID]:
                            primary_text = transcription_ID_dict.get(v)
                            if primary_text:
                                break
                        else:
                            logger.warning(f"primary text {ID} could not be retrieved, nor could {next_integer} be retrieved")
                            primary_text = "PRIMARY TEXT NOT RETRIEVED"

            try:
                translation = translation_ID_dict[ID]
            except KeyError:
                # FIXME gigantic hack to align glosses with translations
                integer_part = ID.replace("ann", "").replace("a", "")
                try:
                    next_integer = int(integer_part) + 1
                except ValueError:
                    logger.warning("translation", ID, "could not be retrieved")
                    translation = "TRANSLATION NOT RETRIEVED"
                else:
                    try:
                        new_key = f"ann{next_integer}"
                        translation = translation_ID_dict[new_key]
                    except KeyError:
                        logger.warning(f"translation{ID} could not be retrieved, nor could {next_integer} be retrieved")
                        translation = "TRANSLATION NOT RETRIEVED"
            primary_text_cell = primary_text or ""
            vernacular_cell = "\t".join(vernacular_subcells) or ""
            gloss_cell = "\t".join(gloss_subcells) or ""
            translation_cell = translation or ""
            comment = comments_ID_dict.get(
                ID, ""
            )  # FIXME check whether any comments are discarded which should be saved
            # ignore completely empty annotations
            if (
                primary_text_cell + vernacular_cell + gloss_cell + translation_cell
            ).strip() == "":
                continue
            lgr_cell = "WORD_ALIGNED"
            # FIXME check for morpheme alignment
            line = [
                ID,
                primary_text_cell,
                vernacular_cell,
                gloss_cell,
                translation_cell,
                comment,
                lgr_cell,
            ]
            lines.append(line)
        if matrix:
            return lines
        else:
            cldfstringbuffer = io.StringIO()
            csv_writer = csv.writer(
                cldfstringbuffer, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
            )
            csv_writer.writerow(
                "ID Primary_Text Analyzed_Word Gloss Translated_Text Comment LGRConformance".split()
            )
            for line in lines:
                csv_writer.writerow(line)
            return cldfstringbuffer.getvalue()

    def populate_glosses(self, candidates=constants.ACCEPTABLE_GLOSS_TIER_TYPES):
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
            new_glossed_sentences = []
            for i, annotation in enumerate(annos):
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
                        logger.warning(f"tried to update non-existing word for gloss in {self.path} > {sentenceID}")
                    continue
                if sentenceID != current_sentence_ID:
                    if current_sentence_ID:
                        new_glossed_sentences.append(d)
                    current_sentence_ID = sentenceID
                    d = {sentenceID: [[word, gloss]]}
                else:
                    try:
                        d[sentenceID].append([word, gloss])
                    except KeyError:
                        logger.warning(f"gloss with no parent {self.path} > {tierID} > {annos[i].ID}")
            new_glossed_sentences.append(d)
            return new_glossed_sentences

        root = self.root
        if root is None:
            self.glossed_sentences = {}
            logger.warning(f"No glossed sentences in {self.path}")
            return
        mapping = get_annotation_text_mapping(root)
        retrieved_glosstiers = {}
        for candidate in candidates:
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            glosstiers = root.findall(querystring)
            if glosstiers != []:
                # we found a tier of the linguistic type
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
                        annotation.Annotation(
                            el,
                            self.timeslots,
                            self.ref_annotations,
                            self.alignable_annotations,
                        )
                        for el in tier.findall(".//ANNOTATION")
                    ]
                    # try:
                    # new_glossed_sentences = get_glossed_sentences(annotations)
                    # except KeyError:
                    # print("problematic parent relations in ", self.path, tierID)
                    # continue
                    retrieved_glosstiers[candidate][tierID] = get_glossed_sentences(
                        annotations
                    )
        if len(retrieved_glosstiers)>0:
            self.glossed_sentences = retrieved_glosstiers
        else:
            self.glossed_sentences = {}

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
                raise EldpyError("reference to unknown LINGUISTIC_TYPE_ID  {linguistic_type} when establishing constraints in {self.path}")
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
            logger.info("No timeslots for {self.path}")
            timeslots = {}
        return timeslots

    def get_alignable_annotations(self, root):
        """
        Create a dictionary with alignable annotations ID as keys and the elements themselves as values
        """

        aas = root.findall(".//ALIGNABLE_ANNOTATION")
        return {aa.attrib["ANNOTATION_ID"]: aa for aa in aas}

    def print_overview(self, writer=sys.stdout):  # FIXME print tier ID
        filename = self.path.split("/")[-1]
        # outputstring = f"{filename[:4]}...{filename[-8:-4]}"
        try:
            sorted_timecodes = sorted([int(x) for x in self.timeslots.values()])
        except AttributeError:
            sorted_timecodes = [0, 0]
        first_timecode = 0
        last_timecode = 0
        try:
            first_timecode = sorted_timecodes[0]
            last_timecode = sorted_timecodes[-1]
        except IndexError:
            pass
        duration_in_seconds = (last_timecode - first_timecode) / 1000
        if duration_in_seconds == 0:
            logger.WARNING(f"{self.path} has a duration of 0 seconds")
        duration_timeslots = self.readable_duration(duration_in_seconds)
        translation_tier_names = list(self.translations.keys())
        translation_tier_names_string = ",".join(translation_tier_names)
        translated_sentence_count = 0
        translated_word_count = 0
        translated_char_count = 0
        if len(translation_tier_names) > 1:
            logger.warning(f"{self.path} more than one translation tier found")
        if len(translation_tier_names) > 0:
            for translation_tier in self.translations:
                for at_name in self.translations[translation_tier].values():
                    for sentence in at_name:
                        translated_sentence_count += 1
                        words = sentence.split()
                        translated_word_count += len(words)
                        translated_char_count += sum([len(w) for w in words])
        try:
            translated_sec_percentage = (
                self.secondstranslated * 100 / duration_in_seconds
            )
        except ZeroDivisionError:
            translated_sec_percentage = -1
        transcription_tier_names = list(self.transcriptions.keys())
        # primary_transcription_tier_name = ""
        transcribed_sentence_count = 0
        transcribed_word_count = 0
        transcribed_char_count = 0
        if len(transcription_tier_names) > 1:
            logger.warning(f"{self.path} more than one transcription tier found")
        transcription_tier_names_string = ",".join(transcription_tier_names)
        if len(transcription_tier_names) > 0:
            for transcription_tier in self.transcriptions:
                for at_name in self.transcriptions[transcription_tier].values():
                    for sentence in at_name:
                        transcribed_sentence_count += 1
                        words = sentence.split()
                        transcribed_word_count += len(words)
                        transcribed_char_count += sum([len(w) for w in words])
        try:
            transcribed_sec_percentage = (
                self.secondstranscribed * 100 / duration_in_seconds
            )
        except ZeroDivisionError:
            transcribed_sec_percentage = -1
        try:
            gloss_tier_names = list(self.glossed_sentences.keys())
        except AttributeError:
            gloss_tier_names = []
        primary_gloss_tier_name = ""
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
                        if max_ascii < 65:  # we have no letters in gloss
                            continue
                        gloss_count += 1
                        distinct_glosses[gloss] += 1
        max_glosses = sorted(
            [distinct_glosses[k] for k in distinct_glosses],
            key=lambda x: x,
            reverse=True,
        )

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
            zipf2 = max2 / max3
        if max2:
            zipf1 = max1 / max2
        if translated_sentence_count == 0:
            translated_sentence_count = -1
        if translated_word_count == 0:
            translated_word_count = -1
        if transcribed_sentence_count == 0:
            transcribed_sentence_count = -1
        if transcribed_word_count == 0:
            transcribed_word_count = -1
        if distinct_glosses == {}:
            distinct_glosses = {None: True}
        empty_segment_count, segment_count = self.get_segment_counts()
        try:
            empty_segment_ratio = empty_segment_count / segment_count
        except ZeroDivisionError:
            empty_segment_ratio = -1
        outputstring = "\t".join(
            [
                filename,
                duration_timeslots,
                # #
                translation_tier_names_string,
                str(translated_sentence_count),
                str(translated_word_count),
                str(translated_char_count),
                str(round(translated_word_count / translated_sentence_count, 2)),
                str(round(translated_char_count / translated_word_count, 2)),
                self.readable_duration(self.secondstranslated),
                str(round(translated_sec_percentage, 2)),
                # #
                transcription_tier_names_string,
                str(transcribed_sentence_count),
                str(transcribed_word_count),
                str(transcribed_char_count),
                str(round(transcribed_word_count / transcribed_sentence_count, 2)),
                str(round(transcribed_char_count / transcribed_word_count, 2)),
                self.readable_duration(self.secondstranscribed),
                str(round(transcribed_sec_percentage, 2)),
                # #
                primary_gloss_tier_name,
                str(glossed_sentences_count),
                str(gloss_count),
                str(len(distinct_glosses)),
                str(round(gloss_count / len(distinct_glosses), 2)),
                str(round(zipf1, 2)),
                str(round(zipf2, 2)),
                str(empty_segment_count),
                str(segment_count),
                str(round(empty_segment_ratio * 100, 2)),
            ]
        )
        # writer.write(f"{outputstring}\n")
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


class EldpyError(Exception):
    def __init__(self, message):
        self.message = message
        logger.error(self.message)

    pass
