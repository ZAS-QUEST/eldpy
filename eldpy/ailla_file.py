import requests
import humanize

class AillaFile:
    def __init__(self, name, url, type_):
        self.url = url
        self.download_url = url
        self.name = name
        self.type_ = type_
        self.size = 0

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
        self.size = size
