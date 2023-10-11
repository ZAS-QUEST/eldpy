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
                    annotation = Annotation(
                        aas.get(ref_annotation.attrib["ANNOTATION_REF"]),
                        self.timeslots,
                    )
                    result.append(annotation)
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

        return [
            av.text.strip()
            for av in t.findall(".//ANNOTATION_VALUE")
            if av.text is not None
        ]

    def get_seconds_from_tier(self, t):
        """
        get a list of duration from the time slots directly mentioned in annotations
        """

        timelist = [
            Annotation(aa, self.timeslots).get_duration()
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

        transcriptioncandidates = ACCEPTABLE_TRANSCRIPTION_TIER_TYPES
        transcriptions = defaultdict(dict)
        root = self.root
        if root is None:
            self.transcriptions = []
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
                time_in_seconds.append(self.get_seconds_from_tier(tier))
                if self.is_major_language(wordlist, spanish=True):
                    continue
                transcriptions[candidate][tierID] = wordlist
        self.secondstranscribed = sum(time_in_seconds)
        self.transcriptions = transcriptions

    def populate_translations(self):
        """fill the attribute translation with translations from the ELAN file"""

        translationcandidates = ACCEPTABLE_TRANSLATION_TIER_TYPES
        root = self.root
        if root is None:
            self.transcriptions = []
            return
        # we check the XML file which of the frequent names for translation tiers it uses
        # there might be several translation tiers with different names, hence we store them
        # in a dictionary
        translations = defaultdict(dict)
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
                    translations[candidate][tierID] = wordlist
        self.translations = translations

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

        def get_parent_element_ID_dic(root):
            # querystring = (
            # ".//REF_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % annotation_ref
            # )
            get_parent_element_ID_dic = {
                ref_annotation.attrib.get("ANNOTATION_ID"): ref_annotation.getparent()
                for ref_annotation in root.findall(".//REF_ANNOTATION")
            }
            return get_parent_element_ID_dic

        def get_glossed_sentences(annos):
            ws = [mapping.get(annotation.parentID, "") for annotation in annotations]
            ids = [
                self.timeslottedancestors[annotation.ID] for annotation in annotations
            ]
            current_sentence_ID = None
            d = {}
            glossed_sentences = []
            for i, annotation in enumerate(annos):
                gloss = annos[i].text
                word = ws[i]
                sentenceID = ids[i]
                if sentenceID != current_sentence_ID:
                    if current_sentence_ID:
                        glossed_sentences.append(d)
                    current_sentence_ID = sentenceID
                    d = {sentenceID: [(word, gloss)]}
                else:
                    try:
                        d[sentenceID].append((word, gloss))
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
        glosscandidates = ACCEPTABLE_GLOSS_TIER_TYPES
        mapping = get_annotation_text_mapping(root)
        retrieved_glosstiers = {}

        # annotationdic = {
        #     el[0].attrib["ANNOTATION_ID"]: Annotation(el, self.timeslots)
        #     for el in root.findall(".//ANNOTATION")
        # }  # TODO this should probably be in init
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
                        Annotation(el, self.timeslots)
                        for el in tier.findall(".//ANNOTATION")
                    ]
                    # try:
                    # glossed_sentences = get_glossed_sentences(annotations)
                    # except KeyError:
                    # print("problematic parent relations in ", self.path, tierID)
                    # continue
                    retrieved_glosstiers[candidate][tierID] = get_glossed_sentences(annotations)
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
        self.translations = []

    def transcriptions_from_tiers(self):
        self.transcriptions = []

    def glosses_from_tiers(self):
        self.glosses = []

    def annotation_time(self):
        self.annotation_time = 0

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

    def print_overview(self):
        filename = self.path.split('/')[-1]
        outputstring = f"{filename[:28]}...{filename[-8:-4]}"
        print(outputstring, end=" ")
        if self.transcriptions:
            print(str(len(self.get_transcriptions()[0])).rjust(4,' '),end=" ")
        else:
            print("0".rjust(4,' ') ,end=" ")
        if self.translations:
            print(str(len(self.get_translations()[0])).rjust(4,' '),end=" ")
        else:
            print("0".rjust(4,' ') ,end=" ")
        try:
            if self.glossed_sentences:
                print(str(len(self.glossed_sentences.popitem()[1].popitem()[1])).rjust(4,' '))
            else:
                print("0".rjust(4,' ') ,end=" ")
        except AttributeError:
            print("0".rjust(4,' ') ,end=" ")

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


class Annotation:
    def __init__(self, element, timeslots):
        """
        """

        if element is None:
            raise ValueError("Annotation is None")
        if element.tag not in ["ANNOTATION", "ALIGNABLE_ANNOTATION"]:
            logger.warning(f"{element.tag} is not an <(ALIGNABLE_)ANNOTATION> element")
            raise ValueError(f"{element.tag} is not an <(ALIGNABLE_)ANNOTATION> element")
        self.text = ""
        self.starttime = 0
        self.endtime = 0
        self.ID = None
        self.parentID = None
        # ELAN stores the annotation information in two different types of elements.
        # One is ANNOTATION, the other one is ALIGNABLE_ANNOTATION. We do not know which
        # kind is submitted to the constructor. If it is ANNOTATION, we have to drill
        # down the DOM to find ALIGNABLE_ANNOTATION
        if element.tag == "ANNOTATION":
            alignable_annotation = element.find(".//ALIGNABLE_ANNOTATION")
        else:
            alignable_annotation = element
        annotation_value = element.find(".//ANNOTATION_VALUE")
        ref_annotation = element.find(".//REF_ANNOTATION")
        try:
            self.text = annotation_value.text
        except AttributeError:
            pass
        if alignable_annotation is None:  # not time aligned
            if ref_annotation is  None:
                print("Annotation without ID in", self.text)
                print(element[0].text)
                raise ValueError
                self.ID = None
                self.parentID = None
            else:
                self.ID = ref_annotation.attrib["ANNOTATION_ID"]
                self.parentID = ref_annotation.attrib["ANNOTATION_REF"]
        else: #   time aligned
            self.ID = alignable_annotation.attrib["ANNOTATION_ID"]
            self.parentID = None
            try:
                self.starttime = int(
                    timeslots[alignable_annotation.attrib["TIME_SLOT_REF1"]]
                )
                self.endtime = int(
                    timeslots[alignable_annotation.attrib["TIME_SLOT_REF2"]]
                )
            except KeyError:
                pass

    def get_duration(self):
        """
        compute the duration by subtracting start times from end time
        """

        return self.endtime - self.starttime






ACCEPTABLE_TRANSLATION_TIER_TYPES = [
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


ACCEPTABLE_TRANSCRIPTION_TIER_TYPES = [
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

ACCEPTABLE_WORD_TIER_TYPES = [
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

ACCEPTABLE_GLOSS_TIER_TYPES = [
    "ge",
    "morph-item",
    "gl",
    "Gloss",
    "gloss",
    "glosses",
    "word-gls",
    "gl (interlinear gloss)",
]

ACCEPTABLE_POS_TIER_TYPES = ["ps", "parts of speech"]
