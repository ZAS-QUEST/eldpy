"""
An archive with primary material in and about endangered languages
"""

class Archive():
    FILETYPES = {
    "ELAN":"text/x-eaf+xml",
    "Toolbox":"text/x-toolbox-text",
    "transcriber":"text/x-trs",
    "praat":"text/praat-textgrid",
    "Flex":"FLEx"
    }     
    
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.collections = [] 
        
    def populate_collections(self):
        pass
    
    def analyze_collections(self):
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
    
    def get_recursive_triples(self):
        triples = self.get_triples()
        for collection in self.collections:
            triples += collection.get_recursive_triples(archive_url=self.url)
        return triples
        
        
    def getIdentifiers(filename, typ):  
        tree = etree.parse(filename)
        etree.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
        #retrieve all tags <dc:format>
        dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
        #retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
        for dcformat in dcformats: 
            if dcformat.text == typ: 
                identifiers = dcformat.findall("../{http://purl.org/dc/elements/1.1/}identifier")
                return identifiers
            
    def retrieve(xmlfiles, mimetype): 
        #retrieve all identifiers found in the xml files which include relevant mimetype
        globalidentifiers = [getIdentifiers(x,mimetype) for x in xmlfiles]
        #remove empty return values
        records = [x for x in globalidentifiers if x != None]
        #flatten out tuples of multiple identifiers contained in one file 
        IDs = [x2.text for x in records for x2 in x] 
        print("found %i IDs (%i records) with references to %s files"%(len(IDs),len(records),mimetype))
        return IDs, records

    def scan(d, xmlfiles, filetypes):
        print("Scanning %s" % d)    
        for filetype in filetypes:
            IDs, records = retrieve(xmlfiles,filetypes[filetype])
            
    def olaceaf(xmlfile, typ): 
        tree = etree.parse(xmlfile)
        etree.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
        globalidentifiers = []
        dico = defaultdict(list)
        #retrieve all tags <dc:format>
        dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
        #retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
        print(len(dcformats))
        for dcformat in dcformats:  
            if dcformat.text.strip() == typ:  
                identifiers = dcformat.getparent().findall(".//{http://purl.org/dc/elements/1.1/}identifier")            
                globalidentifiers.append(identifiers)
        records = [x for x in globalidentifiers if x != None]
        #flatten out tuples of multiple identifiers contained in one file 
        for IDs in records: 
            for item in IDs: #etree.findall returns list 
                dico[0].append(item.text.strip().replace("<","").replace(">",""))
