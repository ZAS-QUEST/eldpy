import urllib
import requests
import json

from bs4 import BeautifulSoup

from eldpy.archives.ailla_file import  AillaFile

class AillaBundle():
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.url = f"https://ailla.utexas.org/folders/{id_}"
        self.files = []


    def populate_files(self, hardlimit=10000):
        print(f" populating files for {self.url}")
        request_folder = requests.get(self.url)
        soup = BeautifulSoup(request_folder.content, 'html.parser')
        j = json.loads(soup.find('script',type="application/json").text)
        try:
            sets = j['props']['pageProps']['data']['items']
        except KeyError:
            print(f"  no file sets for {self.url}")
            return
        file_list = []
        for set_ in sets:
            id_ = set_['id']
            name = set_['name']
            set_url = f"https://ailla.utexas.org/sets/{id_}"
            new_files = self.get_file_links(set_url)
            file_list += new_files
        self.files += file_list
        print(f"  {len(self.files)} files for {self.url}")


    def get_file_links(self, set_url):
        print(f"  file set url is {set_url}. Retrieving information")
        request_set = requests.get(set_url)
        soup = BeautifulSoup(request_set.content, 'html.parser')
        j = json.loads(soup.find('script',type="application/json").text)
        files = []
        try:
            data = j['props']['pageProps']['data']
        except KeyError:
            return []
        try:
            subject_languages = [x['language_code'] for x in data['subject_languages']]
            # print(subject_languages)
        except KeyError:
            # print("no subject_languages")
            subject_languages = []
        for f in data['files']:
            filename = f['filename']
            file_size = f['file_size']
            islandora_pid = f['islandora_pid']
            type_ = f['media_type']
            download_url = f"https://ailla-legacy.lib.utexas.edu/islandora/object/{islandora_pid}/datastream/OBJ/download"
            files.append(AillaFile(filename, download_url, type_, file_size, subject_languages))
        # print(f"   found {len(files)} files")
        return files





