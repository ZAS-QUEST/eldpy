import urllib
from bs4 import BeautifulSoup
from paradisec_file import  ParadisecFile
import requests

class ParadisecBundle():
    def __init__(self, name, url, languages):
        self.name = name
        self.url = url
        self.languages = []
        self.files = []


    def populate_files(self):
        r = requests.get(self.url)
        content = r.content
        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find_all('table')[1]
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            name = tds[0].text
            type_ = tds[1].text
            size = tds[2].text
            duration = tds[3].text
            url = None
            self.files.append(ParadisecFile(name,url,type_,size,duration))
