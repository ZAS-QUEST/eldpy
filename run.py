from download import bulk_download
from bulk import (
    bulk_populate,
    bulk_cache,
    bulk_rdf,
    bulk_statistics,
    bulk_fingerprints,
)

for archive in (1, 2, 3, 4, 5):
    bulk_download(archive=archive, filetype=1)


# bulkpopulate(archives=['AILLA', 'ELAR'])
bulk_populate()
bulk_cache()
bulk_fingerprints()
bulk_statistics()
bulk_rdf()
