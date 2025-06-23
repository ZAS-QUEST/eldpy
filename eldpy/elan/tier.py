from collections import Counter

class Tier:
    def __init__(self):
        self.ID = ""  # the ID as used in the Elan file
        self.reftypename = ""  # the reftype used in the elan file
        self.constrainttype = ""  # subdivision, association, etc
        self.parenttier = None
        self.annotations = []
        self.annotation_values = []
        self.rawglosses = []

    # def get_annotated_time(self):
    #     pass
    #
    # def get_annotation_text(self):
    #     return []

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
                person = personnumberdic[k][0]
                number = personnumberdic[k][1]
                occurrences = cleanglosses[k]
                cleanglosses[person] += occurrences
                cleanglosses[number] += occurrences
                del cleanglosses[k]
        return cleanglosses

    def get_lgr_glosses(self):
        """return all glosses which are in the Leipzig Glossing Rules"""

        result = self.get_gloss_count()
        for key in result:
            if key not in constants.LGRLIST:
                del result[key]
        return result

