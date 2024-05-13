"""
Helper functions to deal with ELAN files
"""

import re
import time
from collections import defaultdict
from langdetect import detect_langs, lang_detect_exception
from eldpy.eldpyerror import EldpyError


LANGDETECT_THRESHOLD = 0.95  # 85% seems to have no false positives in a first run


def tier_to_id_wordlist(t):
    """
    create a list of all words in that tier by splitting
    and collating all annotation values of that tier
    """

    result = []
    for ref_ann in t.findall(".//REF_ANNOTATION") + t.findall(
        ".//ALIGNABLE_ANNOTATION"
    ):
        ref_ann_id = ref_ann.attrib["ANNOTATION_ID"]
        try:
            annotation_text = ref_ann.find(".//ANNOTATION_VALUE").text.strip()
        except AttributeError:
            # there is no text
            annotation_text = ""
        result.append((ref_ann_id, annotation_text))
    return result


def tier_to_wordlist(t):
    """
    extract all strings representing words from a tier
    """

    tier_with_ids = tier_to_id_wordlist(t)
    result = [el[1] for el in tier_with_ids]
    return result


def tier_to_annotation_id_list(t):
    """
    create a list of all IDs in that tier
    """

    return [
        (ra.attrib["ANNOTATION_ID"], ra.attrib["ANNOTATION_REF"])
        for ra in t.findall(".//REF_ANNOTATION")
    ]


def is_id_tier(wl):
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
    return False


def is_major_language(
    list_,
    accepted_languages=("en",),
    # spanish=False,
    # french=False,
    # indonesian=False,
    # portuguese=False,
    # russian=False,
    logtype="False",
    logger=None,
):
    """
    return True if this string is from a language of wider communication,
    which could possibly be used for a translation tier
    """

    try:  # detect candidate languages and retrieve most likely one
        toplanguages = detect_langs(" ".join(list_))
        toplanguage = toplanguages[0]
    except lang_detect_exception.LangDetectException:
        # we are happy that this is an unknown language
        toplanguage = None

    # if spanish:
    #     accepted_languages.append("es")
    # if french:
    #     accepted_languages.append("fr")
    # if indonesian: #indonesian causes some random errors for muyu
    #     pass
    # #     accepted_languages.append("id")
    # if portuguese:#portuguese throws falls positives
    #     pass
    # #     accepted_languages.append("pt")
    # if russian:
    #     accepted_languages.append("ru")
    # print(toplanguage.lang,toplanguage.prob,accepted_languages)
    if (
        toplanguage
        and toplanguage.lang in accepted_languages
        and toplanguage.prob > LANGDETECT_THRESHOLD
    ):
        if logtype == "True":
            probability_percentage = toplanguage.prob * 100
            tier_start_words = " ".join(list_)[:100]
            if logger:
                logger.info(
                    f'ignored vernacular tier with {toplanguage.lang} language content at {probability_percentage:.2f}% probability ("{tier_start_words} ...")'
                )
        return True
    if toplanguage is None:
        if logtype == "False" and logger:
            logger.warning(f"could not detect language for {list_}")
        return False
    if toplanguage.prob < LANGDETECT_THRESHOLD:
        # language is English or Spanish, but likelihood is too small
        if logtype == "False":
            percentage_probablity = toplanguage.prob * 100
            tier_first_words = " ".join(list_)[:100]
            if logger:
                logger.info(
                    f'ignored {percentage_probablity:.2f}% probability {toplanguage.prob} for "{tier_first_words} ..."'
                )
        return False
    return False


def get_alignable_annotations(root):
    """
    Create a dictionary with alignable annotations ID as keys and the elements themselves as values
    """

    aas = root.findall(".//ALIGNABLE_ANNOTATION")
    return {aa.attrib["ANNOTATION_ID"]: aa for aa in aas}


def readable_duration(seconds):
    """return the duration in seconds in human readable format"""

    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def get_zipfs(distinct_glosses):
    """
    count glosses in a tier and order by rank. Return the ration of
    #1/#2 and #2/#3. This is useful to check whether a tier contains
    natural language or repetitive glosses
    """

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
    return zipf1, zipf2


def get_words_from_translation_tiers(translation_tier_names, translations, logger=None):
    """
    extract the natural language words from a translation tier.
    Return an array of words as well as the count of translated sentences
    """

    words = []
    translated_sentence_count = 0
    if len(translation_tier_names) > 1:
        logger.warning("more than one translation tier found")
    if len(translation_tier_names) > 0:
        for translation_tier in translations:
            for at_name in translations[translation_tier].values():
                for sentence in at_name:
                    translated_sentence_count += 1
                    current_words = sentence.split()
                    words += current_words
    return words, translated_sentence_count


def get_words_from_transcription_tiers(
    transcription_tier_names, transcriptions, logger=None
):
    """
    extract the natural language words from a transcription tier.
    Return an array of words as well as the count of transcribed  sentences
    """

    words = []
    transcribed_sentence_count = 0
    if logger and len(transcription_tier_names) > 1:
        logger.warning("more than one transcription tier found")
    if len(transcription_tier_names) > 0:
        for transcription_tier in transcriptions:
            for at_name in transcriptions[transcription_tier].values():
                for sentence in at_name:
                    transcribed_sentence_count += 1
                    current_words = sentence.split()
                    words += current_words
    return words, transcribed_sentence_count


def get_gloss_metadata(gloss_tier_tokens, logger=None):
    """
    return the number of distinct_glosses and of glossed sentences in a tier
    """

    glossed_sentences_count = 0
    distinct_glosses = defaultdict(int)
    distinct_glossed_sentences = {}
    if len(gloss_tier_tokens) > 1:
        logger.warning("More than one gloss tier found")
    for at_name in gloss_tier_tokens.values():
        glossed_sentences_count += len(at_name)
        for gloss_list in at_name:
            distinct_glossed_sentences[list(gloss_list.keys())[0]] = True
            try:
                tuples = list(gloss_list.values())[0]
            except IndexError:
                continue
            for t in tuples:
                gloss = t[1]
                if gloss is None:
                    continue
                if gloss == "***":
                    continue
                max_ascii = max(ord(c) for c in gloss)
                if max_ascii < 65:  # we have no letters in gloss
                    continue
                distinct_glosses[gloss] += 1
    return distinct_glosses, len(distinct_glossed_sentences)


def get_annotation_text_mapping(root):
    """
    map annotation IDs to the XML texts found in the annotation
    """

    if root is None:
        return {}
    textdic = {
        ref_annotation.attrib.get("ANNOTATION_ID"): ref_annotation.find(
            "./ANNOTATION_VALUE"
        ).text
        for ref_annotation in root.findall(".//REF_ANNOTATION")
    }
    return textdic


def increment_key(s, tier_type, logger=None):
    """
    increment the integer value of an ID by 1
    """

    m = re.match("(a)(n*)([0-9]+)", s)
    if not m:
        if logger:
            logger.warning(f"{tier_type} {s} could not be retrieved")
        return None
    prefix = "".join(m.groups()[:2])
    integer_part = m.groups()[2]
    next_integer = int(integer_part) + 1
    return f"{prefix}{next_integer}"


def get_translation_text(d, id_, logger=None):
    """
    get the translation for an annotation
    """

    try:
        translation = d[id_]
    except KeyError:
        try:
            new_key = increment_key(id_, "translation", logger=logger)
            translation = d[new_key]
        except KeyError:
            if logger:
                logger.warning(
                    f"translation {id_} could not be retrieved, nor could {new_key} be retrieved"
                )
                return None
    return translation


def get_transcription_text(
    transcription_id_dict, id_, timeslotted_reversedic, logger=None
):
    """
    get the transcription for an annotation
    """

    try:
        primary_text = transcription_id_dict[id_]
    except KeyError:
        try:
            new_key = increment_key(id_, "primary text")
            primary_text = transcription_id_dict[new_key]
        except KeyError:
            # we try to retrieve a tier dependent on the ref tier which does have a primary text
            for v in timeslotted_reversedic[id_]:
                primary_text = transcription_id_dict.get(v)
                if primary_text:
                    break
            else:
                if logger:
                    logger.warning(
                        f"primary text {id_} could not be retrieved, nor could {new_key} be retrieved"
                    )
                    return None
    return primary_text


def get_translation_retain(tmp_translations_dict, logger=None):
    """
    among the tiers given, retrieve the tier which is most likely
    to be a translation tier
    """

    translation_tier_to_retain = {}
    translation_tiername_to_retain = ""
    max_charcount = 0
    for type_candidate in tmp_translations_dict:
        for tier in tmp_translations_dict[type_candidate]:
            charcount = 0
            for top_element in tmp_translations_dict[type_candidate][tier]:
                charcount += len(
                    tmp_translations_dict[type_candidate][tier][top_element]
                )
            if charcount >= max_charcount:
                max_charcount = charcount
                translation_tiername_to_retain = tier
                translation_tier_to_retain = tmp_translations_dict[type_candidate][tier]
    if logger:
        logger.info(
            f"  retaining {translation_tiername_to_retain} as the tier with most characters ({max_charcount})"
        )
    return translation_tier_to_retain


def get_glosstier_to_retain(glosses_d, provided_gloss_tier_name):
    """
    among the tiers given, retrieve the tier which is most likely
    to be a translation tier
    """

    best_tier_ratio = 0
    glosstiername_to_retain = ""
    glosstier_to_retain = {}
    for type_candidate in glosses_d:
        for tier in glosses_d[type_candidate]:
            tier_glosses = []
            for current_annotation in glosses_d[type_candidate][tier]:
                for element in current_annotation:
                    glosses = [x[1] for x in current_annotation[element]]
                    tier_glosses += glosses
            distinct_glosses = list(set(tier_glosses))
            try:
                ratio = len(distinct_glosses) / len(tier_glosses)
            except ZeroDivisionError:
                ratio = 0
            if provided_gloss_tier_name and tier == provided_gloss_tier_name:
                best_tier_ratio = 100
                glosstiername_to_retain = tier
                glosstier_to_retain = glosses_d[type_candidate][tier]
                break
            if ratio > best_tier_ratio:
                best_tier_ratio = ratio
                glosstiername_to_retain = tier
                glosstier_to_retain = glosses_d[type_candidate][tier]
    return glosstier_to_retain, glosstiername_to_retain


def get_line(
    g,
    transcription_id_dict,
    timeslotted_reversedic,
    translation_id_dict,
    comments_id_dict,
    logger=None,
):
    """
    compute one line for the output in a metadata sheet
    """

    if g == {}:
        return ["", "", "", "", "", "", ""]
    vernacular_subcells = []
    gloss_subcells = []
    id_, word_gloss_list = g.popitem()
    for tupl in word_gloss_list:
        vernacular = tupl[0]
        gloss = tupl[1]
        if vernacular is None and gloss is None:
            # no need to act
            continue
        if vernacular is None:
            # raise EldpyError(f"empty transcription with gloss {tupl[0]}:{tupl[1]} in " , logger=logger)
            if logger:
                logger.warning(
                    f"empty transcription with gloss {repr(tupl[0])}:{repr(tupl[1])}. Setting vernacular to ''"
                )
            vernacular = ""
        if gloss is None:
            # logger.warning(f"empty transcription with gloss {repr(tupl[0])}:{repr(tupl[1])} in {self.path}. Setting gloss to ''")
            gloss = ""
        vernacular_subcells.append(vernacular)
        gloss_subcells.append(gloss)

    primary_text = get_transcription_text(
        transcription_id_dict, id_, timeslotted_reversedic, logger=logger
    )
    if primary_text is None:
        primary_text = "PRIMARY TEXT NOT RETRIEVED"
    translation = get_translation_text(translation_id_dict, id_, logger=logger)
    if translation is None:
        translation = "TRANSLATION NOT RETRIEVED"

    line = [
        id_,
        primary_text or "",
        "\t".join(vernacular_subcells) or "",
        "\t".join(gloss_subcells) or "",
        translation or "",
        comments_id_dict.get(id_, ""),
        check_lgr_alignment(vernacular_subcells,gloss_subcells),
    ]
    return line

def check_lgr_alignment(vernaculars, glosses):
    """
    Check whether glosses are only word-aligned, or whether
    the numbers of hyphens/equal signs match between vernacular
    and gloss cell.
    If the hyphens/glosses do not  match between at least one
    cell, the whole tier is word-aligned only. If all match, the
    tier is morpheme-aligned
    """

    assert len(vernaculars)==len(glosses)
    for i, _ in enumerate(vernaculars):
        if get_signature(vernaculars[i]) != get_signature(glosses[i]):
            return "WORD_ALIGNED"
    return "MORPHEME_ALIGNED"


def get_signature(s):
    """
    retrieve all hyphens and equal signs from a string and
    return a string collating all of them in order
    """

    return ''.join([ch if ch in "-=" else "" for ch in s])


def get_transcription_id_dict(tmp_transcription_dic):
    """
    map IDs to transcription text
    """

    transcription_id_dict = {}
    for candidate in tmp_transcription_dic:
        for tier in tmp_transcription_dic[candidate]:
            for tupl in tmp_transcription_dic[candidate][tier]:
                transcription_id_dict[tupl[0]] = tupl[1]
    return transcription_id_dict


def get_translation_id_dict(tmp_translations_dict, logger=None):
    """
    map IDs to transcription text
    """

    translation_id_dict = {}
    try:
        translation_tier_to_retain = get_translation_retain(
            tmp_translations_dict, logger=logger
        )
        translation_id_dict = translation_tier_to_retain
    except (ValueError, AttributeError, KeyError) as exc:
        raise EldpyError("No translations found", logger=logger) from exc
    return translation_id_dict


def get_comments_id_dict(tmp_comments_dict, logger=None):
    """
    map IDs to comment text
    """

    comments_id_dict = {}
    try:
        comments_id_dict = tmp_comments_dict.popitem()[1].popitem()[1]
    except KeyError:
        if logger:
            logger.info("no comments")
    return comments_id_dict


def get_glossed_sentences(annos, timeslottedancestors, mapping, logger=None):
    """
    retrieve all glosses together with their transcriptions and map them
    to their timeslotted ancestor
    """

    ws = [mapping.get(annotation.parent_id, "") for annotation in annos]
    ids = [timeslottedancestors.get(annotation.id_, None) for annotation in annos]
    current_sentence_id = None
    d = {}
    new_glossed_sentences = []
    for i, current_annotation in enumerate(annos):
        gloss = annos[i].text
        sentence_id = ids[i]
        if current_annotation.previous_annotation_id is None:
            word = ws[i]
        else:
            try:
                d[sentence_id][-1][1] += gloss
            except TypeError:
                pass
            except KeyError:
                if logger:
                    logger.warning(
                        f"tried to update non-existing word for gloss {sentence_id}"
                    )
            continue
        if sentence_id != current_sentence_id:
            if current_sentence_id:
                new_glossed_sentences.append(d)
            current_sentence_id = sentence_id
            d = {sentence_id: [[word, gloss]]}
        else:
            try:
                d[sentence_id].append([word, gloss])
            except KeyError:
                if logger:
                    logger.warning(
                        f"gloss with no parent {sentence_id} > {annos[i].id_}"
                    )
    new_glossed_sentences.append(d)
    return new_glossed_sentences
