import urllib
from bs4 import BeautifulSoup
from eldpy.archives.tla_file import  TLAFile
from eldpy.archives.bundle import  Bundle
import requests

class TLABundle(Bundle):
    def __init__(self, name, id_):
        self.name = name
        self.url = url
        self.id_ = url.split('/')[-1]
        # self.url = f"https://archive.mpi.nl/tla/islandora/object/{id_}"
        self.files = []
        self.languages = []


    def populate_files(self):
        r = requests.get(self.url)
        content = r.content
        soup = BeautifulSoup(content, 'html.parser')
        dts_lg = [dt for dt in soup.find_all('dt') if dt.text.strip() == "Language"]
        self.languages = [dt.next.next.next.find('p').text for dt in dts_lg]
        print(self.languages)
        download_links = soup.find_all('a', class_="flat-compound-caption-link")
        self.files = [TLAFile(x.text, f"https://archive.mpi.nl{x['href']}", self.languages) for x in download_links]
