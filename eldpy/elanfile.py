"""
A representation of an ELAN file
"""

import copy

# import json
import logging

# import pprint
# import re

# import requests
import csv
import io
from collections import defaultdict
from lxml import etree

from eldpy import annotation
from eldpy import constants
from eldpy.eldpyerror import EldpyError
from eldpy.helpers import (
    is_major_language,
    is_id_tier,
    tier_to_annotation_id_list,
    tier_to_wordlist,
    tier_to_id_wordlist,
    get_alignable_annotations,
    readable_duration,
    get_zipfs,
    get_words_from_transcription_tiers,
    get_words_from_translation_tiers,
    get_gloss_metadata,
    get_annotation_text_mapping,
    get_glosstier_to_retain,
    get_line,
    get_transcription_id_dict,
    get_comments_id_dict,
    get_translation_id_dict,
    get_glossed_sentences
)


logging.basicConfig(filename="eldpy.log", level=logging.WARNING)
logger = logging.getLogger("eldpy")
logger.disabled = True

class ElanFile:
    """A representation of an ELAN file"""

    def __init__(self, path, url, namespace=None):
        self.path = path
        logger.info(f"starting init {self.path}")
        self.id_ = self.path.split("/")[-1]
        self.url = url
        self.namespace = namespace
        self.tiers = []
        self.vernaculartiers = []
        self.translationtiers = []
        self.glosstiers = []
        self.timecodes = {}
        self.reftypes = {}
        self.transcriptions = {}
        self.transcriptions_with_ids = {}
        self.translations = {}
        self.translations_with_ids = {}
        self.comments = {}
        self.comments_with_ids = {}
        self.fingerprint = None
        self.secondstranscribed = 0
        self.secondstranslated = 0
        self.root = self.xml()
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
        logger.info({self.path})

    def __eq__(
        self, other
    ):  # this is needed for some rdflib function which throws unclear errors
        return self.path == other.path

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.path < other.path

    def __gt__(self, other):
        return self.path > other.path

    def __le__(self, other):
        return self.path <= other.path

    def __ge__(self, other):
        return self.path >= other.path

    def get_timeslotted_parents(self):
        """
        return the ulimate ancestor of this annotation which has timing information
        """

        def get_timeslotted_parent(child_id, d):
            parent_id = self.ref_annotations[child_id]
            if parent_id in self.alignable_annotations:
                # parent is an alignable_annotation with timecodes
                return parent_id
            if parent_id in d:
                # we had already established who the ultimate ancestor of the parent is
                d[child_id] = d[
                    parent_id
                ]  # the ultimate ancestor or ego is the same as the ua of ego's father
                return d[parent_id]
            # this parent element is unknown
            return get_timeslotted_parent(parent_id, d)

        d = copy.copy(self.alignable_annotations)
        a = {ra: get_timeslotted_parent(ra, d) for ra in self.ref_annotations}
        return a

    def xml(self):
        """return the XML representation"""

        try:
            root = etree.parse(self.path)
        except etree.XMLSyntaxError as exc:
            raise EldpyError(f"the file {self.path} is not valid XML", logger=logger) from exc
        return root

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
        # tree = self.xml()
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

        typedic = {
            "Symbolic_Subdivision": "s",
            "Symbolic Subdivision": "s",
            "Symbolic_Association": "a",
            "Symbolic Association": "a",
            "Time_Subdivision": "t",
            "Time Subdivision": "t",
            "Included_In": "i",
            "root": "R",
        }
        constraint = d["constraint"]
        code = typedic.get(constraint, "x")
        if lump and code in ("ti"):
            # fold both "t" and "i" into "s"
            code = "s"
        self.fingerprint += code
        children = self.tier_hierarchy[d["id"]]
        if children == []:
            return
        self.fingerprint += "["
        for child in children:
            self.analyze_tier(child, level + 1, lump=lump)
        self.fingerprint += "]"

    def get_annotation_list(self, t):
        """return a list of the annotations for a given tier"""

        aas = get_alignable_annotations(self.root)
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
                    # there is no text
                    continue
        return result

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
        if len(timelist) > 1 and sum(timelist) != 0:
            return sum(timelist) / 1000
        annotation_list = self.get_annotation_list(t)
        found_start_times = []
        cleaned_duration_list = []
        for anno in annotation_list:
            if anno.starttime not in found_start_times:
                cleaned_duration_list.append(anno.get_duration())
                found_start_times.append(anno.starttime)
        return sum(cleaned_duration_list) / 1000

    def has_minimal_translation_length(self, t, tier_id):
        """
        how many words should the average annotation have for this
        tier to be counted as translation?
        Very short stretches are typically not translations but something else
        """

        translation_minimum = 1.5
        avg_annotation_length = sum(len(x.strip().split()) for x in t) / len(t)
        if avg_annotation_length < translation_minimum:
            logger.warning(
                f"{tier_id} has too short annotations {avg_annotation_length} for the tier to be a translation ({', '.join(t[:3])} ,...)"
            )
            return False
        return True

    def populate(
        self,
        transcriptioncandidates=constants.ACCEPTABLE_TRANSCRIPTION_TIER_TYPES,
        translationcandidates=constants.ACCEPTABLE_TRANSLATION_TIER_TYPES,
        glosscandidates=constants.ACCEPTABLE_GLOSS_TIER_TYPES,
        commentcandidates=constants.ACCEPTABLE_COMMENT_TIER_TYPES,
        major_languages=("en",)
    ):
        """
        fill all tiers which can be populated
        """

        # pylint: disable=too-many-arguments
        self.populate_transcriptions(
            candidates=transcriptioncandidates, major_languages=major_languages
        )
        self.populate_translations(
            candidates=translationcandidates,
            major_languages=major_languages
        )
        self.populate_glosses(candidates=glosscandidates)
        self.populate_comments(candidates=commentcandidates)

    def get_segment_counts(self):
        """count the number of annotations which have no content"""

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
            wordlist = tier_to_id_wordlist(tier)
            empty_segments = [x for x in wordlist if x[1] == ""]
            segment_count += len(wordlist)
            empty_segment_count += len(empty_segments)
        return empty_segment_count, segment_count

    def populate_transcriptions(
        self,
        candidates=constants.ACCEPTABLE_TRANSCRIPTION_TIER_TYPES,
        major_languages=("en",),
    ):
        """fill the attribute transcriptions with translations from the ELAN file"""


        transcriptions = defaultdict(dict)
        transcriptions_with_ids = defaultdict(dict)
        root = self.root
        if root is None:
            self.transcriptions = {}
            self.transcriptions_with_ids = {}
            return
        # we check the XML file which of the frequent names for transcription tiers it uses
        # there might be several transcription tiers with different names, hence we store them
        # in a dictionary
        time_in_seconds = []
        for candidate in candidates:
            # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
            querystring = f"TIER[@LINGUISTIC_TYPE_REF='{candidate}']"
            vernaculartiers = root.findall(querystring)
            for tier in vernaculartiers:
                tier_id = tier.attrib["TIER_ID"]
                wordlist_with_ids = tier_to_id_wordlist(tier)
                wordlist = [el[1] for el in wordlist_with_ids]
                if wordlist == []:
                    continue
                if is_id_tier(wordlist):
                    logger.info("skipping ID tier")
                    continue
                if is_major_language(
                    wordlist, accepted_languages=major_languages, logger=logger
                ):
                    continue
                newseconds = self.get_seconds_from_tier(tier)
                time_in_seconds.append(newseconds)
                transcriptions[candidate][tier_id] = wordlist
                transcriptions_with_ids[candidate][tier_id] = wordlist_with_ids
        self.secondstranscribed += sum(time_in_seconds)
        if len(transcriptions) > 0:
            self.transcriptions = transcriptions
            self.transcriptions_with_ids = transcriptions_with_ids

    def populate_translations(
        self,
        candidates=constants.ACCEPTABLE_TRANSLATION_TIER_TYPES,
        major_languages=("en",)
    ):

        """fill the attribute translation with translations from the ELAN file"""

        root = self.root
        if root is None:
            self.translations = {}
            self.translations_with_ids = {}
            return
        # we check the XML file which of the frequent names for translation tiers it uses
        # there might be several translation tiers with different names, hence we store them
        # in a dictionary
        translations = defaultdict(dict)
        translations_with_ids = defaultdict(dict)
        time_in_seconds = []
        for candidate in candidates:
            # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
            querystring = f"TIER[@LINGUISTIC_TYPE_REF='{candidate}']"
            translationtiers = root.findall(querystring)
            if translationtiers != []:  # we found a tier of the linguistic type
                for tier in translationtiers:
                    tier_id = tier.attrib["TIER_ID"]
                    wordlist = tier_to_wordlist(tier)
                    if wordlist == []:
                        continue
                    # Sometimes, annotators put non-English contents in translation tiers
                    # For our purposes, we want to discard such content
                    if not is_major_language(
                        wordlist,
                        accepted_languages=major_languages,
                        # spanish=spanish,
                        # french=french,
                        # portuguese=portuguese,
                        # indonesian=indonesian,
                        # russian=russian,
                        logger=logger,
                    ):
                        continue
                    if not self.has_minimal_translation_length(wordlist, tier_id):
                        continue
                    newseconds = self.get_seconds_from_tier(tier)
                    time_in_seconds.append(newseconds)
                    translations[candidate][tier_id] = wordlist
                    tmp = tier_to_annotation_id_list(tier)
                    translations_with_ids[candidate][tier_id] = {
                        x[1]: wordlist[i] for i, x in enumerate(tmp)
                    }
        self.secondstranslated += sum(time_in_seconds)
        if len(translations) > 0:
            self.translations = translations
            self.translations_with_ids = translations_with_ids

    def populate_comments(
        self, candidates=constants.ACCEPTABLE_COMMENT_TIER_TYPES,
        comment_tier_id_to_retain = None
    ):
        """
        fill the attribute comment with comments from the ELAN file
        """

        commentcandidates = candidates
        root = self.root
        if root is None:
            self.comments = {}
            self.comments_with_ids = {}
            return
        # we check the XML file which of the frequent names for comment tiers it uses
        # there might be several comment tiers with different names, hence we store them
        # in a dictionary
        comments = defaultdict(dict)
        comments_with_ids = defaultdict(dict)
        for candidate in commentcandidates:
            # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
            querystring = f"TIER[@LINGUISTIC_TYPE_REF='{candidate}']"
            commenttiers = root.findall(querystring)
            if commenttiers != []:  # we found a tier of the linguistic type
                for tier in commenttiers:
                    tier_id = tier.attrib["TIER_ID"]
                    if comment_tier_id_to_retain and comment_tier_id_to_retain != tier_id:
                        continue
                    wordlist = tier_to_wordlist(tier)
                    if wordlist == []:
                        continue
                    comments[candidate][tier_id] = wordlist
                    tmp = tier_to_annotation_id_list(tier)
                    comments_with_ids[candidate][tier_id] = {
                        x[1]: wordlist[i] for i, x in enumerate(tmp)
                    }
        if len(comments) > 0:
            self.comments = comments
            self.comments_with_ids = comments_with_ids

    def get_translations(self):
        """return a list of lists of translations per tier"""

        return [
            self.translations[tier_type][tier_id]
            for tier_type in self.translations
            for tier_id in self.translations[tier_type]
        ]

    def get_transcriptions(self):
        """return a list of lists of transcriptions per tier"""

        return [
            self.transcriptions[tier_type][tier_id]
            for tier_type in self.transcriptions
            for tier_id in self.transcriptions[tier_type]
        ]

    def get_cldfs(self, provided_gloss_tier_name=False, matrix=False):
        """
        return a representation of the ELAN file in the
        Cross-Linguistic Data Format     """

        tmp_transcription_dic = copy.deepcopy(self.transcriptions_with_ids)
        transcription_id_dict = get_transcription_id_dict(tmp_transcription_dic)
        translation_id_dict =get_translation_id_dict(copy.deepcopy(self.translations_with_ids))
        comments_id_dict = get_comments_id_dict(copy.deepcopy(self.comments_with_ids))
        try:
            glosses, glosstiername_to_retain = get_glosstier_to_retain(copy.deepcopy(self.glossed_sentences),provided_gloss_tier_name)
        except AttributeError as exc:
            raise EldpyError(
                f"No glosses found in {self.path}. Try providing the tier type of the gloss tier explicitly",
                logger,
            ) from exc

        if glosses is None:
            raise EldpyError(
                f"Glosses could not be retrieved from {self.path} > {glosstiername_to_retain}",
                logger,
            )
        lines = []
        for g in glosses:
            line = get_line(g, transcription_id_dict, self.timeslotted_reversedic,translation_id_dict,comments_id_dict,logger=logger)
             # ignore completely empty annotations
            if "".join(line[1:4]).strip() == "":
                # print(line)
                continue
            lines.append(line)
        if matrix:
            return lines
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

    def populate_glosses(
        self, candidates=constants.ACCEPTABLE_GLOSS_TIER_TYPES
    ):
        """retrieve all glosses from an eaf file and map to text from parent annotation"""


        root = self.root
        if root is None:
            self.glossed_sentences = {}
            logger.warning(f"No glossed sentences in {self.path}")
            return
        mapping = get_annotation_text_mapping(root)
        retrieved_glosstiers = {}
        for candidate in candidates:
            querystring = f"TIER[@LINGUISTIC_TYPE_REF='{candidate}']"
            glosstiers = root.findall(querystring)
            if glosstiers != []:
                # we found a tier of the linguistic type
                retrieved_glosstiers[candidate] = {}
                for tier in glosstiers:
                    tier_id = tier.attrib["TIER_ID"]
                    annotations = [
                        annotation.Annotation(
                            el,
                            self.timeslots,
                            self.ref_annotations,
                            self.alignable_annotations,
                        )
                        for el in tier.findall(".//ANNOTATION")
                    ]
                    retrieved_glosstiers[candidate][tier_id] = get_glossed_sentences(
                        annotations,
                        self.timeslottedancestors,
                        mapping,
                        logger=logger
                    )
        if len(retrieved_glosstiers) > 0:
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
        for tier_id in self.tier_hierarchy:
            for child in self.tier_hierarchy[tier_id]:
                d[child["id"]] = tier_id
        self.child_parent_dic = d

    def get_tier_hierarchy(self):
        """
        map tiers to their parents
        """

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
            id_ = tier.attrib["TIER_ID"]
            # map all tiers to their parent tiers, defaulting to the file itself
            parent_ref = tier.attrib.get("PARENT_REF", (self.path))
            linguistic_type = tier.attrib["LINGUISTIC_TYPE_REF"]
            try:
                constraint = tierconstraints[linguistic_type]
            except KeyError as exc:
                raise EldpyError(
                    "reference to unknown LINGUISTIC_TYPE_ID  {linguistic_type} when establishing constraints in {self.path}",
                    logger=logger,
                ) from exc
            dico[parent_ref].append(
                {"id": id_, "constraint": constraint, "ltype": linguistic_type}
            )
        self.tier_hierarchy = dico

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

    def print_overview(
        self,
        # writer=sys.stdout
    ):  # FIXME print tier ID
        """
        generate a report string with information about an eaf file
        """
        # pylint: disable=use-implicit-booleaness-not-comparison, , too-many-locals, too-many-statements

        filename = self.path.split("/")[-1]
        # outputstring = f"{filename[:4]}...{filename[-8:-4]}"
        first_timecode = 0
        last_timecode = 0
        translated_sentence_count = 0
        translated_word_count = 0
        translated_char_count = 0
        transcribed_sentence_count = 0
        transcribed_word_count = 0
        transcribed_char_count = 0
        glossed_sentences_count = 0
        gloss_count = 0
        zipf1 = 0
        zipf2 = 0

        try:
            sorted_timecodes = sorted([int(x) for x in self.timeslots.values()])
        except AttributeError:
            sorted_timecodes = [0, 0]
        try:
            first_timecode = sorted_timecodes[0]
            last_timecode = sorted_timecodes[-1]
        except IndexError:
            pass
        duration_in_seconds = (last_timecode - first_timecode) / 1000
        if duration_in_seconds == 0:
            logger.warning(f"{self.path} has a duration of 0 seconds")
        duration_timeslots = readable_duration(duration_in_seconds)
        translation_tier_names = list(self.translations.keys())
        translation_tier_names_string = ",".join(translation_tier_names)
        words, sentence_count = get_words_from_translation_tiers(translation_tier_names, self.translations, logger=logger)
        translated_word_count += len(words)
        translated_char_count += sum(len(w) for w in words)
        translated_sentence_count += sentence_count
        try:
            translated_sec_percentage = (
                self.secondstranslated * 100 / duration_in_seconds
            )
        except ZeroDivisionError:
            translated_sec_percentage = -1
        transcription_tier_names = list(self.transcriptions.keys())
        transcription_tier_names_string = ",".join(transcription_tier_names)
        words, sentence_count = get_words_from_transcription_tiers(transcription_tier_names, self.transcriptions, logger=logger)
        transcribed_word_count += len(words)
        transcribed_char_count += sum(len(w) for w in words)
        transcribed_sentence_count += sentence_count
        try:
            transcribed_sec_percentage = (
                self.secondstranscribed * 100 / duration_in_seconds
            )
        except ZeroDivisionError:
            transcribed_sec_percentage = -1
        try:
            gloss_tier_names = list(self.glossed_sentences.keys())
            primary_gloss_tier_name = gloss_tier_names[0]
            distinct_glosses, glossed_sentences_count  =  get_gloss_metadata(self.glossed_sentences[primary_gloss_tier_name],
                                                                        logger=logger)
            distinct_gloss_count = len(distinct_glosses.keys()) or -1
            gloss_count = sum (distinct_glosses.values())
            zipf1, zipf2 = get_zipfs(distinct_glosses)
        except (AttributeError, IndexError):
            distinct_glosses = {}
            gloss_count = 0
            distinct_gloss_count = -1
            zipf1 = 0
            zipf2 = 0
            primary_gloss_tier_name = ''
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
                readable_duration(self.secondstranslated),
                str(round(translated_sec_percentage, 2)),
                # #
                transcription_tier_names_string,
                str(transcribed_sentence_count),
                str(transcribed_word_count),
                str(transcribed_char_count),
                str(round(transcribed_word_count / transcribed_sentence_count, 2)),
                str(round(transcribed_char_count / transcribed_word_count, 2)),
                readable_duration(self.secondstranscribed),
                str(round(transcribed_sec_percentage, 2)),
                # #
                primary_gloss_tier_name,
                str(glossed_sentences_count),
                str(gloss_count),
                str(distinct_gloss_count),
                str(round(gloss_count / distinct_gloss_count, 2)),
                str(round(zipf1, 2)),
                str(round(zipf2, 2)),
                str(empty_segment_count),
                str(segment_count),
                str(round(empty_segment_ratio * 100, 2)),
            ]
        )
        # writer.write(f"{outputstring}\n")
        return outputstring.split("\t")
