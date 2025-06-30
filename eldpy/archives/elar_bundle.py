import urllib
from bs4 import BeautifulSoup
from eldpy.archives.elar_file import  ElarFile
import requests

class ElarBundle():
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.files = []
        self.languages = []

    def get_files_on_page_(self, soup):
        return [ElarFile(a.text, a['href'], a.findNext('div').text.strip()) for h5 in soup.find_all('h5') for a in h5.find_all('a')]

    def get_bundle_files(self, hardlimit=10000):
        limit = 1
        soup = self.get_soup()
        try:
            limit = int(soup.find('div',class_='pagination').find_all('a')[-2].text)
        except (IndexError, AttributeError):
            limit = 1
        print(url.split("uncategorized/")[-1], end=" ")
        files = self.get_files_on_page_(soup)
        current = 2
        while current <= limit and current <= hardlimit:
            current_url =  url + f"?pg={current}"
            print(f" pg={current}", end="", flush=True)
            try:
                with urllib.request.urlopen(current_url) as current_file_reader:
                    current_content = current_file_reader.read()
                    current_soup = BeautifulSoup(current_content, 'html.parser')
                    new_files = self.get_files_on_page_(current_soup)
                    print(f" adding {len(files)} files")
                    files += new_files
            except urllib.error.HTTPError:
                print(f" could not download {current_url}")
            current += 1
        print(f"finished. [{len(files)} files]")
        return files

    def populate_files(self, hardlimit=10000):
        # print("populating files")
        self.files = self.get_bundle_files(hardlimit=hardlimit)

    def get_soup(self):
        url = self.url
        try:
            with urllib.request.urlopen(url) as bundle_reader:
                content = bundle_reader.read()
        except urllib.error.HTTPError:
            print (f"{url} could not be opened")
            return []
        soup = BeautifulSoup(content, 'html.parser')

    def populate_languages(self):
        content = requests.get(self.url).content
        soup = BeautifulSoup(content, 'html.parser')
        try:
            metadata_spans = soup.find_all('h5', class_='metadata-title')
            language_spans = [x for x in metadata_spans if x.text.strip()=="Language"]
            languages = [span.next.next.next.next.next.next.next.next.next.next.text for span in language_spans]
        except AttributeError:
            print(f"no languages found for {self.url}")
            languages = []
        # print(languages)
        self.languages = languages



