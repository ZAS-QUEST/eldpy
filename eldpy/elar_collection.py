from collection import Collection
import urllib
from bs4 import BeautifulSoup
from elar_bundle import  ElarBundle

class ElarCollection(Collection):
    def __init__(self, name, url):
        self.name = name
        self.url = url
        self.bundles = []
        self.files = []

    def get_bundles_on_page(self, soup):
        return [
            ElarBundle(a.text, a["href"]) for h5 in soup.find_all("h5") for a in h5.find_all("a")
        ]

    def get_collection_bundles(self, hardlimit=10000,languages=True):
        url = self.url
        limit = 1
        bundles = []
        try:
            with urllib.request.urlopen(url) as collection_reader:
                content = collection_reader.read()
                soup = BeautifulSoup(content, "html.parser")
                try:
                    limit = int(
                        soup.find("div", class_="pagination").find_all("a")[-2].text
                    )
                except (IndexError, AttributeError):
                    limit = 1
                print(" ", url.split("uncategorized/")[-1], f"[{limit} pages]")
                bundles = self.get_bundles_on_page(soup)
        except urllib.error.HTTPError:
            bundles = []
            print(f"  could not download{url}")
            return bundles
        current = 2
        while current <= limit and current <= hardlimit:
            current_url = url + f"?pg={current}"
            print(f"  pg={current}", end="", flush=True)
            try:
                with urllib.request.urlopen(current_url) as current_collection_reader:
                    current_content = current_collection_reader.read()
                    current_soup = BeautifulSoup(current_content, "html.parser")
                    new_bundles = self.get_bundles_on_page(current_soup)
                    # print(f"  adding {len(new_bundles)} bundles")
                    bundles += new_bundles
            except urllib.error.HTTPError:
                print(f"\n  could not download{current_url}")
            current += 1
        if limit > 1:
            print()
        # print(f" finished. There are {len(bundles)} bundles")
        return bundles

    def populate_bundles(self, hardlimit=10000,languages=True):
        # print("populating bundles")
        self.bundles = self.get_collection_bundles(hardlimit=hardlimit,languages=languages)
        if languages:
            for bundle in self.bundles:
                bundle.populate_languages()

    def populate_files(self):
        for bundle in self.bundles:
            if bundle.files == []:
                bundle.populate_files()
        self.files += bundle.files
