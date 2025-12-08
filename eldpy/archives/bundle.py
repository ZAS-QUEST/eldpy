import urllib
import requests
import json

from bs4 import BeautifulSoup

from eldpy.archives.ailla_file import  AillaFile

class Bundle():
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.id_ = url.split('/')[-1]
        self.files = []
        self.languages = []


    def populate_files(self, hardlimit=10000):
        print("function populate_files not overwritten")


    def get_file_links(self, set_url):
        print("function get_file_links not overwritten")
