import requests
import humanize
from eldpy.archives.tla_sizes import tla_sizes


class TLAFile:
    def __init__(self, name, url, languages):
        self.url = url
        self.ID = url.split('/')[-1].replace("tla%","lat:")
        print(self.ID)
        # self.download_url = self.url
        self.name = name
        self.type_ = self.name.split('.')[-1]
        self.languages = languages
        self.size = tla_sizes.get(self.ID, 0)
        self.duration = 0
        print(self.type)
        if self.type_ == "wav":
            self.duration = self.size/176400

    def get_size(self):
        return self.size
    #     print(f"getting size for {self.url}")
    #     response = requests.head(f"{url}datastream/OBJ/download")
    #     size = response.headers.get('Content-Length', 0)
    #     # print(humanize.naturalsize(size))
    #     self.size = int(size)
