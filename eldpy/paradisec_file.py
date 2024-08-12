import requests

class ParadisecFile:
    def __init__(self, name, url, type_, size, duration, languages):
        self.name = name
        self.url = url
        self.type_ = type_
        self.size = self.get_size(size)
        self.duration = duration
        self.languages = languages

    def get_size(self, s):
        try:
            number, unit = s.split()
        except ValueError:
            number = 0
            unit = ''
        factor = 1
        if unit == "KB":
            factor = 1024
        if unit == "MB":
            factor = 1024**2
        if unit == "GB":
            factor = 1024**3
        if unit == "TB":
            factor = 1024**4
        return int(float(number)*factor)
