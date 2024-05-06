import re

import time
from langdetect import detect_langs, lang_detect_exception


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

    return [  # FIXME use generic method
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
    accepted_languages = ["en"],
    # spanish=False,
    # french=False,
    # indonesian=False,
    # portuguese=False,
    # russian=False,
    logtype="False",
    logger=None
):
    """
    return True if this string is from a language of wider communication,
    which could possibly be used for a translation tier
    """

    LANGDETECTTHRESHOLD = 0.95  # 85% seems to have no false positives in a first run
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
        and toplanguage.prob > LANGDETECTTHRESHOLD
    ):
        if logtype == "True":
            probability_percentage = toplanguage.prob * 100
            tier_start_words =  " ".join(list_)[:100]
            if logger:
                logger.info(f'ignored vernacular tier with {toplanguage.lang} language content at {probability_percentage:.2f}% probability ("{tier_start_words} ...")')
        return True
    if toplanguage is None:
        if logtype == "False" and logger:
            logger.warning(f"could not detect language for {list_}")
        return False
    if toplanguage.prob < LANGDETECTTHRESHOLD:
        # language is English or Spanish, but likelihood is too small
        if logtype == "False":
            percentage_probablity = toplanguage.prob * 100
            tier_first_words = " ".join(list_)[:100]
            if logger:
                logger.info(f'ignored {percentage_probablity:.2f}% probability {toplanguage.prob} for "{tier_first_words} ..."')
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
