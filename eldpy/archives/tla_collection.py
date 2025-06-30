from eldpy.archives.collection import Collection
import urllib
import requests
from bs4 import BeautifulSoup
from eldpy.archives.tla_bundle import  TLABundle

class TLACollection(Collection):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.files = []

    def populate_bundles(self):
        self.get_bundles(self.url)

    def get_bundles(self, url):
        """
        Accumulate all 'terminal nodes', from where files are linked
        Non-terminal nodes have a <h2 class="block-title">. For non-terminal
        nodes, recursively descend into all subnodes to find the terminal nodes
        """
        r = requests.get(url)
        content = r.content
        soup = BeautifulSoup(content, 'html.parser')
        has_more_bundles = soup.find("h2", class_="block-title")
        if not has_more_bundles:
            # This is a terminal node
            # print(f"{url} is a terminal node")
            name = soup.find('h1').text
            self.bundles.append(TLABundle(name, url))
        else:
            # This node has subnodes
            # print(f"{url} is a non-terminal node")
            div = soup.find('div', class_="view-content")
            links = div.find_all('a')
            new_links = [f"https://archive.mpi.nl{l['href']}" for l in links if l.get('title') and '305B_C' not in l['href'] and l.get('href','').startswith("/tla/isl")]
            # print(f" found {len(new_links)} subnodes")
            for new_link in new_links:
                self.get_bundles(new_link)




