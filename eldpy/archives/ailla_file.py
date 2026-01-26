import requests
import humanize
# from eldpy.helpers import get_seconds_from_clean_str

class AillaFile:
    def __init__(self, name, url, type_, size, duration_string, languages):
        self.url = url
        self.download_url = url
        self.name = name
        self.type_ = type_
        self.languages = languages
        if size:
            self.size = size*1024 #Ailla gives file sizes in KB
        else:
            self.size = 0
        self.duration = duration_string
        # if duration_string:
        #     self.duration = get_seconds_from_clean_str(duration_string)


    def download(self, cookie=None, accept='*'):
        if accept == '*' or self.type_ in accept:
            r = requests.get(self.url, cookie=cookie)
            content = r.content
            with open(f"{self.name}.{self.type_}", "w") as out:
                out.write(content)
