from getpass import getpass
import gzip
import os
import sys
import urllib.request
from lxml import etree
from lxml.html.soupparser import fromstring
from tqdm import tqdm
import requests


# https://stackoverflow.com/questions/15644964/python-progress-bar-and-downloads
class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)


def download_file(url, filename):
    """download the file from url to filename and display a progress bar"""

    with DownloadProgressBar(unit="B",
                             unit_scale=True,
                             miniters=1,
                             desc=url.split("/")[-1]
                            ) as t:
        urllib.request.urlretrieve(url, filename=filename, reporthook=t.update_to)


def elar_download(bundle_id, phpsessid, extension):
    """download files from an ELAR session/bundle, using a given extension"""

    # check for validity of ID
    try:
        soasID = bundle_id.split("oai:soas.ac.uk:")[1]
    except IndexError:  # bundle_id does not start with oai:soas.ac.uk:, so we are not interested
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
            locations = {
                a.attrib["href"] for a in links if a.attrib["href"].endswith(extension)
            }
        except AttributeError:  # not an ELAN file
            print("files are not accessible")
            return
        # dowload identified files
        if locations == []:
            print("files are not accessible")
            return
        for location in locations:
            filename = location.split("/")[-1]
            print("  downloading %s:" % filename)
            # filename = "./downloads/elar/%s.eaf" % filename[:200]  # avoid overlong file names
            filename = "%s.%s" % (
                filename[:-4][:200],
                extension,
            )  # avoid overlong file names

            filepath = os.path.join('elar', 'elar', filename)
            print("  downloading %s as %s:" % (location, filepath))
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "wb") as f:
                response = s.get(location, cookies=cookie, stream=True)
                total = response.headers.get("content-length")

                if total is None:
                    f.write(response.content)
                else:
                    downloaded = 0
                    total = int(total)
                    for data in response.iter_content(chunk_size=max(int(total / 1000),
                                                                     1024 * 1024
                                                                    )
                                                     ):
                        downloaded += len(data)
                        f.write(data)
                        done = int(50 * downloaded / total)
                        sys.stdout.write(
                            "\r[{}{}]".format("█" * done, "." * (50 - done))
                        )
                        sys.stdout.flush()
                sys.stdout.write("\n")


def retrieve_elar(extension):
    """identify and download  all accessible files from ELAR"""
    try:
        print("unpacking zipped OLAC file")
        gunzipped_file = gzip.open("ListRecords.xml.gz")
    except FileNotFoundError:
        print(
            "no olac dump found. Retrieving dump from http://www.language-archives.org/xmldump/ListRecords.xml.gz"
        )
        download_file(
            "http://www.language-archives.org/xmldump/ListRecords.xml.gz",
            "ListRecords.xml.gz",
        )
        print("unpacking zipped OLAC file")
    gunzipped_file = gzip.open("ListRecords.xml.gz")
    print("parsing OLAC file")
    tree = etree.parse(gunzipped_file)

    globalidentifiers = {}
    # retrieve all records which references files of interest
    dcformats = tree.findall(".//{http://purl.org/dc/elements/1.1/}format")

    for dcformat in dcformats:
        if dcformat.text.strip() == mimetype:
            identifiers = dcformat.getparent().findall(
                ".//{http://purl.org/dc/elements/1.1/}identifier"
            )
            for identifier in identifiers:
                strippedtext = identifier.text.strip().replace("<", "").replace(">", "")
                if strippedtext.startswith("oai:soas.ac.uk"):
                    globalidentifiers[strippedtext] = True

    print("found %i relevant records" % len(globalidentifiers))

    limit = 9999999
    subset = list(globalidentifiers.keys())[:limit]
    print("preparing to download %i files" % len(subset))
    # print(subset)

    # retrieve links
    login_url = "https://elar.soas.ac.uk/MyResearch/Home"

    session = requests.Session()
    un_name = "username"
    pw_name = "password"
    username = input("enter user name for ELAR: \n")
    password = getpass(
        "Your password will only be used for this login session and not be stored anywhere.\n Enter password for ELAR: \n"
    )

    values = {
        un_name: username.strip(),
        pw_name: password,
        "auth_method": "ILS",
        "processLogin": "Login",
    }
    session.post(login_url, data=values)
    phpsessid = session.cookies.get_dict().get("PHPSESSID")

    for globalidentifier in subset:
        elar_download(globalidentifier, phpsessid, extension)


def retrieve_tla(extension):
    """identify and download all accessible files of a given type from TLA"""

    if extension != 'eaf':
        print("currently, only eaf downloads are supported for TLA")
        return
    TLA_LIMIT = 5000 #there are currently 35k ELAN files in TLA
    #base_url = """https://archive.mpi.nl/tla/islandora/search/*%3A*?f[0]=cmd.Format%3A"%s"&f[1]=-cmd.Country%3A"Netherlands"&f[2]=-cmd.Country%3A"Belgium"&f[3]=-cmd.Country%3A"Germany"&limit=%i"""%(mimetype, TLA_LIMIT)
    #https://archive.mpi.nl/tla/islandora/search/%2A%3A%2A?page=2&f%5B0%5D=cmd.Format%3A%22text/x-eaf%2Bxml%22&islandora_solr_search_navigation=0&sort=fgs_label_s%20asc&limit=500
    login_url = "https://archive.mpi.nl/tla/user/login"
    username = input("Enter user name for TLA: \n")
    password = getpass(
        "Your password will only be used for this login session and not be stored anywhere.\n Enter password for TLA: \n"
    )
    with requests.Session() as s:
        print("retrieving collections")
        s = requests.Session()
        un_name = "name"
        pw_name = "pass"
        values = {
            un_name: username.strip(),
            pw_name: password,
            "op": "Log+in",
            "form_id": "user_login",
        }
        s.post(login_url, data=values)
        session_id = s.cookies.get_dict().get("SESSd8112b76bc7d4802dc104c36df341519")
        print(session_id)
        #get pages quantity
        collection_urls = []
        tla_mime = "text/x-eaf%2Bxml"
        country_restrictors = "f%5B1%5D=-cmd.Country%3A%22Netherlands%22&f%5B2%5D=-cmd.Country%3A%22Belgium%22&f%5B3%5D=-cmd.Country%3A%22Germany%22&"
        resultpages = ["https://archive.mpi.nl/tla/islandora/search/%%2A%%3A%%2A?page=%i&f%%5B0%%5D=cmd.Format%%3A%%22%s%%22&%slimit=%i"%(i, tla_mime, country_restrictors, TLA_LIMIT) for i in range(5)]
        for resultpage in resultpages:
            print(resultpage)
            base_request = s.get(resultpage)
            base_html = base_request.text
            #print(base_html)
            base_root = fromstring(base_html)
            collection_links = base_root.findall('.//dd[@class="solr-value cmd-title"]/a')
            new_collection_urls = [
                "https://archive.mpi.nl/%s" % a.attrib["href"] for a in collection_links
            ]
            print(len(new_collection_urls), "new urls")
            collection_urls += new_collection_urls
        collection_length = len(collection_urls)
        print(len(collection_urls), "collections")
        OFFSET= 3390
        for i, c_url in enumerate(collection_urls[OFFSET:]):
            #print("collection ", c_url)
            collection_id = c_url.split("%3A")[-1]
            print(collection_id, "%i (+%i)/%i"%(i+1, OFFSET, collection_length))
            c_request = s.get(c_url)
            c_html = c_request.text
            c_root = fromstring(c_html)
            file_links = c_root.findall('.//a[@class="flat-compound-caption-link"]')
            file_tuples = [
                (a.attrib["href"], a.text)
                for a in file_links
                if a.text is not None and a.text.endswith(extension)
            ]
            for file_tuple in file_tuples:
                # print("  f: ", file_tuple)
                f_url, filename = file_tuple
                download_url = "https://archive.mpi.nl/%s" % f_url
                filepath = os.path.join('tla', collection_id, filename)
                print("  downloading %s as %s:" % (download_url, filepath))
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    cookie = {"SESSd8112b76bc7d4802dc104c36df341519": session_id}
                    response = s.get(download_url, cookies=cookie, stream=True)
                    total = response.headers.get("content-length")
                    if total is None:
                        f.write(response.content)
                    else:
                        downloaded = 0
                        total = int(total)
                        for data in response.iter_content(chunk_size=max(int(total / 1000),
                                                                        1024 * 1024)
                                                        ):
                            downloaded += len(data)
                            f.write(data)
                            done = int(50 * downloaded / total)
                            sys.stdout.write(
                                "\r[{}{}]".format("█" * done, "." * (50 - done))
                            )
                            sys.stdout.flush()
                    sys.stdout.write("\n")



def retrieve_ailla(extension):
    """identify and download all accessible files of a given type from AILLA"""

    base_url = "https://ailla.utexas.org/islandora/object/ailla%3Acollection_collection?page=1&rows=1000"
    username = input("Enter user name for AILLA: \n")
    password = getpass(
        "Your password will only be used for this login session and not be stored anywhere.\n Enter password for AILLA: \n"
    )
    with requests.Session() as s:
        print("retrieving collections")
        s = requests.Session()
        un_name = "name"
        pw_name = "pass"
        values = {
            un_name: username.strip(),
            pw_name: password,
            "op": "log+in",
            "form_id": "user_login_block",
        }
        s.post(base_url, data=values)
        session_id = s.cookies.get_dict().get("SSESS64f35ecaf4903fe271ed0b0c15ee2bce")
        b_request = s.get(base_url)
        b_html = b_request.text
        b_root = fromstring(b_html)
        collection_links = b_root.findall(".//div/dl/dd/a")
        collection_urls = [
            "https://ailla.utexas.org/%s" % a.attrib["href"] for a in collection_links
        ]
        collections_length = len(collection_urls)
        for i, c_url in enumerate(collection_urls):
            print("collection ", c_url)
            collection_id = c_url.split("%3A")[-1]
            c_request = s.get(c_url)
            c_html = c_request.text
            c_root = fromstring(c_html)
            session_links = c_root.findall(".//div/dl/dd/a")
            session_urls = [
                "https://ailla.utexas.org/%s" % a.attrib["href"] for a in session_links
            ]
            sessions_length = len(session_urls)
            for j, s_url in enumerate(session_urls):
                print(
                    " session %s (c :%s/%s; s:%s/%s)"
                    % (s_url[51:], i + 1, collections_length, j + 1, sessions_length,)
                )
                s_request = s.get(s_url)
                s_html = s_request.text
                s_root = fromstring(s_html)
                file_links = s_root.findall(".//tbody/tr/td/a")
                file_tuples = [
                    (a.attrib["href"], a.text)
                    for a in file_links
                    if a.text is not None and a.text.endswith(extension)
                ]
                for file_tuple in file_tuples:
                    # print("  f: ", file_tuple)
                    f_url, filename = file_tuple
                    download_url = "%s/datastream/OBJ/download" % f_url
                    filepath = os.path.join('ailla', collection_id, filename)
                    print("  downloading %s as %s:" % (download_url, filepath))
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        cookie = {"SSESS64f35ecaf4903fe271ed0b0c15ee2bce": session_id}
                        response = s.get(download_url, cookies=cookie, stream=True)
                        total = response.headers.get("content-length")
                        if total is None:
                            f.write(response.content)
                        else:
                            downloaded = 0
                            total = int(total)
                            for data in response.iter_content(chunk_size=max(int(total / 1000),
                                                                             1024 * 1024)
                                                             ):
                                downloaded += len(data)
                                f.write(data)
                                done = int(50 * downloaded / total)
                                sys.stdout.write(
                                    "\r[{}{}]".format("█" * done, "." * (50 - done))
                                )
                                sys.stdout.flush()
                        sys.stdout.write("\n")


def retrieve_paradisec(extension):
    """identify and download all accessible files of a given type from PARADISEC"""

    #login_url = "https://catalog.paradisec.org.au/users/sign_in"
    #username = input("Enter your email for PARADISEC: \n")
    #password = getpass(
        #"Your password will only be used for this login session and not be stored anywhere.\n Enter password for PARADISEC: \n"
    #)
    #print("retrieving collections")
    with requests.Session() as s:
        ##log in
        #un_name = "user[email]"
        #pw_name = "user[password]"
        #values = {
            #un_name: username.strip(),
            #pw_name: password,
            #"commit": "Sign+in",
            #"user[remember_me]": "0",
        #}
        #response = s.post(login_url, data=values)
        ##session_id = response.cookies.get_dict().get("_session_id")
        session_id = input("For PARADISEC, you have to login manually and retrieve the cookie called '_session_id'. Paste the value of this cookie (e.g. d9bb68a51923ae30204be72f0006ae63)\n")

        #store session cookie from login
        cookies = {"_session_id": session_id}
        base_url = "https://catalog.paradisec.org.au/items/search?page=1&per_page=30000"
        print("retrieving full list of PARADISEC collections. This might take some time")
        b_request = s.get(base_url)
        print("done")
        b_html = b_request.text
        b_root = fromstring(b_html)
        collection_links = b_root.findall(".//body/div/div[5]/div/table//tr/td[8]/a")
        collection_urls = [
            "https://catalog.paradisec.org.au%s?items_per_page=1000" % a.attrib["href"] for a in collection_links
        ]
        collections_length = len(collection_urls)
        print(collections_length, "collections found")
        OFFSET = 0
        print("OFFSET is", OFFSET)
        for i, c_url in enumerate(collection_urls[OFFSET:]):
            print("collection ", c_url)
            collection_id = c_url.split("/")[-1]
            c_request = s.get(c_url)
            c_html = c_request.text
            try:
                c_root = fromstring(c_html)
            except ValueError:
                print("invalid XML", c_url)
            item_links = c_root.findall(".//div/div/div/fieldset/table//tr/td/a")
            item_urls = [
                "https://catalog.paradisec.org.au%s?files_per_page=1000" % a.attrib["href"] for a in item_links if "items" in a.attrib["href"]
            ]
            items_length = len(item_urls)
            for j, i_url in enumerate(item_urls):
                print(
                    " session %s (c (+%i):%s/%s; s:%s/%s)"
                    % (i_url[33:-20], OFFSET, i + 1, collections_length, j + 1, items_length)
                )
                i_request = s.get(i_url, cookies=cookies)
                i_html = i_request.text
                i_root = fromstring(i_html)
                i_root.find("./body/div/div[5]/div[5]/fieldset[1]/table/tbody/tr[1]/td[5]/a")
                tds = i_root.findall(".//tbody/tr/td[1]")
                print("  ", len(tds)-1, "downloadable files found. Checking for correct extensions")
                f_tuples = []
                for td in tds:
                    rawname = td.text
                    if rawname.endswith(extension) is False:
                        continue
                    try:
                        parts = rawname.split('-')
                        collection_id = parts[0]
                        running_number = parts[1]
                        remainder = parts[2]
                    except IndexError:
                        continue
                    f_url = "http://catalog.paradisec.org.au/repository/%s/%s/%s" % (collection_id, running_number,rawname)
                    #print(f_url)
                    found = True
                    f_tuples.append((f_url,collection_id,rawname))
                print("  ", len(f_tuples), "relevant file(s) found")
                #print(f_tuples)
                for f_tuple in f_tuples:
                    f_url, collection_id, basename = f_tuple
                    filename = basename
                    #print("  f: ", file_tuple)
                    download_url = f_url
                    filepath = os.path.join('paradisec', collection_id, basename)
                    print("  downloading %s as %s:" % (download_url, filepath))
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    with open(filepath, "wb") as f:
                        response = s.get(download_url, cookies=cookies, stream=True)
                        total = response.headers.get("content-length")
                        if total is None:
                            f.write(response.content)
                        else:
                            downloaded = 0
                            total = int(total)
                            for data in response.iter_content(chunk_size=max(int(total / 1000),
                                                                                1024 * 1024)
                                                                ):
                                downloaded += len(data)
                                f.write(data)
                                done = int(50 * downloaded / total)
                                sys.stdout.write(
                                    "\r[{}{}]".format("█" * done, "." * (50 - done))
                                )
                                sys.stdout.flush()
                        sys.stdout.write("\n")


if __name__ == "__main__":
    filetypes = {
        1: ("ELAN", "text/x-eaf+xml", "eaf"),
        2: ("Toolbox", "text/x-toolbox-text", "tbx"),
        3: ("transcriber", "text/x-trs", "trs"),
        4: ("praat", "text/praat-textgrid", "textgrid"),
        5: ("Flex", "FLEx", "xml"),
        6: ("Wave audio", "audio/x-wav", "wav"),
    }

    archives = {1: "ELAR", 2: "TLA", 3: "PARADISEC", 4: "AILLA", 5: "ANLA"}

    print(
        "This script will download all files from ELAR/AILLA which you have access to. You will have to provide your username and password. Which file type are you interested in?"
    )
    for filetype in filetypes:
        print("%i) %s" % (filetype, filetypes[filetype][0]))
    input_given = False
    #filetypeinput = 1
    while input_given is False:
        try:
            filetypeinput = int(input("Select number and hit enter\n"))
            input_given = True
        except ValueError:
            pass
    typename, mimetype, chosen_extension = filetypes[filetypeinput]
    print("You have chosen %s (%s)" % (typename, chosen_extension))
    print("Which archive are you interested in?")
    for archive in archives:
        print("%i) %s" % (archive, archives[archive]))
    input_given = False
    #archiveinput = 3
    while input_given is False:
        try:
            archiveinput = int(input("Select number and hit enter\n"))
            input_given = True
        except ValueError:
            pass
    archivename = archives[archiveinput]
    print("You have chosen %s" % archivename)
    if archiveinput == 1:  # ELAR
        retrieve_elar(chosen_extension)
    if archiveinput == 2:  # TLA
        retrieve_tla(chosen_extension)
    if archiveinput == 3:  # PARADISEC
        retrieve_paradisec(chosen_extension)
    if archiveinput == 4:  # ailla
        retrieve_ailla(chosen_extension)
