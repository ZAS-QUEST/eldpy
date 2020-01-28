"""
An archive with primary material in and about endangered languages
"""

import glob
import json
from collections import Counter
from lxml.html.soupparser import fromstring

#from random import shuffle
import matplotlib.pyplot as plt
from matplotlib import cm
import squarify

from collection import Collection


# from collections import defaultdict


class Archive:
    FILETYPES = {
        "ELAN": "text/x-eaf+xml",
        "Toolbox": "text/x-toolbox-text",
        "transcriber": "text/x-trs",
        "praat": "text/praat-textgrid",
        "Flex": "FLEx",
    }

    def __init__(self, name, url, collectionprefix="", collection_url_template=""):
        self.name = name
        self.url = url
        self.collectionprefix = collectionprefix
        self.collections = {}
        self.collection_url_template = collection_url_template

    def populate_collections(self):
        if self.name == "ANLA":
            print("loading cached information")
            try:
                with open("cache/links/anla.json") as json_in:
                    cached_links = json.loads(json_in.read())
            except IOError:
                cached_links = {}
            html_files = glob.glob("anla/*html")
            landingpage_template = "https://www.uaf.edu/anla/collections/search/resultDetail.xml?resource=%s"
            print("reading files")
            for f in html_files:
                if f in cached_links:
                    # we already haveinformation about this file
                    if cached_links[f] == {}:
                        continue
                    # transfer information
                    for collection in cached_links[f]:
                        self.collections[collection] = Collection(
                            collection, "url", archive="anla"
                        )
                        self.collections[collection].elanpaths = cached_links[f][
                            collection
                        ]

                # print(f,anla_ID)
                # landingpage = landingpage_template % anla_ID
                else:
                    anla_ID = f[5:-5]  # get rid of "anla/" and ".html"
                    with open(f, encoding="iso8859-1") as c:
                        content = c.read()
                        # print(len(content))
                        try:
                            root = fromstring(content)
                        except ValueError:
                            print(f, "is not valid XML")
                            continue
                        cached_links[f] = {}
                        for link in root.findall(".//td/a"):
                            href = link.attrib.get("href", "")
                            if href.endswith("eaf"):
                                flag = True
                                collection, eaf_file = href.split("/")[-2:]
                                try:
                                    self.collections[collection].elanpaths.append(
                                        eaf_file
                                    )
                                except KeyError:
                                    self.collections[collection] = Collection(
                                        collection, "url", archive="anla"
                                    )  # TODO check for mutliple eaf files
                                    self.collections[collection].elanpaths = [eaf_file]
                                try:
                                    cached_links[f][collection].append(eaf_file)
                                except:
                                    cached_links[f][collection] = [eaf_file]

            print("updating cache")
            with open("cache/links/anla.json", "w") as json_out:
                json_out.write(json.dumps(cached_links, sort_keys=True, indent=4))

        if self.name == "PARADISEC":
            print("loading cached information")
            try:
                with open("cache/links/paradisec.json") as json_in:
                    cached_links = json.loads(json_in.read())
            except IOError:
                cached_links = {}
                print(
                    """please download files from the PARADISEC archive
via
> wget -O paradisec.html "https://catalog.paradisec.org.au/items/search?page=1&per_page=18347"
> grep '<a href="/collections' paradisec.html |grep -o '".*"'|grep -o '[^"]*'| sed "s/\//https:\/\/catalog.paradisec.org.au\//"> itemlist
> wget -w 5 -i itemlist
"""
                )

            landingpage_template = "https://catalog.paradisec.org.au/collections/%s"
            for collection in cached_links:
                self.collections[collection] = Collection(
                    collection,
                    landingpage_template % collection,
                    archive="paradisec",
                    urlprefix=self.collectionprefix,
                    url_template=self.collection_url_template,
                )
                self.collections[collection].elanpaths = [
                    path
                    for bundle in cached_links[collection]
                    for path in cached_links[collection][bundle]
                ]

        if self.name == "ELAR":
            print("loading cached information")
            try:
                with open("cache/links/elar.json") as json_in:
                    cached_links = json.loads(json_in.read())
            except IOError:
                cached_links = {}
                print(
                    """please download files from the ELAR archive
"""
                )
            landingpage_template = "https://elar.soas.ac.uk/Collection/%s"
            for collection in cached_links:
                self.collections[collection] = Collection(
                    collection,
                    landingpage_template % collection,
                    archive="elar",
                    urlprefix=self.collectionprefix,
                    url_template=self.collection_url_template,
                )
                self.collections[collection].elanpaths = [
                    path
                    for bundle in cached_links[collection]
                    for path in cached_links[collection][bundle]
                ]
        if self.name == "TLA":
            print("loading cached information")
            try:
                with open("cache/links/tla.json") as json_in:
                    cached_links = json.loads(json_in.read())
            except IOError:
                cached_links = {}
                print(
                    """please download files from the TLA archive
"""
                )
            landingpage_template = "https://archive.mpi.nl/islandora/object/%s"
            for collection in cached_links:
                tmpc = collection.split('/')[5]
                print(tmpc)
                self.collections[tmpc] = Collection(
                    tmpc,
                    landingpage_template % tmpc,
                    archive="tla",
                    urlprefix=self.collectionprefix,
                    url_template=self.collection_url_template,
                )
                self.collections[tmpc].elanpaths = [
                    path
                    for path in cached_links[collection]
                    #for path in cached_links[tmpc][bundle]
                ]

        if self.name == "AILLA":
            print("loading cached information")
            try:
                with open("cache/links/ailla.json") as json_in:
                    cached_links = json.loads(json_in.read())
            except IOError:
                cached_links = {}
                print(
                    """please download files from the TLA archive
"""
                )
            landingpage_template = "https://ailla.utexas.org/islandora/object/%s"
            for collection in cached_links:
                self.collections[collection] = Collection(
                    collection,
                    landingpage_template % collection,
                    archive="ailla",
                    urlprefix=self.collectionprefix,
                    url_template=self.collection_url_template,
                )
                self.collections[collection].elanpaths = [
                    path
                    for bundle in cached_links[collection]
                    for path in cached_links[collection][bundle]
                ]
        #with  open('cache/translations/%s.json'%self.name,w) as translationsout:
            #write(json.dumps(translations))
        #with  open('cache/transcriptions/%s.json'%self.name,w) as translationsout:
            #write(json.dumps(transcriptions))
        #with  open('cache/glosses/%s.json'%self.name,w) as translationsout:
            #write(json.dumps(glosses))
        #with  open('cache/NER/%s.json'%self.name,w) as translationsout:
            #write(json.dumps(NER))

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
        etree.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
        # retrieve all tags <dc:format>
        dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
        # retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
        for dcformat in dcformats:
            if dcformat.text == typ:
                identifiers = dcformat.findall(
                    "../{http://purl.org/dc/elements/1.1/}identifier"
                )
                return identifiers

    def retrieve(xmlfiles, mimetype):
        # retrieve all identifiers found in the xml files which include relevant mimetype
        globalidentifiers = [getIdentifiers(x, mimetype) for x in xmlfiles]
        # remove empty return values
        records = [x for x in globalidentifiers if x != None]
        # flatten out tuples of multiple identifiers contained in one file
        IDs = [x2.text for x in records for x2 in x]
        print(
            "found %i IDs (%i records) with references to %s files"
            % (len(IDs), len(records), mimetype)
        )
        return IDs, records

    def scan(d, xmlfiles, filetypes):
        print("Scanning %s" % d)
        for filetype in filetypes:
            IDs, records = retrieve(xmlfiles, filetypes[filetype])

    def olaceaf(xmlfile, typ):
        tree = etree.parse(xmlfile)
        etree.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
        globalidentifiers = []
        dico = defaultdict(list)
        # retrieve all tags <dc:format>
        dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
        # retrieve all identifiers within a <oai_dc:dc> if there is reference to  file of given type
        print(len(dcformats))
        for dcformat in dcformats:
            if dcformat.text.strip() == typ:
                identifiers = dcformat.getparent().findall(
                    ".//{http://purl.org/dc/elements/1.1/}identifier"
                )
                globalidentifiers.append(identifiers)
        records = [x for x in globalidentifiers if x != None]
        # flatten out tuples of multiple identifiers contained in one file
        for IDs in records:
            for item in IDs:  # etree.findall returns list
                dico[0].append(item.text.strip().replace("<", "").replace(">", ""))

    def get_fingerprints(self):
        # map filenames to fingerprints
        fingerprintd = {
            "%s/%s" % (self.name, eaf.path): eaf.fingerprint()
            for c in self.collections
            for eaf in self.collections[c].elanfiles
        }

        # sort by number of occurences and print
        counted_fingerprints = Counter(fingerprintd.values())
        ranks = sorted(
            [(counted_fingerprints[key], key) for key in counted_fingerprints.keys()]
        )[::-1]
        values = [x[0] for x in ranks]
        squarify.plot(
            sizes=values,
            label=values[:38],
            color=[cm.pink(x * 0.1) for x in [2, 8, 4, 7, 1, 6, 3, 9, 5]],
        )  # jumble colormap
        plt.axis("off")
        plt.savefig("tiertypetreemap-%s.png" % self.name)
        with open("tierranks-%s.txt" % self.name, "w") as out:
            out.write("\n".join(["%s:%s" % x for x in ranks]))
        with open("cache/fingerprints/%s.json" % self.name, "w") as out:
            out.write(json.dumps(fingerprintd, indent=4, sort_keys=True))
