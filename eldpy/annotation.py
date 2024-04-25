
class Annotation:
    def __init__(self, element, timeslots, ref_annotations, alignable_annotations):
        """ """

        if element is None:
            raise ValueError("Annotation is None")
        if element.tag not in ["ANNOTATION", "ALIGNABLE_ANNOTATION"]:
            logger.warning(f"{element.tag} is not an <(ALIGNABLE_)ANNOTATION> element")
            raise ValueError(
                f"{element.tag} is not an <(ALIGNABLE_)ANNOTATION> element"
            )
        self.text = ""
        self.starttime = 0
        self.endtime = 0
        self.ID = None
        self.parent_id = None
        self.previous_annotation_ID = None
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
            if ref_annotation is None:
                print("Annotation without ID in", self.text)
                print(element[0].text)
                raise ValueError
                self.ID = None
                self.parent_id = None
            else:
                self.ID = ref_annotation.attrib["ANNOTATION_ID"]
                self.parent_id = ref_annotation.attrib["ANNOTATION_REF"]
                self.previous_annotation_ID = ref_annotation.attrib.get("PREVIOUS_ANNOTATION")
                try:
                    parentAnnoID = ref_annotations[self.parent_id]
                    parentAnno = alignable_annotations[parentAnnoID]
                    startslot = parentAnno[0]
                    endslot =  parentAnno[1]
                    self.starttime = timeslots[startslot]
                    self.endtime = timeslots[endslot]
                except KeyError:
                    pass
        else:  #   time aligned
            self.ID = alignable_annotation.attrib["ANNOTATION_ID"]
            self.parent_id = None
            try:
                self.starttime = int(
                    timeslots[alignable_annotation.attrib["TIME_SLOT_REF1"]]
                )
                self.endtime = int(
                    timeslots[alignable_annotation.attrib["TIME_SLOT_REF2"]]
                )
            except KeyError:
                pass

    def get_duration(self, include_void_annotations=True):
        """
        compute the duration by subtracting start times from end time
        """
        if include_void_annotations or self.text:
            return int(self.endtime) - int(self.starttime)
        else:
            return 0

