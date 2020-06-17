from .download import bulk_download
from .bulk import *
from .delaman import archives

def run():
    for archive in archives:
        bulk_download(archive=archive, filetype=1)#1=ELAN
    bulk_populate(cache=True)
    bulk_cache()
    bulk_fingerprints()
    bulk_cache()
    bulk_statistics()
    bulk_rdf()
