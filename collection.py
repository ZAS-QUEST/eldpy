"""
A collection with primary material in and about endangered languages.
"""

class Collection():
    def __init__(self, name, url, namespace=None):
        self.name = name
        self.ID = ''
        self.url = url
        self.bundles = []
        self.namespace = namespace
          
    def populate_bundles(self):
        pass   
    
    def analyze_bundles(self):
        """
        get information about: 
        - number of words
        - number of glosses
        - time transcribed
        etc
        """
        pass
        
    def get_triples(self):
        """
        get RDF triples describing the Resource 
        """
        pass
    
    def get_recursive_triples(self, archive_url=None):
        triples = self.get_triples()
        for bundle in self.bundles:
            triples += bundle.get_recursive_triples(collection_url=self.url)
        return triples
        
    def paradisec_eaf_download(self, filename):
        #compute urls to use
        #PARADISEC has a naming scheme for URLs which can be inferred
        #from eaf file names. 
        archive_url = "http://catalog.paradisec.org.au/repository/%s/%s/%s" 
        first, second, thirdthrowaway = filename.split('-')    
        url = archive_url%(first, second, filename)
        with requests.Session() as s:
            eafcontent = s.post(url, cookies=cookie).text
        #abort if fetched data is HTML because this is an error message
        if eafcontent.startswith("<!DOCTYPE html>"):
            #print("no access")
            return None
        return eafcontent
    
    def elar_eaf_download(filename):          
            #check for validity of ID
            try:
                soasID = filename.split("oai:soas.ac.uk:")[1]  
            except IndexError: #filename does not start with oai:soas.ac.uk:, so we are not interested
                return None
            #prepare request
            url = "https://elar.soas.ac.uk/Record/%s" % soasID
            phpsessid = ""
            cookie = {'PHPSESSID': phpsessid} 
            #user, password = open('password').read().strip().split(',') #it is unclear whether we need user and pw; possibly the Session ID is sufficient
            #payload = {'user':user, 'password':password}
            
            #retrieve catalog page 
            with requests.Session() as s:
                #r = s.post(url, cookies=cookie, data=payload)
                r = s.post(url, cookies=cookie)
                html = r.text
                #extract links to ELAN files
                try:
                    links = fromstring(html).findall('.//tbody/tr/td/a')    
                    eaflocations = list(set([a.attrib["href"] for a in links if a.attrib["href"].endswith('eaf')])) #make this configurable for other types
                except AttributeError:
                    return
                #dowload identified files
                retrievedfiles = []
                for eaflocation in eaflocations:          
                    eafname = eaflocation.split('/')[-1] 
                    print("  downloading %s:" %eafname, endchar = ' '), 
                    eafname = "%s.eaf" % eafname[:200] #avoid overlong file names
                    r2 = s.post(eaflocation, cookies=cookie, data=payload) 
                    eafcontent = r2.text  
                    retrievedfiles.append({'eafname':eafcontent})
