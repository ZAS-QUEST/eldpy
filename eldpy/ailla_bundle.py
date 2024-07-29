import urllib
from bs4 import BeautifulSoup
from ailla_file import  AillaFile

class AillaBundle():
    def __init__(self, name, id_):
        self.name = name
        self.id_ = id_
        self.url = f"https://ailla.utexas.org/folders/{id_}"
        self.files = []
