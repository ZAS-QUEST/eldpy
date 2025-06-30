import requests
import humanize

class ElarFile:
    def __init__(self, name, url, type_, id_=None):
        self.url = url
        self.download_url = self.url.replace("https://eldp.access.preservica.com/uncategorized/",
                                             "https://www.elararchive.org/download/file/")
        self.name = name
        self.id_ = id_
        self.type_ = type_
        self.megatype = ''
        self.size = 0
        self.duration = 0
        self.languages = []

    def download(self, cookie=None, accept='*'):
        if accept == '*' or self.type_ in accept:
            r = requests.get(self.url, cookie=cookie)
            content = r.content
            with open(f"{self.name}.{self.type_}", "w") as out:
                out.write(content)

    def get_size(self):
        print(f"getting size for {self.download_url}")
        response = requests.head(self.download_url)
        size = response.headers.get('Content-Length', 0)
        print(humanize.naturalsize(size))
        self.size = int(size)
