"""
A representation of an ELAN file
"""

import requests
from collections import Counter
import lod
from lxml import etree
from collections import defaultdict
from langdetect import detect_langs,  lang_detect_exception
import logging 

class ElanFile():
    def __init__(self, path, url, namespace=None):
        #self.name = name
        self.path = path
        self.ID = ''
        self.url = url 
        self.namespace = namespace
        self.tiers = []
        self.vernaculartiers = []
        self.translationtiers = []
        self.glosstiers = []
        self.get_tier_hierarchy()
        self.create_parent_dic()
        self.timecodes = {}
        self.reftypes = {}
        
        
    LANGDETECTTHRESHOLD = 0.95  # 85% seems to have no false positives in a first run
    
    def xml(self):
        root = etree.parse(self.path)
        return root
        
    def write(self):
        """write the file to the file system"""
        pass
    
    
    def analyze(self, fingerprint=False):
        """
        get information about: 
        - number of words
        - number of glosses
        - time transcribed
        etc
        """
        if fingerprint:
            print("fingerprint of %s is %s"%(self.path, self.fingerprint()))
        
    def get_triples(self, bundle_url=None):
        """
        get RDF triples describing the Resource 
        """
        #metadata triples
        #transcription triples
        #translation triples
        #gloss triples
        #NER triples
        pass
    

    
    def fingerprint(self): 
        """
        check the tiers there are in a given file and
        return a fingerprint describing the structure
        Dots indicate the level
        The type of a tier is indicated by
        - s: subdivision
        - a: association
        - x: anything else
        """
        
        tree = self.xml()
        self.fingerprint = '['
        #start with dummy tier
        self.analyze_tier({'id':self.path,
                    'constraint': 'root',
                    'ltype': ''
                    },
                    0,
                    #lump=lump
                    )    
        self.fingerprint += ']' 
        return self.fingerprint
    
    def analyze_tier(self, d, level, lump=False):
        """analyze a tier and its children""" 
        #print(d)
        constraint = d['constraint']
        code = 'x'
        if constraint == 'Symbolic_Subdivision' or constraint == 'Symbolic Subdivision':
            code = 's'
        elif constraint == 'Symbolic_Association' or constraint == 'Symbolic Association' :
            code = 'a'
        elif constraint == 'Time_Subdivision' or constraint == 'Time Subdivision':
            if lump:
                code = 's'
            else:
                code = 't'
        elif constraint == 'Included_In':
            if lump:
                code = 's'
            else:
                code = 'i'
        elif constraint == 'root':
            code = 'R'
        elif constraint == '':
            code = 'x'
        elif constraint is None:
            code = 'x'
        else:
            print(repr(constraint))
            0/0 
        self.fingerprint += code
        children = self.tier_hierarchy[d['id']] 
        if children == []:
            return
        self.fingerprint += '['
        for child in children:
            self.analyze_tier(child, level+1, lump=lump)        
        self.fingerprint += ']'
    
    def populate_transcriptions(self): # TODO refactor this into smaller methods and functions
        transcriptioncandidates = lod.acceptable_transcription_tier_types
        transcriptions = {}
        root = self.xml()
        time_in_seconds = []
        for candidate in transcriptioncandidates:
            # try different LINGUISTIC_TYPE_REF's to identify the relevant tiers
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            vernaculartiers = root.findall(querystring)
            if vernaculartiers != []:  # we found a tier of the linguistic type
                tierfound = True
                for tier in vernaculartiers:
                    tierID = tier.attrib["TIER_ID"]
                    # create a list of all words in that tier by splitting
                    # and collating all annotation values of that tier
                    wordlist = [
                        av.text.strip()
                        for av in tier.findall(".//ANNOTATION_VALUE")
                        if av.text is not None
                    ]
                    # get a list of duration from the time slots directly mentioned in annotations
                    if wordlist == []:
                        continue
                    try:
                        timeslots = self.get_timeslots(root)
                    except KeyError:
                        timeslots = {}
                    timelist = [
                        Annotation(aa, timeslots).get_duration()
                        for aa in tier.findall(".//ALIGNABLE_ANNOTATION")
                        if aa.find(".//ANNOTATION_VALUE").text is not None
                    ]
                    # get a list of durations from time slots mentioned in parent elements
                    timelistannno = [
                        Annotation(self.get_alignable_annotations(root).get(ra.attrib["ANNOTATION_REF"]),timeslots).get_duration()
                        for ra in tier.findall(".//REF_ANNOTATION")
                        if ra.find(".//ANNOTATION_VALUE").text is not None
                    ]
                    secs = sum(timelist + timelistannno) / 1000
                    time_in_seconds.append(secs)
                    try:  # detect candidate languages and retrieve most likely one
                        toplanguage = detect_langs(" ".join(wordlist))[0]
                    except lang_detect_exception.LangDetectException:
                        #we are happy that this is an unknown language
                        toplanguage = None
                    #print(toplanguage)
                    if (toplanguage
                            and toplanguage.lang == "en"
                            and toplanguage.prob > self.LANGDETECTTHRESHOLD):
                        # language is English
                        logging.warning(
                            'ignored vernacular tier with English language content at %.2f%% probability ("%s ...")'
                            % (toplanguage.prob * 100, " ".join(wordlist)[:100])
                        )
                        continue
                    try:
                        transcriptions[candidate][tierID] = wordlist
                    except KeyError:
                        transcriptions[candidate] = {}
                        transcriptions[candidate][tierID] = wordlist
        self.secondstranscribed = sum(time_in_seconds)
        self.transcriptions = transcriptions
    
    def populate_translations(self):
        translationcandidates = lod.acceptable_translation_tier_types 
        root = self.xml()
        translations = {}
        for candidate in translationcandidates:
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            translationtiers = root.findall(querystring)
            if translationtiers != []:  # we found a tier of the linguistic type
                for tier in translationtiers:
                    tierID = tier.attrib["TIER_ID"]
                    # create a list of all words in that tier
                    wordlist = [
                        av.text.strip()
                        for av in tier.findall(".//ANNOTATION_VALUE")
                        if av.text is not None
                    ]
                    if wordlist == []:
                        continue
                    # sometimes, annotators put non-English contents in translation tiers
                    # for our purposes, we want to discard such content
                    try:  # detect candidate languages and retrieve most likely one
                        toplanguage = detect_langs(" ".join(wordlist))[0]
                    except lang_detect_exception.LangDetectException:
                        logging.warning(
                            "could not detect language for %s in %s" % (wordlist, filename)
                        )
                        continue
                    if toplanguage.lang != "en":
                        continue
                    if toplanguage.prob < self.LANGDETECTTHRESHOLD:
                        # language is English, but likelihood is too small
                        logging.warning(
                            'ignored %.2f%% probability English for "%s ..."'
                            % (toplanguage.prob * 100, " ".join(wordlist)[:100])
                        )
                        continue
                    #how many words should the average annotation have for this
                    #tier to be counted as translation?
                    translation_minimum = 1.5
                    avg_annotation_length = sum(
                        [len(x.strip().split()) for x in wordlist]
                    ) / len(wordlist)
                    if avg_annotation_length < translation_minimum:
                        logging.warning(
                            "%s has too short annotations (%s) for the tier to be a translation (%s ,...)"
                            % (tierID,
                            avg_annotation_length,
                            ", ".join(wordlist[:3])
                            )
                        )
                        continue
                    try:
                        translations[candidate][tierID] = wordlist
                    except KeyError:
                        translations[candidate] = {}
                        translations[candidate][tierID] = wordlist
        self.translations = translations
        
    def get_translations(self):
        return [self.translations[tier_type][tierID]
                for tier_type in self.translations
                for tierID in self.translations[tier_type]
                ]      
    
    def get_transcriptions(self):
        return [self.transcriptions[tier_type][tierID]
                for tier_type in self.transcriptions
                for tierID in self.transcriptions[tier_type]
                ]
                
    def get_glosses(self):
        return [self.glosses[tier_type][tierID]
                for tier_type in self.glosses
                for tierID in self.glosses[tier_type]
                ]
    
    def populate_glosses(self):
        """retrieve all glosses from an eaf file and map to text from parent annotation"""

        def get_word_for_gloss(annotation_value):
            """retrieve the parent annotation's text"""

            # get the XML parent, called <REF_ANNOTATION>
            ref_annotation = annotation_value.getparent()
            # find the attributed called ANNOTATION_REF, which gives the ID of the referred annotation
            annotation_ref = ref_annotation.attrib["ANNOTATION_REF"]
            # retrieve the referenced annotation
            querystring = (
                ".//REF_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % annotation_ref
            )
            parent = root.find(querystring)
            try:
                return parent.text
            except AttributeError:
                return None

        glosscandidates = lod.acceptable_gloss_tier_types
        retrieved_glosstiers = {}
        
        root = self.xml()                                    
            
        for candidate in glosscandidates:
            querystring = "TIER[@LINGUISTIC_TYPE_REF='%s']" % candidate
            glosstiers = root.findall(querystring)
            if glosstiers != []:  # we found a tier of the linguistic type
                retrieved_glosstiers[candidate] = {}
                for tier in glosstiers:
                    tierID = tier.attrib["TIER_ID"]
                    parent = invertedparentdic[tierID] 
                    print(tier, tierID, parent.attrib["TIER_ID"])
                    parentID = parent.attrib["TIER_ID"]
                    parent_type = parent.attrib["LINGUISTIC_TYPE_REF"]
                    if not parent_type in lod.acceptable_word_tier_types:
                        logging.warning(
                            "%s: Type %s is not accepted for potential parent %s of gloss candidate %s" %
                            (self.path, parent_type, parentID, tierID)
                        )
                        continue
                    # create a list of all annotations in that tier
                    annotations = tier.findall(".//ANNOTATION_VALUE")
                    # retrieve the text values associated with the parent annotations
                    #(i.e., the vernacular words)
                    words = [get_word_for_gloss(annotation) for annotation in annotations]
                    # retrieve the glosses
                    glosses = [
                        "" if av.text is None else av.text.strip() for av in annotations
                    ]
                    #print(len(words), len(glosses))
                    retrieved_glosstiers[candidate][tierID] = (words, glosses) 
        self.glosses = retrieved_glosstiers
                    
    def create_parent_dic(self):
        """
        match all tier IDs with the referenced parent IDs

        The parents are not the XML parents but are different tiers,
        which are the logical parents of a tier
        """
        d = {}
        for tier_ID in self.tier_hierarchy:
            for child in self.tier_hierarchy[tier_ID]: 
                
                d[child['id']] = tier_ID 
        self.child_parent_dic = d
        
    def get_tier_hierarchy(self):
        tree = self.xml()
        dico = defaultdict(list)
        linguistic_types = tree.findall(".//LINGUISTIC_TYPE")
        #map tier IDs to their constraints
        tierconstraints = {lt.attrib["LINGUISTIC_TYPE_ID"]:lt.attrib.get("CONSTRAINTS") for lt in linguistic_types}
        tiers = tree.findall(".//TIER")
        for tier in tiers:
            ID = tier.attrib["TIER_ID"]
            #map all tiers to their parent tiers, defaulting to the file itself
            PARENT_REF = tier.attrib.get("PARENT_REF", (self.path))
            ltype = tier.attrib["LINGUISTIC_TYPE_REF"]
            try:
                constraint = tierconstraints[ltype]
            except KeyError:
                print("reference to unknown LINGUISTIC_TYPE_ID  %s when establishing constraints in %s" %(ltype,self.path))
                continue
            dico[PARENT_REF].append({'id': ID,
                                    'constraint': constraint,
                                    'ltype': ltype
                                    }
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
        
    def get_timeslots(self, xml):
        """
        Create a dictionary with time slot ID as keys and offset in ms as values
        """

        timeorder = xml.find(".//TIME_ORDER")
        timeslots = {slot.attrib["TIME_SLOT_ID"]:slot.attrib["TIME_VALUE"]
                    for slot
                    in timeorder.findall("TIME_SLOT")
                    }
        return timeslots
    
    def get_alignable_annotations(self,root):
        """
        Create a dictionary with alignable annotations ID as keys and the elements themselves as values
        """

        aas = root.findall(".//ALIGNABLE_ANNOTATION")
        return {aa.attrib["ANNOTATION_ID"]:aa for aa in aas}
    
 
        
class Tier():
    def __init__(self):
        self.ID = '' # the ID as used in the Elan file
        self.reftypename = '' #the reftype used in the elan file
        self.constrainttype = '' #subdivision, association, etc
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
        for key in LGRLIST:
            if key not in LGRLIST:
                del result[key]
        return result
    
    def get_entities(self): 
        """sent text to online resolver and retrieve wikidataId's"""

        url = "http://cloud.science-miner.com/nerd/service/disambiguate"
        text = self.get_annotation_text()
        if len(text.split()) < 5: #cannot do NER on less than 5 words
            return []
        #send text 
        rtext = requests.post(url, json={"text": text}).text
        #parse json
        retrieved_entities = json.loads(rtext).get("entities", [])
        #extract names and wikidataId's
        return [(x["rawName"], x["wikidataId"])
                for x in retrieved_entities
                if x.get("wikidataId") and x["wikidataId"] not in lod.NER_BLACKLIST]
        
class Annotation():
    def __init__(self, element,timeslots):
        self.ID = ''
        self.value = ''
        self.parentref = ''
        try:
            self.starttime = int(
                timeslots[element.attrib["TIME_SLOT_REF1"]])
        except AttributeError:
            self.starttime = 0
        except KeyError:
            self.starttime = 0
        try:
            self.endtime = int(
                timeslots[element.attrib["TIME_SLOT_REF2"]])
        except AttributeError:
            self.endtime = 0
        except KeyError:
            self.endtime = 0
        
    def get_duration(self):
        """
        compute a list of durations of each annotation by substracting start times from end times
        """

        return self.endtime - self.starttime     
