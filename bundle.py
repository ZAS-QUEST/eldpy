"""
A bundle with primary material in and about endangered languages
Bundles are not found in all archives. In archives without
bundles, we use one-bundle collections.
"""

class Bundle():
    def __init__(self, name, url, namespace=None):
        self.name = name
        self.ID = ''
        self.url = url
        self.elanfiles = []
        self.namespace = namespace
        
    def populate_elanfiles(self):
        pass      

    def analyze_elanfiles(self):
        """
        get information about: 
        - number of words
        - number of glosses
        - time transcribed
        etc
        """
        pass
        
    def get_triples(self, collection_url=None):
        """
        get RDF triples describing the Resource 
        """
        pass
    
    def get_recursive_triples(self):
        triples = self.get_triples()
        for elanfile in self.elanfiles:
            triples += elanfile.get_triples(bundle_url=self.url)
        return triples
            
        
