import requests
import humanize

class AillaFile:
    def __init__(self, name, url, type_, size, languages):
        self.url = url
        self.download_url = url
        self.name = name
        self.type_ = type_
        self.languages = languages
        if size:
            self.size = size*1024 #Ailla gives file sizes in KB
        else:
            self.size = 0

    def download(self, cookie=None, accept='*'):
        if accept == '*' or self.type_ in accept:
            r = requests.get(self.url, cookie=cookie)
            content = r.content
            with open(f"{self.name}.{self.type_}", "w") as out:
                out.write(content)
