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

def elar_eaf_download(filename, phpsessid, extension):
    # check for validity of ID
    try:
        soasID = filename.split("oai:soas.ac.uk:")[1]
    except IndexError:  # filename does not start with oai:soas.ac.uk:, so we are not interested
        print("not a SOAS file", soasID)
        return
    # prepare request
    url = "https://elar.soas.ac.uk/Record/%s" % soasID
    cookie = {"PHPSESSID": phpsessid}
    print("checking", url)
    # retrieve catalog page
    with requests.Session() as s:
        # r = s.post(url, cookies=cookie, data=payload)
        r = s.post(url, cookies=cookie)
        html = r.text
        # extract links to ELAN files
        try:
            links = fromstring(html).findall(".//tbody/tr/td/a")
            locations = {a.attrib["href"]
                            for a in links
                            if a.attrib["href"].endswith(extension)
                            }
        except AttributeError:#not an ELAN file
            print("files are not accessible")
            return
        # dowload identified files
        retrievedfiles = []
        for location in locations:
            print(location)
            filename = location.split("/")[-1]
            print("  downloading %s:" % filename)
            #filename = "./downloads/elar/%s.eaf" % filename[:200]  # avoid overlong file names
            filename = "./%s.%s" % (filename[:200], extension)  # avoid overlong file names
            r2 = s.post(location, cookies=cookie)
            content = r2.text
            #retrievedfiles.append({eafname: eafcontent})
            with open(filename, 'w') as out:
                out.write(content)



filetypes = {
    1: ("ELAN","text/x-eaf+xml","eaf"),
    2: ("Toolbox","text/x-toolbox-text","tbx"),
    3: ("transcriber","text/x-trs","trs"),
    4: ("praat","text/praat-textgrid","textgrid"),
    5: ("Flex","FLEx","xml"),
    6: ("Wave audio","audio/x-wav","wav")
    }

archives = {
    1: 'ELAR',
    2: 'TLA',
    3: 'PARADISEC',
    4: 'AILLA',
    5: 'ANLA'
    }


print("Which files are you interested in?")
for i in filetypes:
    print("%i) %s" % (i, filetypes[i][0]))
input_given = False
while input_given == False:
    try:
        filetypeinput = int(input("Select number and hit enter"))
        input_given = True
    except ValueError:
        pass

typename, mimetype, extension = filetypes[filetypeinput]
print("You have chosen %s (%s)" % (typename, extension))

try:
    print("unpacking zipped OLAC file")
    gunzipped_file = gzip.open("ListRecords.xml.gz")
except FileNotFoundError:
    print("no olac dump found. Retrieving dump from http://www.language-archives.org/xmldump/ListRecords.xml.gz")
    download_file('http://www.language-archives.org/xmldump/ListRecords.xml.gz', 'ListRecords.xml.gz')
    print("unpacking zipped OLAC file")
gunzipped_file = gzip.open("ListRecords.xml.gz")
print("parsing OLAC file")
tree = etree.parse(gunzipped_file)

globalidentifiers = {}
#retrieve all records which references files of interest
dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")

for dcformat in dcformats:
    if dcformat.text.strip() == mimetype:
        identifiers = dcformat.getparent().findall(
            ".//{http://purl.org/dc/elements/1.1/}identifier"
        )
        for identifier in identifiers:
            strippedtext = identifier.text.strip().replace("<", "").replace(">", "")
            if strippedtext.startswith('oai:soas.ac.uk'):
                globalidentifiers[strippedtext] = True

print("found %i relevant records" % len(globalidentifiers))

limit = 9999999
subset = list(globalidentifiers.keys())[:limit]

print("preparing to download %i files" % len(subset))
#print(subset)

#retrieve links
login_url = "https://elar.soas.ac.uk/MyResearch/UserLogin"
session = requests.Session()
un_name = "username"
pw_name = "password"
username = input("enter user name for ELAR: \n")
password = input("Your password will only be used for this login session and not be stored anywhere. Enter password for ELAR: \n")
values = {un_name: username.strip(), pw_name: password.strip()}
r = session.post(login_url, data = values)
phpsessid = session.cookies.get_dict().get('PHPSESSID')

for globalidentifier in subset:
    elar_eaf_download(globalidentifier, phpsessid, extension)
