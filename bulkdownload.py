import requests
import urllib.request
from tqdm import tqdm
from lxml import etree
import gzip
from collections import Counter, defaultdict
from lxml.html.soupparser import fromstring

#https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_file(url, filename):
    with DownloadProgressBar(unit='B',
                            unit_scale=True,
                            miniters=1,
                            desc=url.split('/')[-1]
                            ) as t:
        urllib.request.urlretrieve(url,
                            filename=filename,
                            reporthook=t.update_to)

def elar_eaf_download(filename, phpsessid):
    # check for validity of ID
    try:
        soasID = filename.split("oai:soas.ac.uk:")[1]
    except IndexError:  # filename does not start with oai:soas.ac.uk:, so we are not interested
        print("not a SOAS file", soasID)
        return
    # prepare request
    url = "https://elar.soas.ac.uk/Record/%s" % soasID
    cookie = {"PHPSESSID": phpsessid}
    print(url)
    # retrieve catalog page
    with requests.Session() as s:
        # r = s.post(url, cookies=cookie, data=payload)
        r = s.post(url, cookies=cookie)
        html = r.text
        # extract links to ELAN files
        try:
            links = fromstring(html).findall(".//tbody/tr/td/a")
            eaflocations = {a.attrib["href"]
                            for a in links
                            if a.attrib["href"].endswith("eaf")
                            }
        except AttributeError:#not an ELAN file
            print("ELAN files are not accessible")
            return
        # dowload identified files
        retrievedfiles = []
        for eaflocation in eaflocations:
            print(eaflocation)
            eafname = eaflocation.split("/")[-1]
            print("  downloading %s:" % eafname)
            eafname = "./downloads/elar/%s.eaf" % eafname[:200]  # avoid overlong file names
            eafname = "./%s.eaf" % eafname[:200]  # avoid overlong file names
            r2 = s.post(eaflocation, cookies=cookie)
            eafcontent = r2.text
            #retrievedfiles.append({eafname: eafcontent})
            with open(eafname, 'w') as out:
                out.write(eafcontent)



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




#try:
    #olacdump = open('ListRecords.xml')
#except FileNotFoundError:
    #print("no olac dump found. Retrieving dump from http://www.language-archives.org/xmldump/ListRecords.xml.gz")


typ = filetypes["ELAN"]

print("unpacking zipped OLAC file")
gunzipped_file = gzip.open("ListRecords.xml.gz")
print("parsing OLAC file")
tree = etree.parse(gunzipped_file)

globalidentifiers = {}
#retrieve all records which references files of interest
dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")
for dcformat in dcformats:
    if dcformat.text.strip() == typ:
        identifiers = dcformat.getparent().findall(
            ".//{http://purl.org/dc/elements/1.1/}identifier"
        )
        for identifier in identifiers:
            strippedtext = identifier.text.strip().replace("<", "").replace(">", "")
            if strippedtext.startswith('oai:soas.ac.uk'):
                globalidentifiers[strippedtext] = True

print("found %i relevant records" % len(globalidentifiers))

subset = list(globalidentifiers.keys())[:50]
print(subset)

#retrieve links
login_url = "https://elar.soas.ac.uk/MyResearch/UserLogin"
session = requests.Session()
un_name = "username"
pw_name = "password"
print("enter user name:")
username = "%s"%input()
print("enter password:")
password = "%s"%input()
values = {un_name: username.strip(), pw_name: password.strip()}
r = session.post(login_url, data = values)
phpsessid = session.cookies.get_dict().get('PHPSESSID')

for globalidentifier in subset:
    elar_eaf_download(globalidentifier, phpsessid)

#enumerate

#download 10.

#Estimate duration

#finish
