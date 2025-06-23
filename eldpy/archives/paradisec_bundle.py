import urllib
from bs4 import BeautifulSoup
from paradisec_file import  ParadisecFile
import requests
import time

class ParadisecBundle():
    def __init__(self, name, url, languages):
        self.name = name
        self.url = url
        self.languages = []
        self.files = []


    def populate_files(self):
        if self.url == '':
            return
        time.sleep(.1)
        try:
            r = requests.get(self.url)
        except requests.exceptions.ConnectionError:
            print(f"{self.url} connection dropped while populating files")
            time.sleep(5)
            return
        content = r.content
        soup = BeautifulSoup(content, 'html.parser')
        isocodes = []
        try:
            table = soup.find_all('table')[0]
            languagelinks = [x.next.next.next.find_all('a') for x in table.find_all('th') if x.text=='Subject language(s)']
            isocodes = [a['href'].split('/')[-1] for l in languagelinks for a in l]
            self.languages = isocodes
            # print(isocodes)
        except IndexError:
            print(f"languages could not be retrieved for {self.url}")
        try:
            table = soup.find_all('table')[1]
        except IndexError:
            return
        for tr in table.find_all('tr'):
            try:
                tds = tr.find_all('td')
                name = tds[0].text
                type_ = tds[1].text
                size = tds[2].text
                duration = tds[3].text
                url = None
                self.files.append(ParadisecFile(name,url,type_,size,duration,self.languages))
            except IndexError:
                continue
