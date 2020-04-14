import urllib.request

from tqdm import tqdm
from lxml import etree
import gzip
from collections import Counter, defaultdict

#https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

filetypes = {
    "ELAN":"text/x-eaf+xml",
    "Toolbox":"text/x-toolbox-text",
    "transcriber":"text/x-trs",
    "praat":"text/praat-textgrid",
    "Flex":"FLEx"
    }

archives = {
    1: 'ELAR',
    2: 'TLA',
    3: 'PARADISEC',
    4: 'AILLA',
    5: 'ANLA'
    }



print("""This script will download ELAN files from endangered language archives for you. Please give a comma-separated list of the archives you are interested in (e.g. 1,3,4):
    1) ELAR
    2) TLA
    3) PARADISEC
    4) AILLA
    5) ANLA
""")

rawinputlist = input()
try:
    inputlist = {int(x) for x in rawinputlist.strip().split(',')}
except  ValueError:
    print("Please use integers")

if list is []:
    print("No input given")
print("You selected %s" %', '.join([archives[i] for i in inputlist]))

#try:
    #olacdump = open('ListRecords.xml')
#except FileNotFoundError:
    #print("no olac dump found. Retrieving dump from http://www.language-archives.org/xmldump/ListRecords.xml.gz")


#with DownloadProgressBar(unit='B',
                         #unit_scale=True,
                         #miniters=1,
                         #desc=url.split('/')[-1]) as t:
    #urllib.request.urlretrieve("http://www.language-archives.org/xmldump/ListRecords.xml.gz",
                               #filename="ListRecords.xml.gz",
                               #reporthook=t.update_to)
print("unpacking zipped OLAC file")
gunzipped_file = gzip.open("ListRecords.xml.gz")
print("parsing OLAC file")
tree = etree.parse(gunzipped_file)
etree.register_namespace("dc", "http://purl.org/dc/elements/1.1/")
typ = filetypes["ELAN"]
globalidentifiers = {}
# retrieve all tags <dc:format>
dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
print("Dump lists %i references to files of given type" %len(dcformats))
#retrieve all records which references files of interest
for dcformat in dcformats:
    if dcformat.text.strip() == typ:
        identifiers = dcformat.getparent().findall(
            ".//{http://purl.org/dc/elements/1.1/}identifier"
        )
        for identifier in identifiers:
            strippedtext = identifier.text.strip().replace("<", "").replace(">", "")
            if strippedtext.startswith('http'):
                if strippedtext.startswith('https://lat1.lis.soas.ac.uk'):
                    globalidentifiers[strippedtext] = True

print("found %i relevant records" % len(globalidentifiers))


#retrieve links

#ask for session key or un/pw

#enumerate

#download 10.

#Estimate duration

#finish
