import requests
import humanize

class TLAFile:
    def __init__(self, name, url, languages):
        self.url = url
        # self.download_url = self.url
        self.name = name
        self.type_ = self.name.split('.')[-1]
        self.languages = languages
        self.size = 0

    def get_size(self):
        print(f"getting size for {self.url}")
        response = requests.head(f"{url}datastream/OBJ/download")
        size = response.headers.get('Content-Length', 0)
        print(humanize.naturalsize(size))
        self.size = int(size)
