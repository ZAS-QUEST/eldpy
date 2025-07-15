from collections import defaultdict
import eldpy.elan.annotation as annotation
from eldpy.helpers import get_alignable_annotations


def has_minimal_translation_length(t, tier_id):
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


def sanitize(s):
    return "".join([ch for ch in s if ord(ch) < 128])


def get_annotation_list(t, timeslots, ref_annotations, alignable_annotations, root):
    """return a list of the annotations for a given tier"""

    aas = get_alignable_annotations(root)
    result = []
    for ref_annotation in t.findall(".//REF_ANNOTATION"):
        if ref_annotation.find(".//ANNOTATION_VALUE").text is not None:
            try:
                anno = annotation.Annotation(
                    aas.get(ref_annotation.attrib["ANNOTATION_REF"]),
                    timeslots,
                    ref_annotations,
                    alignable_annotations,
                )
                result.append(anno)
            except ValueError:
                # there is no text
                continue
    return result


def get_seconds_from_tier(t, timeslots, ref_annotations, alignable_annotations, root):
    """
    get a list of duration from the time slots directly mentioned in annotations
    """

    timelist = [
        annotation.Annotation(
            aa, timeslots, ref_annotations, alignable_annotations
        ).get_duration(include_void_annotations=False)
        for aa in t.findall("./ANNOTATION")
        if aa.text is not None
    ]
    if len(timelist) > 1 and sum(timelist) != 0:
        return sum(timelist) / 1000
    annotation_list = get_annotation_list(
        t, timeslots, ref_annotations, alignable_annotations, root
    )
    found_start_times = []
    cleaned_duration_list = []
    for anno in annotation_list:
        if anno.starttime not in found_start_times:
            cleaned_duration_list.append(anno.get_duration())
            found_start_times.append(anno.starttime)
    return sum(cleaned_duration_list) / 1000


def get_segment_counts(root, path):
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


def create_parent_tier_dic(tier_hierarchy):
    """
    match all tier IDs with the referenced parent IDs

    The parents are not the XML parents but are different tiers,
    which are the logical parents of a tier
    """
    d = {}
    for tier_id in tier_hierarchy:
        for child in tier_hierarchy[tier_id]:
            d[child["id"]] = tier_id
    return d


def get_tier_hierarchy(tree, path):
    """
    map tiers to their parents
    """

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
        parent_ref = tier.attrib.get("PARENT_REF", (path))
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
    return dico


def get_timeslots(root, path):
    """
    Create a dictionary with time slot ID as keys and offset in ms as values
    """

    time_order = root.find(".//TIME_ORDER")
    try:
        timeslots = {
            slot.attrib["TIME_SLOT_ID"]: slot.attrib["TIME_VALUE"]
            for slot in time_order.findall("TIME_SLOT")
        }
    except AttributeError:
        logger.info("No timeslots for {path}")
        timeslots = {}
    return timeslots
